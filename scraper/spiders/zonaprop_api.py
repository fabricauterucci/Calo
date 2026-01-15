import scrapy
import json
from datetime import datetime
from scraper.items import PropiedadItem


class ZonapropApiSpider(scrapy.Spider):
    """
    Spider ultra-rápido que usa la API interna de Zonaprop.
    Evita completamente el HTML y Cloudflare.
    """
    name = "zonaprop_api"
    
    # Configuración optimizada para API
    custom_settings = {
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS": 8,
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True,  # Necesario para mantener sesión
    }
    
    api_url = "https://www.zonaprop.com.ar/rplis-api/postings"
    
    # Mapeo de características según la documentación
    FEATURES_MAP = {
        "CFT101": "superficie_cubierta", 
        "CFT1": "ambientes",
        "CFT2": "dormitorios",
        "CFT3": "banos",
        "CFT7": "cocheras",
        # CFT100 es superficie_lote (no está en PropiedadItem)
        # CFT5 es antiguedad (no está en PropiedadItem)
    }
    
    def start_requests(self):
        """
        Lanza búsquedas paralelas para casas, departamentos y PHs en ARS y USD, y recorre más páginas para cada combinación.
        """
        headers = {
            'accept': '*/*',
            'accept-language': 'es-AR,es;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://www.zonaprop.com.ar',
            'referer': 'https://www.zonaprop.com.ar/departamentos-alquiler-rosario.html',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

        tipos = [
            ("2", "Casa"),
            ("1", "Departamento"),
            ("6", "PH"),
        ]
        monedas = [
            (1, "ARS", 30000, 2000000),
            (2, "USD", 200, 5000),
        ]
        max_pages = 8  # Aumentar páginas para mayor cobertura

        for tipoDePropiedad, tipo_nombre in tipos:
            for moneda, moneda_nombre, preciomin, preciomax in monedas:
                for pagina in range(1, max_pages + 1):
                    payload = {
                        "moneda": moneda,
                        "preciomin": str(preciomin),
                        "preciomax": str(preciomax),
                        "tipoDeOperacion": "2",  # Alquiler
                        "tipoDePropiedad": tipoDePropiedad,
                        "tipoAnunciante": "ALL",
                        "sort": "relevance",
                        "city": "1004728",  # Rosario
                        "pagina": pagina,
                    }
                    yield scrapy.Request(
                        self.api_url,
                        method='POST',
                        headers=headers,
                        body=json.dumps(payload),
                        callback=self.parse_api,
                        meta={'currency': moneda_nombre, 'page': pagina, 'payload': payload, 'headers': headers},
                        dont_filter=True,
                    )
    
    def parse_api(self, response):
        """Parsea la respuesta JSON de la API"""
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parseando JSON: {e}")
            return
        
        # Extraer propiedades del resultado
        postings = data.get('listPostings', [])
        total = data.get('paging', {}).get('totalPostings', 0)
        current_page = response.meta['page']
        
        self.logger.info(f"📄 Página {current_page} ({response.meta['currency']}): {len(postings)} propiedades de {total} totales")
        
        for posting in postings:
            yield self.parse_posting(posting)
        
        # Ya no se hace paginación incremental aquí, porque start_requests lanza todas las páginas en paralelo para acelerar el scraping.
    
    def parse_posting(self, posting):
        """Convierte un posting de la API a PropiedadItem"""
        item = PropiedadItem()
        
        item['fuente'] = 'zonaprop'
        item['id_externo'] = str(posting.get('postingId', ''))
        
        # URL
        url = posting.get('url', '')
        if url and not url.startswith('http'):
            url = 'https://www.zonaprop.com.ar' + url
        item['url'] = url
        
        # Información básica
        item['titulo'] = posting.get('title', 'Propiedad en Zonaprop')
        item['descripcion'] = posting.get('descriptionNormalized', '') or posting.get('description', '')
        
        # Precio
        price_operations = posting.get('priceOperationTypes', [])
        if price_operations:
            first_price = price_operations[0].get('prices', [{}])[0]
            item['precio'] = first_price.get('amount')
            currency = first_price.get('currency', '')
            item['moneda'] = 'USD' if currency == 'USD' else 'ARS'
        
        # Expensas
        expenses = posting.get('expenses', {})
        if expenses:
            item['expensas'] = expenses.get('amount')
        
        # Ubicación (estructura correcta: postingLocation)
        posting_location = posting.get('postingLocation', {})
        if not posting_location:
            posting_location = {}
        
        location = posting_location.get('location', {})
        if not location:
            location = {}
            
        address = posting_location.get('address', {})
        if not address:
            address = {}
        
        # Buscar ciudad en la jerarquía de parent (label: "CIUDAD")
        ciudad = ''
        provincia = 'Santa Fe'
        current = location
        while current:
            label = current.get('label', '')
            if label == 'CIUDAD':
                ciudad = current.get('name', '')
            elif label == 'PROVINCIA':
                provincia = current.get('name', 'Santa Fe')
            current = current.get('parent')
        
        item['ciudad'] = ciudad
        item['provincia'] = provincia
        
        # Dirección y barrio
        item['direccion'] = address.get('name', '')
        item['barrio'] = ''  # Zonaprop no parece tener barrio en este nivel
        
        # Filtrar solo Rosario (excluir Rafaela y otras ciudades)
        ciudad_lower = ciudad.lower()
        if ciudad_lower != 'rosario':
            self.logger.info(f"❌ Descartado (ciudad={ciudad}): {item['titulo']}")
            return None
        
        # Características principales (mainFeatures es un dict de feature_id -> feature_data)
        main_features = posting.get('mainFeatures', {})
        if isinstance(main_features, dict):
            for feat_id, feat_data in main_features.items():
                if not isinstance(feat_data, dict):
                    continue
                
                # Extraer valor
                value_str = feat_data.get('value')
                if not value_str:
                    continue
                
                # Intentar convertir a número
                try:
                    value = int(value_str)
                except (ValueError, TypeError):
                    continue
                
                # Mapear por feature ID (más confiable que por label)
                if feat_id in self.FEATURES_MAP:
                    field = self.FEATURES_MAP[feat_id]
                    item[field] = value
                else:
                    # Fallback: mapear por label si no está en el mapa
                    label = feat_data.get('label', '').lower()
                    if 'ambiente' in label:
                        item['ambientes'] = value
                    elif 'dormitorio' in label:
                        item['dormitorios'] = value
                    elif 'baño' in label:
                        item['banos'] = value
                    elif 'cochera' in label or 'garage' in label:
                        item['cocheras'] = value
                    elif 'superficie total' in label:
                        item['superficie_total'] = value
                    elif 'superficie cubierta' in label:
                        item['superficie_cubierta'] = value
        
        # Características adicionales (features)
        features = posting.get('features', {})
        if features and isinstance(features, dict):
            for feat_id, feat_value in features.items():
                if feat_id in self.FEATURES_MAP:
                    field = self.FEATURES_MAP[feat_id]
                    if field not in item or not item[field]:
                        item[field] = feat_value
        
        # Tipo de propiedad (estructura correcta: realEstateType)
        real_estate_type = posting.get('realEstateType', {})
        tipo = real_estate_type.get('name', 'Casa')  # Default Casa en vez de Departamento
        # Normalizar plural a singular
        if tipo == 'Casas':
            tipo = 'Casa'
        elif tipo == 'Departamentos':
            tipo = 'Departamento'
        elif tipo == 'PHs':
            tipo = 'PH'
        item['tipo'] = tipo
        item['operacion'] = 'Alquiler'
        
        # Amenities y extras
        amenities = posting.get('tags', [])
        amenities_text = ' '.join(amenities).lower()
        titulo_desc = (item.get('titulo', '') + ' ' + item.get('descripcion', '')).lower()
        
        # Mascotas: detectar si acepta, pero descartar si dice "no" o "sin"
        mascotas_text = amenities_text + ' ' + titulo_desc
        tiene_mascota_positivo = any(word in mascotas_text for word in ['acepta mascota', 'permite mascota', 'admite mascota', 'pet friendly', 'pets allowed'])
        tiene_mascota_negativo = any(word in mascotas_text for word in ['no mascota', 'sin mascota', 'no acepta mascota', 'no se acepta mascota', 'no permite mascota', 'no admite mascota', 'not pet', 'no pet'])
        
        # Solo marcar True si hay mención positiva Y no hay mención negativa
        item['mascotas'] = tiene_mascota_positivo and not tiene_mascota_negativo
        
        item['patio'] = any(word in amenities_text for word in ['patio', 'jardín', 'jardin', 'terraza']) or \
                       any(word in titulo_desc for word in ['patio', 'jardín', 'jardin', 'terraza', 'quincho'])
        
        # Imágenes
        pictures = posting.get('pictures', [])
        self.logger.debug(f"Pictures encontradas: {len(pictures)} para {posting.get('id')}")
        if pictures:
            imagenes = []
            for pic in pictures:
                url_img = pic.get('url') or pic.get('image2x', '')
                if url_img:
                    imagenes.append(url_img)
            
            if imagenes:
                item['imagenes'] = imagenes
                item['imagen_principal'] = imagenes[0]
                self.logger.debug(f"✓ {len(imagenes)} imágenes agregadas para {item['titulo'][:50]}")
        
        # Metadata
        item['fecha_scraping'] = datetime.now().isoformat()
        
        return item
