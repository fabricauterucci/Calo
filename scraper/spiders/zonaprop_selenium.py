import scrapy
from scraper.items import PropiedadItem


class ZonapropSeleniumSpider(scrapy.Spider):
    """
    Spider de ZonaProp usando Selenium para evitar bloqueos.
    
    Ejecutar con:
        scrapy crawl zonaprop_selenium
    """
    name = 'zonaprop_selenium'
    allowed_domains = ['zonaprop.com.ar']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'SELENIUM_ENABLED': True,  # ✅ Activar Selenium
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.SeleniumMiddleware': 800,
        },
    }
    
    def start_requests(self):
        base_url = 'https://www.zonaprop.com.ar/departamentos-alquiler-rosario.html'
        
        # ✅ Usar Selenium para esta request
        yield scrapy.Request(
            base_url,
            callback=self.parse_listing,
            meta={
                'selenium': True,
                'wait_for': 'div[data-posting-type="PROPERTY"]',  # Esperar a que carguen las propiedades
                'wait_time': 3,
                'scroll': True  # Scroll para lazy loading
            },
            dont_filter=True
        )
    
    def parse_listing(self, response):
        """Parsea la página de listado"""
        self.logger.info(f"📄 Parseando listado: {response.url}")
        
        # Selectores para cada propiedad
        propiedades = response.css('div[data-posting-type="PROPERTY"], div.posting-card')
        self.logger.info(f"✅ Encontradas {len(propiedades)} propiedades")
        
        for prop in propiedades:
            # Extraer URL de la propiedad
            url = prop.css('a::attr(href)').get()
            if not url:
                url = prop.css('a[data-to-posting]::attr(href)').get()
            
            if url:
                if not url.startswith('http'):
                    url = response.urljoin(url)
                
                # ✅ Usar Selenium también para el detalle
                yield scrapy.Request(
                    url,
                    callback=self.parse_propiedad,
                    meta={
                        'selenium': True,
                        'wait_for': 'h1, .price-operation',
                        'wait_time': 2
                    }
                )
        
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
                    'wait_time': 3,
                    'scroll': True
                }
            )
    
    def parse_propiedad(self, response):
        """Parsea el detalle de una propiedad"""
        item = PropiedadItem()
        
        item['fuente'] = 'zonaprop'
        item['url'] = response.url
        item['id_externo'] = response.url.split('-')[-1].split('.')[0]
        
        # DEBUG: Log what we're getting
        all_h1s = response.css('h1::text').getall()
        response_length = len(response.text)
        self.logger.debug(f"🔍 DEBUG URL: {response.url}")
        self.logger.debug(f"🔍 DEBUG Response length: {response_length} chars")
        self.logger.debug(f"🔍 DEBUG H1s encontrados: {all_h1s}")
        
        # Check if this is actually a detail page
        is_detail_page = 'clasificado/' in response.url and 'html' in response.url
        has_title_property = bool(response.css('h1.title-property').get())
        self.logger.debug(f"🔍 DEBUG Is detail page URL: {is_detail_page}, has title-property class: {has_title_property}")
        
        # Título - múltiples selectores
        titulo = (
            response.css('h1.title-property::text').get() or
            response.css('h1[data-qa="POSTING_CARD_TITLE"]::text').get() or
            response.css('h1.posting-title::text').get() or
            response.css('h1::text').get()
        )
        
        # DEBUG
        self.logger.debug(f"🔍 DEBUG Titulo extraído: {titulo}")
        
        item['titulo'] = titulo.strip() if titulo else None
        
        # Descripción
        descripcion = (
            response.css('div.section-description p::text').getall() or
            response.css('div[data-qa="POSTING_DESCRIPTION"]::text').getall() or
            response.css('div.description p::text').getall()
        )
        item['descripcion'] = ' '.join(descripcion).strip() if descripcion else None
        
        # Precio - selectores actualizados y mejorados
        precio_text = (
            response.css('div.price-value::text').get() or  # Selector encontrado en debug
            response.css('div.price-operation::text').get() or
            response.css('span[data-qa="POSTING_CARD_PRICE"]::text').get() or
            response.css('div.price-container span::text').get() or
            response.css('span.price::text').get()
        )
        
        # También buscar en el texto completo si no encuentra con selectores
        if not precio_text:
            precio_full = ' '.join(response.css('div[class*="price"]::text').getall())
            if precio_full:
                precio_text = precio_full
        
        if precio_text:
            item['precio'] = precio_text.strip()
            if 'USD' in precio_text or 'U$S' in precio_text or 'u$s' in precio_text.lower():
                item['moneda'] = 'USD'
            else:
                item['moneda'] = 'ARS'
        
        # Expensas
        expensas = (
            response.css('li:contains("Expensas") span::text').get() or
            response.css('span[data-qa="expensas"]::text').get()
        )
        if expensas:
            item['expensas'] = expensas.strip()
        
        # Ubicación - mejorada con meta tags
        # Intentar extraer ciudad de meta keywords o tags JSON-LD
        ciudad_meta = response.xpath('//meta[@name="keywords"]/@content').get()
        if ciudad_meta and 'Rosario' in ciudad_meta:
            item['ciudad'] = 'Rosario'
        
        # Extraer ubicación desde scripts JSON-LD
        json_ld = response.xpath('//script[@type="application/ld+json"]/text()').get()
        if json_ld:
            import json
            try:
                data = json.loads(json_ld)
                if isinstance(data, dict) and 'address' in data:
                    addr = data['address']
                    if 'addressRegion' in addr:
                        item['ciudad'] = addr['addressRegion']
                    if 'streetAddress' in addr:
                        item['direccion'] = addr['streetAddress']
            except:
                pass
        
        # Fallback: selectores CSS tradicionales
        ubicacion = (
            response.css('h2.title-location::text').get() or
            response.css('h2[data-qa="POSTING_CARD_LOCATION"]::text').get() or
            response.css('div.location-container::text').get()
        )
        
        if ubicacion:
            ubicacion = ubicacion.strip()
            partes = [p.strip() for p in ubicacion.split(',')]
            if len(partes) >= 1 and not item.get('barrio'):
                item['barrio'] = partes[0]
            if len(partes) >= 2 and not item.get('ciudad'):
                item['ciudad'] = partes[1]
        
        direccion = (
            response.css('div.location-address::text').get() or
            response.css('span[data-qa="POSTING_CARD_ADDRESS"]::text').get()
        )
        
        if direccion and not item.get('direccion'):
            item['direccion'] = direccion.strip()
        
        # Características
        features = response.css('li.icon-feature, div.features span')
        for feature in features:
            text = ' '.join(feature.css('::text').getall()).strip()
            if text:
                if 'amb' in text.lower():
                    item['ambientes'] = text
                elif 'dorm' in text.lower():
                    item['dormitorios'] = text
                elif 'baño' in text.lower():
                    item['banos'] = text
                elif 'coch' in text.lower():
                    item['cocheras'] = text
                elif 'm²' in text or 'm2' in text:
                    if 'total' in text.lower():
                        item['superficie_total'] = text
                    elif 'cubierta' in text.lower():
                        item['superficie_cubierta'] = text
                    else:
                        item['superficie_total'] = text
        
        # Amenities - buscar mascotas
        amenities = (
            response.css('ul.amenities li::text').getall() +
            response.css('div[data-qa="amenities"] span::text').getall() +
            response.css('div.amenities-list span::text').getall()
        )
        amenities_text = ' '.join(amenities).lower()
        item['mascotas'] = 'mascota' in amenities_text or 'pet' in amenities_text
        
        # Imágenes - usando selector correcto encontrado en debug
        imagenes = []
        
        # Selector específico de ZonaProp (encontrado en HTML real)
        imagenes_urls = response.css('img.imageGrid-module__imgProperty___KJ-2G::attr(src)').getall()
        
        # Fallbacks si el selector no funciona
        if not imagenes_urls:
            imagenes_urls = (
                response.css('div.carousel-gallery img::attr(data-src)').getall() or
                response.css('div[data-qa="POSTING_PICTURES_VIEWER"] img::attr(src)').getall() or
                response.css('img[alt*="foto"]::attr(src)').getall() or
                response.css('div.swiper-slide img::attr(src)').getall()
            )
        
        # Filtrar imágenes válidas (excluir logos, iconos, etc.)
        for img in imagenes_urls:
            if img and ('http' in img or img.startswith('//')):
                # Excluir logos y SVGs
                if any(x in img.lower() for x in ['logo', '.svg', 'icon', 'naventcdn.com/ficha']):
                    continue
                # Asegurar que es de zonapropcdn (imágenes reales de propiedades)
                if 'zonapropcdn.com/avisos' in img or 'imgar.zonapropcdn.com' in img:
                    if img.startswith('//'):
                        img = 'https:' + img
                    imagenes.append(img)
        
        if imagenes:
            item['imagenes'] = imagenes[:10]  # Máximo 10 imágenes
            item['imagen_principal'] = imagenes[0]
        
        self.logger.info(f"✅ Scrapeada: {item.get('titulo', 'Sin título')[:50]} - {len(imagenes)} imágenes")
        yield item
