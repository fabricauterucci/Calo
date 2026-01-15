import scrapy
from scraper.items import PropiedadItem
import re


class ArgenpropSimpleSpider(scrapy.Spider):
    """
    Spider optimizado de ArgentProp - extrae desde el listado
    """
    name = 'argenprop_simple'
    allowed_domains = ['argenprop.com']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'SELENIUM_ENABLED': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.SeleniumMiddleware': 800,
        },
    }
    
    def start_requests(self):
        base_url = 'https://www.argenprop.com/departamentos/alquiler/rosario-santa-fe'
        
        yield scrapy.Request(
            base_url,
            callback=self.parse_listing,
            meta={
                'selenium': True,
                'wait_for': 'div.listing__item',
                'wait_time': 5,
                'scroll': True
            }
        )
    
    def parse_listing(self, response):
        """Extrae propiedades directamente del listado"""
        self.logger.info(f"📄 Parseando listado: {response.url}")
        
        propiedades = response.css('div.listing__item, div.card')
        self.logger.info(f"✅ Encontradas {len(propiedades)} propiedades")
        
        for prop in propiedades:
            item = PropiedadItem()
            item['fuente'] = 'argenprop'
            
            # URL
            url = prop.css('a.card::attr(href), a::attr(href)').get()
            if url:
                if not url.startswith('http'):
                    url = response.urljoin(url)
                item['url'] = url
            
            # Extraer todo el texto para regex
            all_text = ' '.join(prop.css('::text').getall())
            
            # Construir título
            titulo_parts = []
            
            # Tipo
            if 'departamento' in all_text.lower():
                titulo_parts.append('Departamento')
            elif 'casa' in all_text.lower():
                titulo_parts.append('Casa')
            
            # Ambientes
            amb_match = re.search(r'(\d+)\s*amb', all_text, re.IGNORECASE)
            if amb_match:
                titulo_parts.append(f"{amb_match.group(1)} amb")
                item['ambientes'] = amb_match.group(1)
            
            # Superficie
            sup_match = re.search(r'(\d+)\s*m[²2]', all_text, re.IGNORECASE)
            if sup_match:
                titulo_parts.append(f"{sup_match.group(1)}m²")
                item['superficie_total'] = sup_match.group(1)
            
            # Ubicación
            ubicacion = (
                prop.css('[class*="location"]::text').get() or
                prop.css('.card__address::text').get() or
                prop.css('.listing__item-address::text').get()
            )
            
            if ubicacion:
                ubicacion = ubicacion.strip()
                titulo_parts.append(f"en {ubicacion}")
                item['direccion'] = ubicacion
                
                # Extraer barrio y ciudad
                partes = [p.strip() for p in ubicacion.split(',')]
                if len(partes) >= 1:
                    item['barrio'] = partes[0]
                if 'rosario' in ubicacion.lower():
                    item['ciudad'] = 'Rosario'
                elif len(partes) >= 2:
                    item['ciudad'] = partes[-1]
            else:
                item['ciudad'] = 'Rosario'
            
            if titulo_parts:
                item['titulo'] = ' '.join(titulo_parts)
            
            # PRECIO
            precio_text = (
                prop.css('[class*="price"]::text').get() or
                prop.css('.card__price::text').get() or
                prop.css('.listing__item-price::text').get()
            )
            if precio_text:
                item['precio'] = precio_text.strip()
                if 'USD' in precio_text or 'U$S' in precio_text:
                    item['moneda'] = 'USD'
                else:
                    item['moneda'] = 'ARS'
            
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
            
            # Patio
            if re.search(r'\bpatio\b', all_text, re.IGNORECASE):
                item['patio'] = True
            
            # Mascotas
            if re.search(r'mascota|pet', all_text, re.IGNORECASE):
                item['mascotas'] = True
            
            if item.get('titulo') or item.get('direccion'):
                self.logger.info(f"✅ Extraída: {item.get('titulo', 'Sin título')[:50]}")
                yield item
        
        # Paginación
        next_page = response.css('a.pagination__page--next::attr(href), a[rel="next"]::attr(href)').get()
        if next_page:
            self.logger.info(f"➡️  Siguiente página: {next_page}")
            yield response.follow(
                next_page,
                callback=self.parse_listing,
                meta={
                    'selenium': True,
                    'wait_for': 'div.listing__item',
                    'wait_time': 5,
                    'scroll': True
                }
            )
