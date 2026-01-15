import scrapy
from scraper.items import PropiedadItem


class MapropiedadesSpider(scrapy.Spider):
    name = 'mapropiedades'
    allowed_domains = ['mapropiedades.com.ar']
    
    def start_requests(self):
        base_url = 'https://www.mapropiedades.com.ar/alquiler'
        yield scrapy.Request(base_url, callback=self.parse_listing)
    
    def parse_listing(self, response):
        """Parsea listado"""
        propiedades = response.css('div.propiedad-item, article.property-card')
        
        for prop in propiedades:
            url = prop.css('a::attr(href)').get()
            if url:
                if not url.startswith('http'):
                    url = response.urljoin(url)
                yield scrapy.Request(url, callback=self.parse_propiedad)
        
        # Paginación
        next_page = response.css('a.next::attr(href), a[aria-label="Next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_listing)
    
    def parse_propiedad(self, response):
        """Parsea detalle"""
        item = PropiedadItem()
        
        item['fuente'] = 'mapropiedades'
        item['url'] = response.url
        
        # Título
        item['titulo'] = response.css('h1::text').get()
        
        # Descripción
        item['descripcion'] = ' '.join(response.css('div.descripcion::text, div.description p::text').getall())
        
        # Precio
        precio = response.css('span.precio::text, div.price::text').get()
        if precio:
            item['precio'] = precio
        
        # Ubicación
        ubicacion = response.css('span.ubicacion::text, div.location::text').get()
        if ubicacion:
            item['barrio'] = ubicacion.strip()
        
        # Características
        caracteristicas = response.css('ul.caracteristicas li, div.features span')
        for caract in caracteristicas:
            text = ' '.join(caract.css('::text').getall()).strip()
            
            if 'ambiente' in text.lower():
                item['ambientes'] = text
            elif 'dormitorio' in text.lower():
                item['dormitorios'] = text
            elif 'baño' in text.lower():
                item['banos'] = text
            elif 'cochera' in text.lower():
                item['cocheras'] = text
            elif 'm²' in text or 'm2' in text:
                item['superficie_total'] = text
            elif 'mascota' in text.lower():
                item['mascotas'] = True
        
        # Imágenes
        imagenes = response.css('div.galeria img::attr(src), div.gallery img::attr(src)').getall()
        if imagenes:
            item['imagenes'] = imagenes
            item['imagen_principal'] = imagenes[0]
        
        yield item
