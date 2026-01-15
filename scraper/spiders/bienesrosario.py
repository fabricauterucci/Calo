import scrapy
from scraper.items import PropiedadItem


class BienesrosarioSpider(scrapy.Spider):
    name = 'bienesrosario'
    allowed_domains = ['bienesrosario.com']
    
    def start_requests(self):
        base_url = 'https://www.bienesrosario.com/casas'
        yield scrapy.Request(base_url, callback=self.parse_listing)
    
    def parse_listing(self, response):
        """Parsea listado"""
        propiedades = response.css('div.propiedad, article.property')
        
        for prop in propiedades:
            url = prop.css('a::attr(href)').get()
            if url:
                if not url.startswith('http'):
                    url = response.urljoin(url)
                yield scrapy.Request(url, callback=self.parse_propiedad)
        
        # Paginación
        next_page = response.css('a.next::attr(href), a.pagination-next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_listing)
    
    def parse_propiedad(self, response):
        """Parsea detalle"""
        item = PropiedadItem()
        
        item['fuente'] = 'bienesrosario'
        item['url'] = response.url
        item['tipo'] = 'Casa'  # Este spider es para casas
        
        # Título
        item['titulo'] = response.css('h1::text').get()
        
        # Descripción
        item['descripcion'] = ' '.join(response.css('div.descripcion::text, div.description::text').getall())
        
        # Precio
        precio = response.css('span.precio::text, div.price::text').get()
        if precio:
            item['precio'] = precio
        
        # Ubicación
        ubicacion = response.css('span.ubicacion::text, div.location::text').get()
        if ubicacion:
            partes = ubicacion.split(',')
            if partes:
                item['barrio'] = partes[0].strip()
        
        # Características
        caracteristicas = response.css('ul.caracteristicas li, div.property-features span')
        for caract in caracteristicas:
            text = ' '.join(caract.css('::text').getall()).strip()
            
            if 'ambiente' in text.lower() or 'amb' in text.lower():
                item['ambientes'] = text
            elif 'dormitorio' in text.lower() or 'dorm' in text.lower():
                item['dormitorios'] = text
            elif 'baño' in text.lower():
                item['banos'] = text
            elif 'cochera' in text.lower() or 'garage' in text.lower():
                item['cocheras'] = text
            elif 'm²' in text or 'm2' in text:
                if 'cubierta' in text.lower():
                    item['superficie_cubierta'] = text
                else:
                    item['superficie_total'] = text
        
        # Mascotas
        amenities = response.css('ul.amenities li::text, div.amenities::text').getall()
        amenities_text = ' '.join(amenities).lower()
        item['mascotas'] = 'mascota' in amenities_text
        
        # Imágenes
        imagenes = response.css('div.galeria img::attr(src), div.gallery img::attr(src)').getall()
        if not imagenes:
            imagenes = response.css('img::attr(data-src)').getall()
        
        if imagenes:
            item['imagenes'] = [img for img in imagenes if img and 'http' in img]
            if item['imagenes']:
                item['imagen_principal'] = item['imagenes'][0]
        
        yield item
