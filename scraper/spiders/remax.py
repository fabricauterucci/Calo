import scrapy
from scraper.items import PropiedadItem


class RemaxSpider(scrapy.Spider):
    name = 'remax'
    allowed_domains = ['remax.com.ar']
    
    def start_requests(self):
        base_url = 'https://www.remax.com.ar/departamentos-en-alquiler-en-rosario'
        yield scrapy.Request(base_url, callback=self.parse_listing)
    
    def parse_listing(self, response):
        """Parsea listado"""
        propiedades = response.css('div.property-card, article.property')
        
        for prop in propiedades:
            url = prop.css('a::attr(href)').get()
            if url:
                if not url.startswith('http'):
                    url = response.urljoin(url)
                yield scrapy.Request(url, callback=self.parse_propiedad)
        
        # Paginación
        next_page = response.css('a.next-page::attr(href), a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_listing)
    
    def parse_propiedad(self, response):
        """Parsea detalle"""
        item = PropiedadItem()
        
        item['fuente'] = 'remax'
        item['url'] = response.url
        
        # Título
        item['titulo'] = response.css('h1::text, h1.property-title::text').get()
        
        # Descripción
        item['descripcion'] = ' '.join(response.css('div.description p::text, div.property-description::text').getall())
        
        # Precio
        precio = response.css('span.price::text, div.property-price::text').get()
        if precio:
            item['precio'] = precio
            if 'USD' in precio or 'U$S' in precio:
                item['moneda'] = 'USD'
        
        # Ubicación
        barrio = response.css('span.neighborhood::text, div.location::text').get()
        if barrio:
            item['barrio'] = barrio.strip()
        
        # Características
        features = response.css('ul.features li, div.property-features span')
        for feature in features:
            text = feature.css('::text').get()
            if not text:
                text = ' '.join(feature.css('::text').getall())
            
            if text:
                text = text.strip()
                if 'amb' in text.lower() or 'ambiente' in text.lower():
                    item['ambientes'] = text
                elif 'dorm' in text.lower():
                    item['dormitorios'] = text
                elif 'baño' in text.lower():
                    item['banos'] = text
                elif 'coch' in text.lower() or 'garage' in text.lower():
                    item['cocheras'] = text
                elif 'm²' in text or 'm2' in text:
                    item['superficie_total'] = text
        
        # Mascotas
        amenities = response.css('ul.amenities li::text, div.amenities span::text').getall()
        amenities_text = ' '.join(amenities).lower()
        item['mascotas'] = 'mascota' in amenities_text
        
        # Imágenes
        imagenes = response.css('div.gallery img::attr(src), img.property-image::attr(src)').getall()
        if not imagenes:
            imagenes = response.css('img::attr(data-src)').getall()
        
        if imagenes:
            item['imagenes'] = [img for img in imagenes if img and 'http' in img]
            if item['imagenes']:
                item['imagen_principal'] = item['imagenes'][0]
        
        yield item
