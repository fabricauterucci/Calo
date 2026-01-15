import scrapy
from scraper.items import PropiedadItem


class ArgenpropSpider(scrapy.Spider):
    name = 'argenprop'
    allowed_domains = ['argenprop.com']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'ROBOTSTXT_OBEY': True,
    }
    
    def start_requests(self):
        # URLs con filtros: PH y casas en Rosario, $330k-800k, con patio, solo pesos
        urls = [
            'https://www.argenprop.com/ph/alquiler/rosario-o-rosario-santa-fe/pesos-330000-800000?solo-ver-pesos',
            'https://www.argenprop.com/casas/alquiler/rosario-o-rosario-santa-fe/pesos-330000-800000?con-ambiente-patio&solo-ver-pesos',
        ]
        
        for url in urls:
            yield scrapy.Request(
                url, 
                callback=self.parse_listing,
                errback=self.errback_httpbin
            )
    
    def parse_listing(self, response):
        """Parsea listado de propiedades"""
        propiedades = response.css('div.listing__item')
        
        for prop in propiedades:
            url = prop.css('a.card::attr(href)').get()
            if url:
                if not url.startswith('http'):
                    url = response.urljoin(url)
                yield scrapy.Request(url, callback=self.parse_propiedad)
        
        # Paginación
        next_page = response.css('a.pagination__page--next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_listing)
    
    def parse_propiedad(self, response):
        """Parsea detalle de propiedad"""
        item = PropiedadItem()
        
        item['fuente'] = 'argenprop'
        item['url'] = response.url
        
        # Título - mejorado
        titulo = (
            response.css('h1.titlebar__address::text').get() or
            response.css('h1.card__title::text').get() or
            response.css('h1[data-qa="titulo"]::text').get() or
            response.css('h1::text').get()
        )
        item['titulo'] = titulo.strip() if titulo else None
        
        # Descripción
        descripcion = (
            response.css('div.section--description p::text').getall() or
            response.css('div.property-description::text').getall() or
            response.css('div[data-qa="descripcion"]::text').getall()
        )
        item['descripcion'] = ' '.join(descripcion).strip() if descripcion else None
        
        # Precio - mejorado
        precio = (
            response.css('p.titlebar__price::text').get() or
            response.css('span.card__price::text').get() or
            response.css('div.price-value::text').get()
        )
        if precio:
            item['precio'] = precio.strip()
            if 'USD' in precio or 'U$S' in precio:
                item['moneda'] = 'USD'
        
        # Expensas
        expensas = (
            response.css('div.titlebar__values span:contains("Exp") + span::text').get() or
            response.css('span[data-qa="expensas"]::text').get()
        )
        if expensas:
            item['expensas'] = expensas.strip()
        
        # Ubicación - mejorada con dirección
        barrio = (
            response.css('h2.titlebar__zone::text').get() or
            response.css('span.card__location::text').get() or
            response.css('div[data-qa="barrio"]::text').get()
        )
        if barrio:
            item['barrio'] = barrio.strip()
        
        # Dirección
        direccion = (
            response.css('span.titlebar__address::text').get() or
            response.css('div.location-street::text').get()
        )
        if direccion:
            item['direccion'] = direccion.strip()
        
        # Características principales
        caracteristicas = response.css('ul.property-features li')
        for caract in caracteristicas:
            text = caract.css('::text').getall()
            text = ' '.join(text).strip()
            
            if 'amb' in text.lower():
                item['ambientes'] = text
            elif 'dorm' in text.lower():
                item['dormitorios'] = text
            elif 'baño' in text.lower():
                item['banos'] = text
            elif 'coch' in text.lower():
                item['cocheras'] = text
            elif 'm²' in text:
                if 'total' in text.lower():
                    item['superficie_total'] = text
                elif 'cubierta' in text.lower():
                    item['superficie_cubierta'] = text
                else:
                    item['superficie_total'] = text
        
        # Características detalladas - buscar mascotas
        detalles = (
            response.css('div.property-details li::text').getall() +
            response.css('ul.amenities li::text').getall()
        )
        detalles_text = ' '.join(detalles).lower()
        item['mascotas'] = 'mascota' in detalles_text or 'pet' in detalles_text
        
        # Imágenes - selectores mejorados
        imagenes = []
        
        # Intentar diferentes selectores
        imagenes_urls = (
            response.css('div.property-gallery img::attr(data-src)').getall() or
            response.css('div.slider-gallery img::attr(data-src)').getall() or
            response.css('div.gallery img::attr(data-src)').getall() or
            response.css('img.gallery-image::attr(data-src)').getall()
        )
        
        # Si no hay data-src, probar con src
        if not imagenes_urls:
            imagenes_urls = (
                response.css('div.property-gallery img::attr(src)').getall() or
                response.css('div.gallery-image img::attr(src)').getall() or
                response.css('div.slider img::attr(src)').getall()
            )
        
        # Filtrar URLs válidas
        for img in imagenes_urls:
            if img and ('http' in img or img.startswith('//')):
                if img.startswith('//'):
                    img = 'https:' + img
                # Evitar iconos pequeños
                if not any(skip in img.lower() for skip in ['icon', 'logo', 'avatar', 'placeholder']):
                    imagenes.append(img)
        
        if imagenes:
            item['imagenes'] = imagenes[:10]  # Máximo 10 imágenes
            item['imagen_principal'] = imagenes[0]
        
        self.logger.info(f"✅ Scrapeada: {item.get('titulo', 'Sin título')[:50]} - {len(imagenes)} imgs")
        yield item
    
    def errback_httpbin(self, failure):
        self.logger.error(f'Error en request: {failure.request.url}')
