# 🎯 Guía: Scrapy + Selenium

## ¿Cuándo usar Selenium?

### ✅ USA Selenium SI:
- El precio/datos solo aparecen después de ejecutar JavaScript
- Hay "infinite scroll" o "lazy loading"
- El sitio detecta bots y bloquea requests normales (403, 429)
- Contenido cargado dinámicamente con AJAX

### ❌ NO uses Selenium SI:
- El HTML tiene toda la información (más rápido con requests)
- El sitio tiene API pública
- Puedes hacer scraping con headers mejorados

---

## 📦 Instalación

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar Selenium
pip install -r requirements-selenium.txt
```

---

## 🧪 Probar Selenium

```bash
# Test básico
scrapy crawl test_selenium

# Si funciona, verás:
# ✅ Selenium está FUNCIONANDO
```

---

## 🕷️ Usar Selenium en un Spider

### Opción 1: Spider completo con Selenium

```python
class MiSpider(scrapy.Spider):
    name = 'mi_spider'
    
    custom_settings = {
        'SELENIUM_ENABLED': True,  # ✅ Activar
        'DOWNLOADER_MIDDLEWARES': {
            'scraper.middlewares.SeleniumMiddleware': 800,
        },
    }
    
    def start_requests(self):
        yield scrapy.Request(
            'https://ejemplo.com',
            callback=self.parse,
            meta={
                'selenium': True,  # ✅ Usar Selenium
                'wait_for': '.product-list',  # Selector a esperar
                'wait_time': 3,  # Segundos extra
                'scroll': True  # Scroll para lazy loading
            }
        )
```

### Opción 2: Selenium solo para requests específicos

```python
class MiSpider(scrapy.Spider):
    # ... sin Selenium en custom_settings
    
    def parse(self, response):
        # Request normal (rápido)
        yield scrapy.Request(url1, callback=self.parse_fast)
        
        # Request con Selenium (solo si es necesario)
        yield scrapy.Request(
            url2,
            callback=self.parse_selenium,
            meta={'selenium': True}
        )
```

---

## 🎮 Ejemplos Prácticos

### ZonaProp con Selenium (evita 403)
```bash
scrapy crawl zonaprop_selenium
```

### ZonaProp sin Selenium (más rápido, puede fallar)
```bash
scrapy crawl zonaprop
```

---

## ⚙️ Opciones del middleware

```python
meta={
    'selenium': True,           # Activar Selenium para este request
    'wait_for': '.selector',    # Esperar a que aparezca este elemento
    'wait_time': 3,             # Segundos extra de espera
    'scroll': True,             # Hacer scroll (lazy loading)
}
```

---

## 🚀 Performance

| Método | Velocidad | CPU | Memoria | Cuándo usar |
|--------|-----------|-----|---------|-------------|
| **Requests** | ⚡⚡⚡ | Baja | Baja | HTML estático |
| **Selenium** | 🐢 | Alta | Alta | JS dinámico |

**Tip**: Combina ambos en el mismo spider para máxima eficiencia.

---

## 🛠️ Troubleshooting

### Error: ChromeDriver no encontrado
```bash
pip install webdriver-manager
```

### Error: Chrome no instalado
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install chromium-browser

# O usar Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
```

### Selenium muy lento
```python
custom_settings = {
    'DOWNLOAD_DELAY': 1,  # Reducir delay
    'CONCURRENT_REQUESTS': 1,  # Un solo request a la vez con Selenium
}
```

---

## 📝 Logs

Cuando Selenium está activo verás:
```
🚀 Inicializando Selenium para spider: zonaprop_selenium
✅ Selenium iniciado correctamente
🌐 Usando Selenium para: https://...
🛑 Cerrando Selenium
```

---

## 🎯 Estrategia Recomendada

1. **Intenta primero sin Selenium** (zonaprop, argenprop, etc.)
2. **Si falla (403, sin datos)** → usa versión con Selenium
3. **Prueba selectores en la consola del navegador** antes de scrapear
4. **Combina**: listado con requests, detalles con Selenium si es necesario
