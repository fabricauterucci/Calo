from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging


class SeleniumMiddleware:
    """
    Middleware para usar Selenium solo cuando sea necesario.
    
    Para activarlo en un spider específico, agregar en custom_settings:
    
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.SeleniumMiddleware': 800,
        },
        'SELENIUM_ENABLED': True,
    }
    """
    
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self._lock = __import__('threading').Lock()  # Lock para sincronizar requests de Selenium
    
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware
    
    def spider_opened(self, spider):
        """Inicializar Selenium solo si el spider lo necesita"""
        selenium_enabled = spider.settings.getbool('SELENIUM_ENABLED', False)
        
        if selenium_enabled:
            self.logger.info("🚀 Inicializando Selenium para spider: %s", spider.name)
            
            chrome_options = Options()
            
            # Opciones para modo headless (sin ventana)
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # User agent realista
            chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Deshabilitar imágenes para más velocidad
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2,  # 2 = no cargar imágenes
                }
            }
            chrome_options.add_experimental_option('prefs', prefs)
            
            # Evitar detección de automatización
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            try:
                # Configurar chromium
                chrome_options.binary_location = '/usr/bin/chromium'
                
                # Intentar diferentes métodos para obtener chromedriver
                try:
                    # Método 1: Chromedriver del sistema
                    import shutil
                    chromedriver_path = shutil.which('chromedriver')
                    if chromedriver_path:
                        self.logger.info(f"🔧 Usando chromedriver del sistema: {chromedriver_path}")
                        service = Service(chromedriver_path)
                    else:
                        # Método 2: webdriver-manager
                        self.logger.info("📥 Descargando chromedriver compatible...")
                        service = Service(ChromeDriverManager(driver_version="143.0.7499.40").install())
                    
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e1:
                    self.logger.warning(f"⚠️  Intento 1 falló: {e1}")
                    # Método 3: Sin service (último recurso)
                    self.logger.info("🔄 Intentando sin service específico...")
                    self.driver = webdriver.Chrome(options=chrome_options)
                
                self.driver.set_page_load_timeout(30)
                self.logger.info("✅ Selenium iniciado correctamente")
            except Exception as e:
                self.logger.error(f"❌ Error iniciando Selenium: {e}")
                self.logger.error("💡 Instala chromedriver: sudo apt install chromium-chromedriver")
                self.driver = None
    
    def spider_closed(self, spider):
        """Cerrar Selenium al terminar el spider"""
        if self.driver:
            self.logger.info("🛑 Cerrando Selenium")
            self.driver.quit()
    
    def process_request(self, request, spider):
        """
        Procesar request con Selenium si tiene el meta 'selenium'
        
        Uso en spider:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={'selenium': True, 'wait_for': '.listing-card'}
            )
        """
        if not self.driver:
            return None
        
        # Solo usar Selenium si el request lo solicita
        if request.meta.get('selenium'):
            # Usar lock para garantizar que solo un request use Selenium a la vez
            with self._lock:
                self.logger.info(f"🌐 Usando Selenium para: {request.url}")
                
                try:
                    # Agregar delay aleatorio antes de navegar (parecer más humano)
                    import time, random
                    time.sleep(random.uniform(1, 2))
                    
                    # Si es el primer request a clasificado/, aceptar cookies primero
                    if '/clasificado/' in request.url and not hasattr(self, '_cookies_accepted'):
                        # Ir a la página principal primero para establecer cookies
                        self.driver.get('https://www.zonaprop.com.ar/')
                        time.sleep(2)
                        # Intentar aceptar cookies si existe el botón
                        try:
                            accept_button = self.driver.find_element(By.CSS_SELECTOR, 'button[id*="accept"], button[class*="cookie"]')
                            accept_button.click()
                            time.sleep(1)
                        except:
                            pass
                        self._cookies_accepted = True
                    
                    self.driver.get(request.url)
                    
                    # Esperar a que cargue un elemento específico
                    wait_for = request.meta.get('wait_for')
                    if wait_for:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                        )
                    
                    # Espera adicional si se especifica
                    wait_time = request.meta.get('wait_time', 3)  # Aumentado a 3 segundos por defecto
                    time.sleep(wait_time + random.uniform(0, 1))
                    
                    # Scroll para cargar lazy loading (opcional)
                    if request.meta.get('scroll', False):
                        # Scroll múltiple para sitios con lazy loading pesado
                        if request.meta.get('scroll_multiple', False):
                            for i in range(3):
                                self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/3});")
                                time.sleep(2)
                        else:
                            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(1)
                    
                    # Obtener HTML renderizado
                    body = self.driver.page_source.encode('utf-8')
                    
                    # DEBUG: Log what we're actually getting
                    from scrapy.selector import Selector
                    sel = Selector(text=body.decode('utf-8'))
                    h1_texts = sel.css('h1::text').getall()
                    self.logger.debug(f"📄 Selenium requested: {request.url[:80]}")
                    self.logger.debug(f"📄 Selenium current URL: {self.driver.current_url[:80]}")
                    self.logger.debug(f"📄 Selenium response H1s: {h1_texts[:3]}")  # First 3 h1s
                    
                    # Crear respuesta de Scrapy con el HTML de Selenium
                    # Usar request.url en vez de current_url para evitar problemas con redirects
                    return HtmlResponse(
                        url=request.url,  # ← Cambiado!
                        body=body,
                        encoding='utf-8',
                        request=request
                    )
                    
                except Exception as e:
                    self.logger.error(f"❌ Error en Selenium para {request.url}: {e}")
                    return None
        
        return None
