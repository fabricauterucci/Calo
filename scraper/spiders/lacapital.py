import scrapy
from scraper.items import PropiedadItem


class LacapitalSpider(scrapy.Spider):
    name = 'lacapital'
    allowed_domains = ['inmuebles.lacapital.com.ar']
    
    def start_requests(self):
        base_url = 'https://inmuebles.lacapital.com.ar/buscar-propiedades/?inmueble_hidden=Departamento&operacion_hidden=Alquiler'
        yield scrapy.Request(base_url, callback=self.parse_listing)
    
    def parse_listing(self, response):
        """Parsea listado"""
        propiedades = response.css('div.property-item, article.propiedad')
        
        for prop in propiedades:
            url = prop.css('a::attr(href)').get()
            if url:
                if not url.startswith('http'):
                    url = response.urljoin(url)
                yield scrapy.Request(url, callback=self.parse_propiedad)
        
        # Paginación
        next_page = response.css('a.siguiente::attr(href), a.next-page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_listing)
    
    def parse_propiedad(self, response):
        """Parsea detalle"""
        item = PropiedadItem()
        
        item['fuente'] = 'lacapital'
        item['url'] = response.url
        
        # Título
        item['titulo'] = response.css('h1.titulo::text, h1::text').get()
        
        # Descripción
        item['descripcion'] = ' '.join(response.css('div.descripcion::text, div.description::text').getall())
        
        # Precio
        precio = response.css('span.precio::text, div.price span::text').get()
        if precio:
            item['precio'] = precio
        
        # Ubicación
        barrio = response.css('span.barrio::text, div.location span::text').get()
        if barrio:
            item['barrio'] = barrio.strip()
        
        # Características
        features = response.css('ul.caracteristicas li, div.features div')
        for feature in features:
            text = ' '.join(feature.css('::text').getall()).strip()
            
            if 'ambiente' in text.lower():
                item['ambientes'] = text
            elif 'dormitorio' in text.lower():
                item['dormitorios'] = text
            elif 'baño' in text.lower():
                item['banos'] = text
            elif 'cochera' in text.lower():
                item['cocheras'] = text
            elif 'm²' in text:
                item['superficie_total'] = text
        
        # Imágenes
        imagenes = response.css('div.galeria img::attr(src), div.fotos img::attr(src)').getall()
        if imagenes:
            item['imagenes'] = imagenes
            item['imagen_principal'] = imagenes[0]
        
        yield item
