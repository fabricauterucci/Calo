import scrapy
import re
from datetime import datetime
from scraper.items import PropiedadItem


class RentolaSpider(scrapy.Spider):
    """
    Spider para Rentola.ar - extrae propiedades en alquiler de Rosario
    """
    name = 'rentola'
    allowed_domains = ['rentola.ar']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 0.8,
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
        urls = [
            # URL con filtros: casas y deptos, 2 ambientes, $400k-800k, con patio
            'https://rentola.ar/alquiler?location=rosario&property_types=house&property_types=apartment&rent=400000-800000&rooms=2&facility=with_patio',
        ]
        
        for url in urls:
            # Para listados NO necesitamos Selenium, el HTML viene completo
            yield scrapy.Request(
                url,
                callback=self.parse_listing,
                meta={'selenium': False},
                dont_filter=True
            )
    
    def parse_listing(self, response):
        """Parsea el listado de propiedades desde el HTML renderizado"""
        self.logger.info(f"📄 Parseando listado: {response.url}")
        
        # Rentola usa SSR (Server-Side Rendering) con Next.js
        # Los datos están renderizados directamente en el HTML
        
        # Los links tienen el patrón /listings/...
        property_links = response.css('a[href*="/listings/"]::attr(href)').getall()
        
        # Deduplicar y contar
        property_links = list(set(property_links))
        self.logger.info(f"✅ Encontrados {len(property_links)} links de propiedades (con filtros aplicados: 2 amb, $400k-800k, con patio)")
        
        # Seguir cada link para extraer los datos detallados
        for link in property_links:  # Procesar todos los links encontrados
            full_url = response.urljoin(link)
            yield scrapy.Request(
                full_url,
                callback=self.parse_property,
                meta={
                    'selenium': True,
                    'wait_for': 'body',
                    'wait_time': 10,
                },
                dont_filter=True
            )
        
        # Paginación
        next_page = response.css('a.pagination-next::attr(href), a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(
                next_page, 
                callback=self.parse_listing,
                meta={
                    'selenium': True,
                    'wait_for': 'body',
                    'wait_time': 15,
                    'scroll': True,
                    'scroll_multiple': True,
                }
            )
    
    def parse_property(self, response):
        """Parsea los datos de una propiedad individual"""
        self.logger.info(f"🏠 Parseando propiedad: {response.url}")
        
        item = PropiedadItem()
        
        try:
            # Título - puede estar en h1 o en meta tags
            titulo = response.css('h1::text').get()
            if not titulo:
                titulo = response.css('meta[property="og:title"]::attr(content)').get()
            
            # Dirección - buscar en diferentes lugares
            direccion = response.css('div.address::text, span.address::text, p.address::text').get()
            if not direccion:
                # Buscar en breadcrumbs o meta
                direccion = response.css('meta[property="og:locality"]::attr(content)').get()
            if not direccion:
                direccion = "Rosario"
            
            # Precio - buscar números con $ o ARS
            precio_text = response.css('span.price::text, div.price::text, strong.price::text').get()
            if not precio_text:
                # Buscar en cualquier elemento que tenga números con $
                precio_text = response.css('*:contains("$")::text').re_first(r'\$?\s*([\d.,]+)')
            
            precio = None
            if precio_text:
                # Limpiar y convertir
                precio_clean = re.sub(r'[^\d.,]', '', precio_text)
                precio_clean = precio_clean.replace('.', '').replace(',', '.')
                try:
                    precio = float(precio_clean)
                except:
                    pass
            
            # Superficie
            superficie_text = response.css('*:contains("m²")::text, *:contains("m2")::text').re_first(r'([\d.,]+)\s*m[²2]')
            superficie = None
            if superficie_text:
                try:
                    superficie = float(superficie_text.replace(',', '.'))
                except:
                    pass
            
            # Dormitorios
            dormitorios_text = response.css('*:contains("dormitorio")::text, *:contains("habitación")::text').re_first(r'(\d+)\s*(?:dormitorio|habitación)')
            dormitorios = None
            if dormitorios_text:
                try:
                    dormitorios = int(dormitorios_text)
                except:
                    pass
            
            # Baños
            banos_text = response.css('*:contains("baño")::text').re_first(r'(\d+)\s*baño')
            banos = None
            if banos_text:
                try:
                    banos = int(banos_text)
                except:
                    pass
            
            # URL actual
            url = response.url
            
            # Detectar patio en todo el contenido de la página
            # Buscar en título, dirección, y todo el texto de la página
            texto_completo = f"{titulo} {direccion} {response.text}".lower()
            patio = any(word in texto_completo for word in ['patio', 'jardín', 'jardin', 'quincho', 'parrilla', 'terraza', 'balcón', 'balcon'])
            
            # Detectar mascotas
            mascotas = any(word in texto_completo for word in ['mascota', 'pet', 'perro', 'gato', 'acepta mascota', 'permite mascota'])
            
            # Extraer barrio
            barrio = self._extraer_barrio(direccion) if direccion else None
            
            # Llenar el item
            item['titulo'] = titulo or 'Propiedad en alquiler'
            item['direccion'] = direccion
            item['precio'] = precio
            item['moneda'] = 'ARS'
            item['ambientes'] = dormitorios
            item['dormitorios'] = dormitorios
            item['banos'] = banos
            item['superficie_total'] = superficie
            item['ciudad'] = 'Rosario'
            item['barrio'] = barrio
            item['fuente'] = 'rentola'
            item['url'] = url
            item['patio'] = patio
            item['mascotas'] = mascotas
            item['fecha_scraping'] = datetime.now().isoformat()
            
            self.logger.info(f"✅ Extraída: {titulo}")
            yield item
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error procesando propiedad: {e}")
            return
    
    def _extraer_precio(self, texto):
        """Extrae el precio del texto"""
        if not texto:
            return None
        
        texto = str(texto).replace('.', '').replace(',', '')
        match = re.search(r'\$?\s*(\d+)', texto)
        if match:
            try:
                return float(match.group(1))
            except:
                return None
        return None
    
    def _extraer_numero(self, textos, patron):
        """Extrae un número usando un patrón regex"""
        if not textos:
            return None
        
        texto = ' '.join(str(t) for t in textos if t)
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def _extraer_barrio(self, texto):
        """Extrae el barrio del texto"""
        barrios_rosario = [
            'Centro', 'Distrito Centro', 'Abasto', 'Alberdi', 'Fisherton',
            'Echesortu', 'Pichincha', 'Luis Agote', 'República de la Sexta',
            'Martín', 'Puerto Norte', 'Distrito Norte', 'Distrito Sur',
            'Distrito Noroeste', 'Refinería', 'La Florida', 'Godoy',
            'Lisandro de la Torre', 'Triángulo Moderno', 'Sarmiento'
        ]
        
        texto_lower = texto.lower()
        for barrio in barrios_rosario:
            if barrio.lower() in texto_lower:
                return barrio
        
        return None
