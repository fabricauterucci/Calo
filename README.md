# Scraper de Propiedades - Rosario

Sistema de scraping de propiedades en alquiler de múltiples portales inmobiliarios de Rosario.

## 🏗️ Arquitectura

```
┌───────────────┐
│   Scrapy      │
│ (requests)    │
└───────┬───────┘
        │
┌───────▼───────┐
│ Parsers por   │
│ sitio         │
└───────┬───────┘
        │
┌───────▼───────┐
│ Normalización │
│ precio, m2    │
│ barrio, link  │
└───────┬───────┏
        │
┌───────▼───────┐
│ DB (SQLite)   │
└───────┬───────┘
        │
┌───────▼───────┐
│ FastAPI       │
│ + Frontend    │
└───────────────┘
```

## 📁 Estructura

```
.
├── scraper/              # Proyecto Scrapy
│   ├── spiders/          # Spiders por sitio
│   ├── items.py          # Definición de datos
│   ├── pipelines.py      # Normalización y DB
│   └── settings.py       # Configuración
├── api/                  # FastAPI backend
│   ├── main.py
│   ├── models.py
│   └── database.py
├── frontend/             # Frontend simple
│   ├── index.html
│   └── app.js
└── requirements.txt
```

## 🚀 Instalación

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## 🔧 Uso

### 1. Scraping
```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar spiders
scrapy crawl zonaprop
scrapy crawl argenprop
scrapy crawl remax
scrapy crawl mapropiedades
scrapy crawl lacapital
scrapy crawl bienesrosario
```

O todos juntos:
```bash
./run_all_spiders.sh
```

### 2. API
```bash
# Con entorno virtual activado
source venv/bin/activate
cd api
uvicorn main:app --reload
```

### 3. Frontend
Abrir `frontend/index.html` en navegador o servir con:
```bash
python -m http.server 8000
```

## 🔍 Sitios Scrapeados

- Zonaprop
- Argenprop
- Remax
- MA Propiedades
- La Capital Inmuebles
- Bienes Rosario

## 📊 Filtros Disponibles

- Precio máximo/mínimo
- Barrio
- Ambientes
- Metros cuadrados
- Mascotas permitidas
