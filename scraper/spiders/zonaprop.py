import scrapy
from scraper.items import PropiedadItem


class ZonapropSpider(scrapy.Spider):
    name = 'zonaprop'
    allowed_domains = ['zonaprop.com.ar']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 2,  # Limitar concurrencia con Selenium
        'SELENIUM_ENABLED': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.SeleniumMiddleware': 800,
        },
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
    }
    
    def start_requests(self):
        # URL de búsqueda de departamentos en alquiler en Rosario
        base_url = 'https://www.zonaprop.com.ar/departamentos-alquiler-rosario.html'
        yield scrapy.Request(
            base_url, 
            callback=self.parse_listing,
            errback=self.errback_httpbin,
            meta={
                'selenium': True,
                'wait_for': 'div[data-posting-type="PROPERTY"]',
                'wait_time': 10,
            },
            dont_filter=True
        )
    
    def parse_listing(self, response):
        """Parsea la página de listado"""
        # Selectores para cada propiedad en el listado
        propiedades = response.css('div[data-posting-type="PROPERTY"]')
        
        self.logger.info(f"✅ Encontradas {len(propiedades)} propiedades en listado")
        
        for prop in propiedades:
            url = prop.css('a.go-to-posting::attr(href)').get()
            if url:
                if not url.startswith('http'):
                    url = response.urljoin(url)
                yield scrapy.Request(
                    url, 
                    callback=self.parse_propiedad,
                    meta={
                        'selenium': True,
                        'wait_for': 'body',
                        'wait_time': 8,
                    }
                )
        
        # Paginación
        next_page = response.css('a.pagination__next::attr(href)').get()
        if next_page:
            yield response.follow(
                next_page, 
                callback=self.parse_listing,
                meta={
                    'selenium': True,
                    'wait_for': 'div[data-posting-type="PROPERTY"]',
                    'wait_time': 10,
                }
            )
    
    def parse_propiedad(self, response):
        """Parsea el detalle de una propiedad"""
        item = PropiedadItem()
        
        item['fuente'] = 'zonaprop'
        item['url'] = response.url
        item['id_externo'] = response.url.split('-')[-1].replace('.html', '')
        
        # Básicos
        item['titulo'] = response.css('h1.title-property::text').get()
        item['descripcion'] = ' '.join(response.css('div.section-description p::text').getall())
        
        # Precio
        precio_text = response.css('div.price-operation span::text').get()
        if precio_text:
            item['precio'] = precio_text
            if 'USD' in precio_text or 'U$S' in precio_text:
                item['moneda'] = 'USD'
        
        # Expensas
        expensas = response.css('li:contains("Expensas") span::text').get()
        if expensas:
            item['expensas'] = expensas
        
        # Ubicación
        ubicacion = response.css('h2.title-location::text').get()
        if ubicacion:
            partes = [p.strip() for p in ubicacion.split(',')]
            if len(partes) >= 1:
                item['barrio'] = partes[0]
            if len(partes) >= 2:
                item['ciudad'] = partes[1]
        
        # Características
        features = response.css('li.icon-feature')
        for feature in features:
            text = feature.css('::text').get()
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
        amenities = response.css('ul.amenities li::text').getall()
        amenities_text = ' '.join(amenities).lower()
        item['mascotas'] = 'mascota' in amenities_text or 'pet' in amenities_text
        
        # Imágenes
        imagenes = response.css('div.carousel-gallery img::attr(src)').getall()
        if imagenes:
            item['imagenes'] = imagenes
            item['imagen_principal'] = imagenes[0]
        
        yield item
    
    def errback_httpbin(self, failure):
        self.logger.error(f'Error en request: {failure.request.url}')
        self.logger.error(f'Razón: {failure.value}')
