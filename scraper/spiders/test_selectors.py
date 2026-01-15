import scrapy
from scraper.items import PropiedadItem


class TestSelectorsSpider(scrapy.Spider):
    """Spider de prueba para debuggear selectores"""
    name = 'test_selectors'
    
    custom_settings = {
        'SELENIUM_ENABLED': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.SeleniumMiddleware': 800,
        },
    }
    
    def start_requests(self):
        # URL de una propiedad específica
        url = 'https://www.zonaprop.com.ar/propiedades/clasificado/alclapin-alquiler-loft-rio-con-cochera-maui-puerto-norte-57583644.html'
        
        yield scrapy.Request(
            url,
            callback=self.parse,
            meta={
                'selenium': True,
                'wait_for': 'h1',
                'wait_time': 5
            }
        )
    
    def parse(self, response):
        self.logger.info("\n" + "="*80)
        self.logger.info(f"📄 URL: {response.url}")
        self.logger.info("="*80)
        
        # Test título
        self.logger.info("\n🔍 TESTING TITULO:")
        titulo = response.css('h1.title-property::text').get()
        self.logger.info(f"  h1.title-property: {titulo}")
        
        titulo2 = response.css('h1::text').get()
        self.logger.info(f"  h1::text: {titulo2}")
        
        all_h1 = response.css('h1::text').getall()
        self.logger.info(f"  Todos los h1: {all_h1}")
        
        # Test precio
        self.logger.info("\n💰 TESTING PRECIO:")
        precio1 = response.css('div.price-value::text').get()
        self.logger.info(f"  div.price-value: {precio1}")
        
        precio2 = response.css('div[class*="price"]::text').getall()
        self.logger.info(f"  div[class*='price']: {precio2}")
        
        # Test imágenes
        self.logger.info("\n🖼️  TESTING IMAGENES:")
        imgs1 = response.css('img.imageGrid-module__imgProperty___KJ-2G::attr(src)').getall()
        self.logger.info(f"  img.imageGrid-module__imgProperty: {len(imgs1)} imágenes")
        if imgs1:
            self.logger.info(f"    Primera: {imgs1[0]}")
        
        all_imgs = response.css('img::attr(src)').getall()
        self.logger.info(f"  Todas las img: {len(all_imgs)} imágenes")
        
        # Filtrar imágenes de propiedades
        prop_imgs = [img for img in all_imgs if 'zonapropcdn.com/avisos' in img]
        self.logger.info(f"  Imágenes de propiedades (zonapropcdn.com/avisos): {len(prop_imgs)}")
        if prop_imgs:
            self.logger.info(f"    Primera: {prop_imgs[0]}")
        
        # Test ubicación
        self.logger.info("\n📍 TESTING UBICACION:")
        ciudad_meta = response.xpath('//meta[@name="keywords"]/@content').get()
        self.logger.info(f"  Meta keywords: {ciudad_meta}")
        
        json_ld = response.xpath('//script[@type="application/ld+json"]/text()').get()
        if json_ld:
            self.logger.info(f"  JSON-LD encontrado (primeros 200 chars): {json_ld[:200]}")
        
        self.logger.info("\n" + "="*80)
