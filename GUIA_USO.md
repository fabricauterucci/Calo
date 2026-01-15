# Guía de Uso Rápido

## 1. Instalación

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate  # En Windows

# Instalar dependencias
pip install -r requirements.txt
```

## 2. Ejecutar Scraping

**IMPORTANTE**: Asegúrate de tener el entorno virtual activado:
```bash
source venv/bin/activate
```

### Scraping individual por sitio:
```bash
scrapy crawl zonaprop
scrapy crawl argenprop
scrapy crawl remax
scrapy crawl mapropiedades
scrapy crawl lacapital
scrapy crawl bienesrosario
```

### Scraping de todos los sitios:
```bash
chmod +x run_all_spiders.sh
./run_all_spiders.sh
```

## 3. Iniciar la API

```bash
# Con el entorno virtual activado
source venv/bin/activate
cd api
uvicorn main:app --reload
```

La API estará disponible en: http://localhost:8000

Documentación interactiva: http://localhost:8000/docs

## 4. Usar el Frontend

Abrir en navegador:
```bash
cd frontend
python -m http.server 8080
```

Luego visitar: http://localhost:8080

O simplemente abrir `frontend/index.html` en tu navegador.

## 5. Endpoints de la API

- `GET /propiedades` - Lista propiedades con filtros
- `GET /propiedades/{id}` - Detalle de una propiedad
- `GET /stats` - Estadísticas generales
- `GET /barrios` - Lista de barrios disponibles
- `GET /fuentes` - Lista de fuentes
- `GET /buscar?q=centro` - Búsqueda de texto libre

### Ejemplos de filtros:

```bash
# Departamentos entre $80k y $150k
curl "http://localhost:8000/propiedades?precio_min=80000&precio_max=150000"

# 2 ambientes en Centro que acepten mascotas
curl "http://localhost:8000/propiedades?ambientes=2&barrio=Centro&mascotas=true"

# Más de 60m² con al menos 2 dormitorios
curl "http://localhost:8000/propiedades?superficie_min=60&dormitorios_min=2"
```

## 6. Base de Datos

Por defecto usa SQLite (`propiedades.db`).

Para usar PostgreSQL:
1. Crear base de datos:
```sql
CREATE DATABASE propiedades;
```

2. Configurar en `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/propiedades
```

## 7. Configuración de Scraping

Editar `scraper/settings.py`:

- `DOWNLOAD_DELAY`: Delay entre requests (default: 2 segundos)
- `CONCURRENT_REQUESTS`: Requests simultáneos (default: 16)
- `ROBOTSTXT_OBEY`: Respetar robots.txt (default: False)

## 8. Notas Importantes

⚠️ **Los selectores CSS pueden cambiar**: Los sitios web actualizan su estructura. Si un spider deja de funcionar, hay que actualizar los selectores en el archivo del spider correspondiente.

⚠️ **Rate limiting**: El scraping tiene delays configurados para no sobrecargar los sitios. Ajustar `DOWNLOAD_DELAY` según necesidad.

⚠️ **Selenium**: Solo usar si el contenido carga dinámicamente con JavaScript. Para estos sitios, HTML directo debería funcionar.

## 9. Agregar Nuevo Sitio

1. Crear spider en `scraper/spiders/nombreitio.py`
2. Usar como plantilla los spiders existentes
3. Implementar `parse_listing` y `parse_propiedad`
4. Ejecutar: `scrapy crawl nombredio`

## 10. Troubleshooting

**Error: externally-managed-environment**:
```bash
# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Error de módulo no encontrado**:
```bash
# Verificar que el entorno virtual esté activado
source venv/bin/activate
pip install -r requirements.txt
```

**Entorno virtual no activo**:
Deberías ver `(venv)` al inicio de tu prompt. Si no:
```bash
source venv/bin/activate
```

**API no conecta**:
- Verificar que la API esté corriendo en puerto 8000
- Cambiar `API_URL` en `frontend/app.js` si es necesario

**Sin datos en frontend**:
- Primero ejecutar el scraping
- Luego iniciar la API
- Finalmente abrir el frontend
