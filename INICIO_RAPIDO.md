# 🎯 Guía Rápida: Usar el Scraper

## ✅ Todo listo y funcionando:

- ✅ Entorno virtual creado (`venv/`)
- ✅ Scrapy + BeautifulSoup instalado
- ✅ Selenium + ChromeDriver funcionando
- ✅ FastAPI configurado
- ✅ Base de datos SQLite configurada
- ✅ Frontend listo

---

## 🚀 Uso Rápido

### 1️⃣ Scraping SIN Selenium (más rápido)

```bash
source venv/bin/activate

# Probar con sitios que no bloquean
scrapy crawl argenprop
scrapy crawl remax
scrapy crawl mapropiedades
scrapy crawl lacapital
scrapy crawl bienesrosario
```

### 2️⃣ Scraping CON Selenium (para sitios que bloquean)

```bash
source venv/bin/activate

# ZonaProp con Selenium (evita error 403)
scrapy crawl zonaprop_selenium
```

### 3️⃣ Iniciar API

```bash
# En otra terminal
source venv/bin/activate
cd api
uvicorn main:app --reload
```

Visita: http://localhost:8000/docs

### 4️⃣ Abrir Frontend

```bash
# En otra terminal
cd frontend
python -m http.server 8080
```

Visita: http://localhost:8080

---

## 📊 Ver datos scrapeados

```bash
# Con SQLite Browser (instalar: sudo apt install sqlitebrowser)
sqlitebrowser propiedades.db

# O directamente con sqlite3
sqlite3 propiedades.db "SELECT COUNT(*) FROM propiedades;"
sqlite3 propiedades.db "SELECT titulo, precio, barrio FROM propiedades LIMIT 5;"
```

---

## 🔧 Comandos Útiles

```bash
# Ver estadísticas del scraping
scrapy crawl zonaprop_selenium -L INFO | grep "✅"

# Guardar en JSON además de DB
scrapy crawl argenprop -o salida.json

# Limitar cantidad de páginas
scrapy crawl zonaprop_selenium -s CLOSESPIDER_PAGECOUNT=5

# Ver solo errores
scrapy crawl remax 2>&1 | grep ERROR
```

---

## 🎮 Spiders Disponibles

| Spider | Selenium | Velocidad | Estado |
|--------|----------|-----------|--------|
| `zonaprop` | ❌ | ⚡⚡⚡ | Error 403 |
| `zonaprop_selenium` | ✅ | 🐢 | **Funciona** |
| `argenprop` | ❌ | ⚡⚡⚡ | Probar |
| `remax` | ❌ | ⚡⚡⚡ | Probar |
| `mapropiedades` | ❌ | ⚡⚡⚡ | Probar |
| `lacapital` | ❌ | ⚡⚡⚡ | Probar |
| `bienesrosario` | ❌ | ⚡⚡⚡ | Probar |

---

## 💡 Tips

1. **Empieza con spiders sin Selenium** - Son más rápidos
2. **Si falla (403, sin datos)** - Usa versión `_selenium`
3. **No corras todos a la vez** - Los sitios pueden bloquearte
4. **Scraping gradual**: Haz un sitio a la vez, espera un poco entre cada uno
5. **Revisa los datos**: Algunos selectores pueden necesitar ajustes

---

## 🐛 Problemas comunes

**No aparecen datos en la API/Frontend**:
```bash
# Verifica que hay datos
sqlite3 propiedades.db "SELECT COUNT(*) FROM propiedades;"

# Verifica que la API esté corriendo
curl http://localhost:8000/stats
```

**Selenium falla**:
```bash
# Verifica chromedriver
chromedriver --version
chromium --version

# Deberían ser versiones compatibles
```

**Error de módulos**:
```bash
source venv/bin/activate  # ¡SIEMPRE activar primero!
pip install -r requirements.txt
```

---

## 🎯 Flujo de trabajo recomendado

```bash
# Terminal 1: Scraping
source venv/bin/activate
scrapy crawl zonaprop_selenium  # Tarda ~5-10 min

# Esperar que termine...
# Luego scrapear otros sitios
scrapy crawl argenprop
scrapy crawl remax

# Terminal 2: API (mientras scrapeas)
source venv/bin/activate
cd api
uvicorn main:app --reload

# Terminal 3: Frontend
cd frontend
python -m http.server 8080
```

Ahora puedes ir a http://localhost:8080 y ver las propiedades mientras se scrapean! 🎉
