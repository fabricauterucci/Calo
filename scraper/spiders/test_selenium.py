"""
🔧 Spider de PRUEBA para verificar que Selenium funciona correctamente
"""
import scrapy


class TestSeleniumSpider(scrapy.Spider):
    """
    Spider de prueba para verificar Selenium.
    
    Ejecutar con:
        scrapy crawl test_selenium
    """
    name = 'test_selenium'
    
    custom_settings = {
        'SELENIUM_ENABLED': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.SeleniumMiddleware': 800,
        },
        'ITEM_PIPELINES': {},  # Desactivar pipelines para prueba
    }
    
    def start_requests(self):
        # Probar con una página simple
        test_url = 'https://www.example.com'
        
        yield scrapy.Request(
            test_url,
            callback=self.parse_test,
            meta={
                'selenium': True,
                'wait_time': 2
            }
        )
    
    def parse_test(self, response):
        """Verificar que Selenium funciona"""
        self.logger.info("=" * 60)
        self.logger.info("✅ Selenium está FUNCIONANDO")
        self.logger.info(f"📄 URL: {response.url}")
        self.logger.info(f"📏 HTML length: {len(response.text)}")
        self.logger.info(f"🏷️  Title: {response.css('title::text').get()}")
        self.logger.info("=" * 60)
        
        yield {
            'url': response.url,
            'title': response.css('title::text').get(),
            'status': 'OK'
        }
