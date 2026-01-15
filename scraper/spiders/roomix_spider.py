import scrapy
import re
from datetime import datetime
from scraper.items import PropiedadItem


class RoomixSpider(scrapy.Spider):
    """
    Spider para Roomix.ai - extrae casas en alquiler en Rosario con patio
    """
    name = 'roomix'
    allowed_domains = ['roomix.ai']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 0.3,  # Reducido de 1.0 a 0.3 para más velocidad
        'CONCURRENT_REQUESTS': 16,  # Aumentar concurrencia
        'SELENIUM_ENABLED': False,
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    def start_requests(self):
        # URLs con filtros: casas, PH y departamentos, Rosario, $300k-800k, con patio
        urls = [
            'https://roomix.ai/buscar/alquilar/casas/en-rosario/total-desde-300000-hasta-800000-ars/con-patio/mas-recientes',
            'https://roomix.ai/buscar/alquilar/ph/en-rosario/total-desde-300000-hasta-800000-ars/con-patio/mas-recientes',
            'https://roomix.ai/buscar/alquilar/departamentos/en-rosario/total-desde-300000-hasta-800000-ars/con-patio/mas-recientes',
        ]
        
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)
    
    def parse(self, response):
        """Parsea el listado y extrae links de propiedades"""
        self.logger.info(f"📄 Parseando listado: {response.url}")
        
        # Extraer links de propiedades
        property_links = response.css('a[href*="/propiedad/"]::attr(href)').getall()
        property_links = list(set(property_links))  # Deduplicar
        
        self.logger.info(f"✅ Encontrados {len(property_links)} links de propiedades")
        
        for link in property_links:
            full_url = response.urljoin(link)
            yield scrapy.Request(full_url, callback=self.parse_property)
        
        # Paginación
        next_page = response.css('a[rel="next"]::attr(href), a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
    
    def parse_property(self, response):
        """Parsea los datos de una propiedad individual"""
        self.logger.info(f"🏠 Parseando propiedad: {response.url}")
        
        item = PropiedadItem()
        
        try:
            # Título - buscar en h1 o meta tags
            titulo = response.css('h1::text').get()
            if not titulo:
                titulo = response.css('meta[property="og:title"]::attr(content)').get()
            titulo = titulo.strip() if titulo else None
            
            # Precio - buscar patrones de precio
            precio = None
            precio_text = response.css('span.price::text, div.price::text, strong.price::text').get()
            
            if not precio_text:
                # Buscar en el texto completo
                precio_match = re.search(r'\$\s*([\d.,]+)', response.text)
                if precio_match:
                    precio_text = precio_match.group(1)
            
            if precio_text:
                try:
                    precio_clean = re.sub(r'[^\d]', '', precio_text)
                    precio = float(precio_clean)
                except:
                    pass
            
            # Dirección
            direccion = response.css('address::text, .address::text, .location::text').get()
            if not direccion:
                direccion = "Rosario"
            else:
                direccion = direccion.strip()
            
            # Superficie
            superficie = None
            superficie_text = response.css('*:contains("m²")::text, *:contains("m2")::text').re_first(r'([\d.,]+)\s*m[²2]')
            if superficie_text:
                try:
                    superficie = float(superficie_text.replace(',', '.'))
                except:
                    pass
            
            # Dormitorios
            dormitorios = None
            dormitorios_match = response.css('*:contains("dormitorio")::text, *:contains("habitación")::text').re_first(r'(\d+)\s*(?:dormitorio|habitación|habitacion)')
            if dormitorios_match:
                try:
                    dormitorios = int(dormitorios_match)
                except:
                    pass
            
            # Baños
            banos = None
            banos_match = response.css('*:contains("baño")::text').re_first(r'(\d+)\s*baño')
            if banos_match:
                try:
                    banos = int(banos_match)
                except:
                    pass
            
            # Ambientes
            ambientes = None
            ambientes_match = response.css('*:contains("ambiente")::text').re_first(r'(\d+)\s*ambiente')
            if ambientes_match:
                try:
                    ambientes = int(ambientes_match)
                except:
                    pass
            
            # URL
            url = response.url
            
            # Tipo - detectar basado en URL o título
            titulo_lower = titulo.lower() if titulo else ''
            if '/departamentos/' in response.url or 'departamento' in titulo_lower or 'depto' in titulo_lower:
                tipo = 'departamento'
            elif '/ph/' in response.url or 'ph' in titulo_lower:
                tipo = 'ph'
            else:
                tipo = 'casa'
            
            # Detectar patio (ya está en el filtro, pero verificamos)
            texto_completo = f"{titulo} {response.text}".lower()
            patio = any(word in texto_completo for word in [
                'patio', 'jardín', 'jardin', 'quincho', 
                'parrilla', 'terraza', 'balcón', 'balcon'
            ])
            
            # Detectar mascotas
            mascotas = any(word in texto_completo for word in [
                'mascota', 'pet', 'perro', 'gato', 
                'acepta mascota', 'permite mascota'
            ])
            
            # Extraer barrio
            barrio = self._extraer_barrio(direccion)
            
            # Llenar item
            item['titulo'] = titulo or 'Casa en alquiler'
            item['direccion'] = direccion
            item['precio'] = precio
            item['moneda'] = 'ARS'
            item['tipo'] = tipo
            item['ambientes'] = ambientes
            item['dormitorios'] = dormitorios
            item['banos'] = banos
            item['superficie_total'] = superficie
            item['ciudad'] = 'Rosario'
            item['barrio'] = barrio
            item['fuente'] = 'roomix'
            item['url'] = url
            item['patio'] = patio
            item['mascotas'] = mascotas
            item['fecha_scraping'] = datetime.now().isoformat()
            
            self.logger.info(f"✅ Extraída: {titulo}")
            yield item
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error procesando propiedad: {e}")
            return
    
    def _extraer_barrio(self, texto):
        """Extrae el barrio del texto"""
        if not texto:
            return None
            
        barrios_rosario = [
            'Centro', 'Distrito Centro', 'Abasto', 'Alberdi', 'Fisherton',
            'Echesortu', 'Pichincha', 'Luis Agote', 'República de la Sexta',
            'Martín', 'Puerto Norte', 'Distrito Norte', 'Distrito Sur',
            'Distrito Noroeste', 'Refinería', 'La Florida', 'Godoy',
            'Lisandro de la Torre', 'Triángulo Moderno', 'Sarmiento',
            'Bella Vista', 'Parque Casado', 'Barrio Industrial',
            'Alberdi', 'Ludueña', 'Triángulo',
        ]
        
        texto_lower = texto.lower()
        for barrio in barrios_rosario:
            if barrio.lower() in texto_lower:
                return barrio
        
        return None
