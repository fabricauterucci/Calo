import scrapy
import httpx
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
from scraper.items import PropiedadItem
import re


class RentolaAsyncSpider(scrapy.Spider):
    """
    Spider asíncrono para Rentola.ar - mucho más rápido que con Selenium
    """
    name = 'rentola_async'
    allowed_domains = ['rentola.ar']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 0.5,  # Más rápido que Selenium
        'CONCURRENT_REQUESTS': 16,
        'SELENIUM_ENABLED': False,  # No necesitamos Selenium
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    def start_requests(self):
        # URL con filtros: casas y deptos, 2 ambientes, $400k-800k, con patio
        base_url = 'https://rentola.ar/alquiler?location=rosario&property_types=house&property_types=apartment&rent=400000-800000&rooms=2&facility=with_patio'
        
        # Scrapy maneja la primera página normalmente
        yield scrapy.Request(
            base_url,
            callback=self.parse,
            dont_filter=True
        )
    
    def parse(self, response):
        """Parsea el listado y extrae links de propiedades"""
        self.logger.info(f"📄 Parseando listado: {response.url}")
        
        # Extraer links de propiedades
        property_links = response.css('a[href*="/listings/"]::attr(href)').getall()
        property_links = list(set(property_links))  # Deduplicar
        
        self.logger.info(f"✅ Encontrados {len(property_links)} links (filtros: 2 amb, $400k-800k, con patio)")
        
        # Usar httpx asíncrono para scrapear todas las propiedades en paralelo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self.fetch_all_properties(property_links))
        loop.close()
        
        # Yield los items extraídos
        for item in results:
            if item:
                yield item
        
        # Paginación (si existe)
        next_page = response.css('a[rel="next"]::attr(href), a.pagination-next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
    
    async def fetch_all_properties(self, property_links):
        """Fetcha todas las propiedades en paralelo usando httpx asíncrono"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = [
                self.fetch_property(client, f"https://rentola.ar{link}") 
                for link in property_links
            ]
            # Procesar 10 propiedades a la vez para no sobrecargar el servidor
            results = []
            for i in range(0, len(tasks), 10):
                batch = tasks[i:i+10]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                results.extend(batch_results)
                await asyncio.sleep(0.5)  # Pausa entre batches
            
            return [r for r in results if not isinstance(r, Exception) and r is not None]
    
    async def fetch_property(self, client: httpx.AsyncClient, url: str):
        """Fetcha y parsea una propiedad individual"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = await client.get(url, headers=headers, follow_redirects=True)
            
            if response.status_code != 200:
                self.logger.warning(f"⚠️ Error {response.status_code} en {url}")
                return None
            
            # Parsear con BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer datos
            item = PropiedadItem()
            
            # Título
            h1 = soup.find('h1')
            titulo = h1.get_text(strip=True) if h1 else None
            if not titulo:
                meta_title = soup.find('meta', property='og:title')
                titulo = meta_title['content'] if meta_title else None
            
            # Precio - buscar en el texto
            precio = None
            precio_patterns = [
                r'\$\s*([\d.,]+)',
                r'ARS\s*([\d.,]+)',
                r'(\d{6,})\s*ARS',
            ]
            for pattern in precio_patterns:
                match = re.search(pattern, response.text)
                if match:
                    try:
                        precio_str = match.group(1).replace('.', '').replace(',', '.')
                        precio = float(precio_str)
                        break
                    except:
                        continue
            
            # Superficie
            superficie = None
            superficie_match = re.search(r'(\d+(?:[.,]\d+)?)\s*m[²2]', response.text, re.IGNORECASE)
            if superficie_match:
                try:
                    superficie = float(superficie_match.group(1).replace(',', '.'))
                except:
                    pass
            
            # Dormitorios
            dormitorios = None
            dormitorios_match = re.search(r'(\d+)\s*(?:dormitorio|habitación|habitacion)', response.text, re.IGNORECASE)
            if dormitorios_match:
                try:
                    dormitorios = int(dormitorios_match.group(1))
                except:
                    pass
            
            # Baños
            banos = None
            banos_match = re.search(r'(\d+)\s*baño', response.text, re.IGNORECASE)
            if banos_match:
                try:
                    banos = int(banos_match.group(1))
                except:
                    pass
            
            # Dirección
            direccion = "Rosario"
            address_meta = soup.find('meta', property='og:locality')
            if address_meta:
                direccion = address_meta.get('content', 'Rosario')
            
            # Detectar patio
            texto_completo = f"{titulo} {response.text}".lower()
            patio = any(word in texto_completo for word in [
                'patio', 'jardín', 'jardin', 'quincho', 
                'parrilla', 'terraza', 'balcón', 'balcon'
            ])
            
            # Extraer barrio
            barrio = self._extraer_barrio(direccion)
            
            # Llenar item
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
            item['fecha_scraping'] = datetime.now().isoformat()
            
            self.logger.info(f"✅ Extraída: {titulo}")
            return item
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error procesando {url}: {e}")
            return None
    
    def _extraer_barrio(self, texto):
        """Extrae el barrio del texto"""
        barrios_rosario = [
            'Centro', 'Distrito Centro', 'Abasto', 'Alberdi', 'Fisherton',
            'Echesortu', 'Pichincha', 'Luis Agote', 'República de la Sexta',
            'Martín', 'Puerto Norte', 'Distrito Norte', 'Distrito Sur',
            'Distrito Noroeste', 'Refinería', 'La Florida', 'Godoy',
            'Lisandro de la Torre', 'Triángulo Moderno', 'Sarmiento',
            'Bella Vista', 'Parque Casado', 'Barrio Industrial',
        ]
        
        texto_lower = texto.lower()
        for barrio in barrios_rosario:
            if barrio.lower() in texto_lower:
                return barrio
        
        return None
