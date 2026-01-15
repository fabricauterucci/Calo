import scrapy
import re
from datetime import datetime, timedelta
from scraper.items import PropiedadItem


class ZonapropSimpleSpider(scrapy.Spider):
    """
    Spider simplificado de ZonaProp - extrae desde el listado
    Sin navegar a páginas de detalle para evitar bloqueos
    """
    name = 'zonaprop_simple'
    allowed_domains = ['zonaprop.com.ar']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 1.5,
        'SELENIUM_ENABLED': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.SeleniumMiddleware': 800,
        },
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        },
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    def start_requests(self):
        # URLs específicas por tipo de propiedad para evitar bloqueos
        urls = [
            'https://www.zonaprop.com.ar/casas-alquiler-rosario.html',
            'https://www.zonaprop.com.ar/departamentos-alquiler-rosario.html',
            'https://www.zonaprop.com.ar/ph-alquiler-rosario.html',
        ]
        
        for url in urls:
            yield scrapy.Request(
                url,
                callback=self.parse_listing,
                meta={
                    'selenium': True,
                    'wait_for': 'div[data-posting-type="PROPERTY"]',
                    'wait_time': 8,
                    'scroll': True
                },
                dont_filter=True
        )
    
    def parse_listing(self, response):
        """Extrae propiedades directamente del listado"""
        self.logger.info(f"📄 Parseando listado: {response.url}")
        
        # Selectores para cada tarjeta de propiedad
        propiedades = response.css('div[data-posting-type="PROPERTY"]')
        self.logger.info(f"✅ Encontradas {len(propiedades)} propiedades")
        
        for prop in propiedades:
            item = PropiedadItem()
            item['fuente'] = 'zonaprop'
            
            # URL
            url = prop.css('a::attr(href)').get()
            if url:
                if not url.startswith('http'):
                    url = response.urljoin(url)
                item['url'] = url
                # Extraer ID desde URL
                if 'html' in url:
                    item['id_externo'] = url.split('-')[-1].split('.')[0].split('?')[0]
            
            # TÍTULO - Extraer de múltiples fuentes
            import re
            all_text = ' '.join(prop.css('::text').getall())
            
            # Intentar construir título desde características visibles
            titulo_parts = []
            
            # Tipo de propiedad
            if 'departamento' in all_text.lower():
                titulo_parts.append('Departamento')
            elif 'casa' in all_text.lower():
                titulo_parts.append('Casa')
            
            # Ambientes
            amb_match = re.search(r'(\d+)\s*amb', all_text, re.IGNORECASE)
            if amb_match:
                titulo_parts.append(f"{amb_match.group(1)} amb")
            
            # Superficie
            sup_match = re.search(r'(\d+)\s*m[²2]', all_text, re.IGNORECASE)
            if sup_match:
                titulo_parts.append(f"{sup_match.group(1)}m²")
            
            # Ubicación como parte del título
            ubicacion_elem = prop.css('[data-qa="POSTING_CARD_LOCATION"]::text').get()
            if ubicacion_elem:
                titulo_parts.append(f"en {ubicacion_elem.strip()}")
            
            titulo = ' '.join(titulo_parts) if titulo_parts else None
            if titulo:
                item['titulo'] = titulo
            
            # UBICACIÓN/DIRECCIÓN - desde la tarjeta
            ubicacion = (
                prop.css('[data-qa="POSTING_CARD_LOCATION"]::text').get() or
                prop.css('div[class*="location"]::text').get()
            )
            
            if ubicacion:
                ubicacion = ubicacion.strip()
                partes = [p.strip() for p in ubicacion.split(',')]
                if len(partes) >= 1:
                    item['barrio'] = partes[0]
                    item['direccion'] = ubicacion  # Usar ubicación completa como dirección
                if len(partes) >= 2:
                    item['ciudad'] = partes[1]
                else:
                    item['ciudad'] = 'Rosario'
            else:
                item['ciudad'] = 'Rosario'
            
            # PRECIO
            precio_text = (
                prop.css('div[data-qa="POSTING_CARD_PRICE"]::text').get() or
                prop.css('span.price::text').get() or
                prop.css('[class*="price"]::text').get()
            )
            if precio_text:
                item['precio'] = precio_text.strip()
                if 'USD' in precio_text or 'U$S' in precio_text:
                    item['moneda'] = 'USD'
                else:
                    item['moneda'] = 'ARS'
            
            # CARACTERÍSTICAS adicionales usando regex
            # Ambientes
            if amb_match:
                item['ambientes'] = amb_match.group(1)
            
            # Superficie
            if sup_match:
                item['superficie_total'] = sup_match.group(1)
            
            # Dormitorios
            dorm_match = re.search(r'(\d+)\s*dorm', all_text, re.IGNORECASE)
            if dorm_match:
                item['dormitorios'] = dorm_match.group(1)
            
            # Baños
            bano_match = re.search(r'(\d+)\s*ba[ñn]o', all_text, re.IGNORECASE)
            if bano_match:
                item['banos'] = bano_match.group(1)
            
            # Cocheras
            coch_match = re.search(r'(\d+)\s*coch', all_text, re.IGNORECASE)
            if coch_match:
                item['cocheras'] = coch_match.group(1)
            
            # Patio - buscar en el texto
            if re.search(r'\bpatio\b', all_text, re.IGNORECASE):
                item['patio'] = True
            
            # Descripción
            descripcion = prop.css('div[data-qa="POSTING_CARD_DESCRIPTION"]::text').get()
            if descripcion:
                item['descripcion'] = descripcion.strip()[:500]
            
            # Filtro de fecha - buscar indicadores de publicación reciente
            fecha_texto = ' '.join(prop.css('::text').getall()).lower()
            es_reciente = self._es_publicacion_reciente(fecha_texto)
            
            if not es_reciente:
                self.logger.debug(f"⏭️  Omitida (antigua): {item.get('titulo', 'Sin título')[:40]}")
                continue
            
            # Solo guardar si tenemos al menos título o ubicación
            if item.get('titulo') or item.get('direccion'):
                self.logger.info(f"✅ Extraída: {item.get('titulo', 'Sin título')[:50]}")
                yield item
        
        # Paginación
        next_page = response.css('a.pagination__next::attr(href), a[aria-label="Next"]::attr(href)').get()
        if next_page:
            self.logger.info(f"➡️  Siguiente página: {next_page}")
            yield response.follow(
                next_page,
                callback=self.parse_listing,
                meta={
                    'selenium': True,
                    'wait_for': 'div[data-posting-type="PROPERTY"]',
                    'wait_time': 5,
                    'scroll': True
                }
            )
    
    def _es_publicacion_reciente(self, texto):
        """
        Verifica si la publicación es reciente (último mes).
        Busca indicadores como: 'hoy', 'ayer', 'días', 'hace X días', etc.
        """
        texto_lower = texto.lower()
        
        # Indicadores de publicación muy reciente (siempre aceptar)
        if any(palabra in texto_lower for palabra in ['hoy', 'ayer', 'hace 1 día', 'hace 2 días']):
            return True
        
        # Buscar "hace X días"
        dias_match = re.search(r'hace\s+(\d+)\s+d[ií]as?', texto_lower)
        if dias_match:
            dias = int(dias_match.group(1))
            return dias <= 30  # Último mes
        
        # Buscar "hace X semanas"
        semanas_match = re.search(r'hace\s+(\d+)\s+semanas?', texto_lower)
        if semanas_match:
            semanas = int(semanas_match.group(1))
            return semanas <= 4  # Último mes (4 semanas)
        
        # Si no encuentra indicador de fecha, asumir que es reciente
        # (mejor incluir de más que filtrar publicaciones válidas)
        return True
