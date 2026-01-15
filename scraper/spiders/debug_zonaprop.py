"""
Spider de DEBUG para inspeccionar el HTML real de ZonaProp
"""
import scrapy


class DebugZonapropSpider(scrapy.Spider):
    name = 'debug_zonaprop'
    
    custom_settings = {
        'SELENIUM_ENABLED': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.SeleniumMiddleware': 800,
        },
        'ITEM_PIPELINES': {},  # Sin pipelines
    }
    
    def start_requests(self):
        # Una sola propiedad para inspeccionar
        url = 'https://www.zonaprop.com.ar/propiedades/clasificado/alclapin-alquiler-loft-rio-con-cochera-maui-puerto-norte-57583644.html'
        
        yield scrapy.Request(
            url,
            callback=self.parse_debug,
            meta={
                'selenium': True,
                'wait_for': 'h1',
                'wait_time': 3
            }
        )
    
    def parse_debug(self, response):
        """Extraer y mostrar todos los selectores importantes"""
        self.logger.info("=" * 80)
        self.logger.info(f"URL: {response.url}")
        self.logger.info("=" * 80)
        
        # Buscar h1 (título)
        h1_tags = response.css('h1')
        self.logger.info(f"\n📝 H1 tags encontrados: {len(h1_tags)}")
        for i, h1 in enumerate(h1_tags[:3]):
            text = h1.css('::text').get()
            classes = h1.css('::attr(class)').get()
            self.logger.info(f"  H1 #{i+1}: {text}")
            self.logger.info(f"    Clases: {classes}")
        
        # Buscar precios
        self.logger.info(f"\n💰 Buscando precios...")
        precios = response.css('*[class*="price"]::text').getall()[:5]
        for precio in precios:
            if precio.strip():
                self.logger.info(f"  Precio encontrado: {precio.strip()}")
        
        # Buscar ubicación
        self.logger.info(f"\n📍 Buscando ubicación...")
        h2_tags = response.css('h2::text').getall()[:5]
        for h2 in h2_tags:
            if h2.strip():
                self.logger.info(f"  H2: {h2.strip()}")
        
        # Buscar imágenes
        self.logger.info(f"\n🖼️  Buscando imágenes...")
        imgs = response.css('img::attr(src)').getall()[:10]
        data_srcs = response.css('img::attr(data-src)').getall()[:10]
        
        self.logger.info(f"  IMGs con src: {len(imgs)}")
        for img in imgs[:3]:
            if 'http' in img:
                self.logger.info(f"    {img[:100]}")
        
        self.logger.info(f"  IMGs con data-src: {len(data_srcs)}")
        for img in data_srcs[:3]:
            if 'http' in img or img.startswith('//'):
                self.logger.info(f"    {img[:100]}")
        
        # Guardar HTML completo a archivo para inspección manual
        html_file = '/tmp/zonaprop_debug.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        self.logger.info(f"\n💾 HTML guardado en: {html_file}")
        self.logger.info("=" * 80)
        
        yield {
            'url': response.url,
            'h1_count': len(h1_tags),
            'imgs_src': len(imgs),
            'imgs_data_src': len(data_srcs)
        }
