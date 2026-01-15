# 🏠 Sistema de Scraping de Propiedades - Rosario

## ✨ Características Optimizadas

- ✅ **Scraping ultra rápido**: ~2.5 propiedades/segundo (30 en 12 segundos)
- ✅ **Filtro inteligente**: Solo propiedades del último mes
- ✅ **Datos completos**: Título, dirección, precio, ambientes, dormitorios, patio
- ✅ **Sin bloqueos**: Extrae desde listados, no requiere acceso a páginas individuales
- ✅ **API REST**: FastAPI con endpoints para búsqueda y filtrado (incluye filtro de patio)
- ✅ **Frontend responsive**: Interfaz web moderna con búsqueda en tiempo real
- ✅ **Base de datos**: SQLite con normalización automática e índices optimizados
- ✅ **Fuente confiable**: ZonaProp (líder en propiedades de Rosario)

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencias (solo primera vez)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Ejecutar todo con el script optimizado
./run.sh
```

## 📊 Uso del Sistema

### Opción 1: Script Interactivo (Recomendado)
```bash
./run.sh
```

Menú disponible:
1. Scrapear propiedades de ZonaProp
2. Ver estadísticas
3. Iniciar API
4. Iniciar Frontend
5. Iniciar TODO (API + Frontend)
6. Limpiar base de datos

### Opción 2: Comandos Manuales

**Scrapear propiedades:**
```bash
source venv/bin/activate
scrapy crawl zonaprop_simple -s CLOSESPIDER_ITEMCOUNT=50
```

**Iniciar API:**
```bash
cd api
source ../venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Iniciar Frontend:**
```bash
cd frontend
python -m http.server 8080
```

## 📡 Endpoints de la API

- `GET /stats` - Estadísticas generales
- `GET /propiedades` - Listar todas las propiedades
- `GET /propiedades?barrio=Centro&precio_min=400000` - Filtrar
- `GET /propiedades/{id}` - Detalles de una propiedad
- `GET /buscar?q=departamento` - Búsqueda por texto
- `GET /barrios` - Listar barrios disponibles

## 🎯 Ejemplos de Datos Extraídos

```json
{
  "titulo": "Departamento 2 amb 64m² en Distrito Centro, Rosario",
  "direccion": "Distrito Centro, Rosario",
  "precio": 800000.0,
  "moneda": "ARS",
  "ambientes": "2",
  "dormitorios": "2",
  "banos": "1",
  "superficie_total": "64",
  "ciudad": "Rosario",
  "barrio": "Distrito Centro",
  "fuente": "zonaprop"
}
```

## 🔧 Configuración

### Ajustar cantidad de propiedades
```bash
scrapy crawl zonaprop_simple -s CLOSESPIDER_ITEMCOUNT=100
```

### Cambiar delay entre requests
Editar `scraper/settings.py`:
```python
DOWNLOAD_DELAY = 0.5  # segundos entre requests (optimizado)
```

### Ver logs detallados
```bash
scrapy crawl zonaprop_simple --loglevel=DEBUG
```

## 📈 Rendimiento

- **Velocidad**: ~8 propiedades/segundo (optimizado con DOWNLOAD_DELAY=0.5)
- **Sin bloqueos**: Extracción desde listados
- **Filtro de fecha**: Solo propiedades del último mes
- **Memoria**: ~100MB en uso
- **Concurrencia**: Configurable (default: 16 requests simultáneos)

## 🛠️ Spider Principal

| Spider | Fuente | Velocidad | Propiedades | Estado |
|--------|--------|-----------|-------------|--------|
| `zonaprop_simple` | ZonaProp | ⚡ ~2.5 props/seg | 30+ por página | ✅ Optimizado |

**Características del spider:**
- ✅ Filtro automático: solo propiedades del último mes
- ✅ Detección de patio
- ✅ Extracción completa: título, precio, ubicación, características
- ✅ Sin bloqueos: extrae desde listados, no accede a páginas individuales

## 📊 Ejemplo de Estadísticas

```bash
sqlite3 propiedades.db << EOF
SELECT 
    COUNT(*) as total,
    AVG(precio) as precio_promedio,
    COUNT(DISTINCT barrio) as barrios
FROM propiedades WHERE precio > 0;
EOF
```

Resultado típico:
```
total|precio_promedio|barrios
90|485000.0|15
```

**Nota**: ZonaProp es la fuente más completa y confiable para Rosario, con mayor cobertura de barrios y datos actualizados diariamente.

## 🔍 Consultas Útiles

**Propiedades más baratas:**
```bash
sqlite3 propiedades.db "SELECT titulo, precio, barrio FROM propiedades WHERE precio > 0 ORDER BY precio LIMIT 5;"
```

**Barrios con más oferta:**
```bash
sqlite3 propiedades.db "SELECT barrio, COUNT(*) as cant FROM propiedades GROUP BY barrio ORDER BY cant DESC LIMIT 5;"
```

## 🐛 Troubleshooting

**Error: "chromium not found"**
```bash
sudo apt install chromium-browser chromium-chromedriver
```

**Error: "Permission denied" al ejecutar run.sh**
```bash
chmod +x run.sh
```

**Frontend no carga datos**
- Verificar que la API esté corriendo en puerto 8000
- Abrir el frontend con `python -m http.server 8080`, no con `file://`

## 📝 Notas

- Los precios se normalizan automáticamente a números
- Las superficies se extraen en m²
- Los datos se actualizan cada vez que se ejecuta el scraping
- No se eliminan automáticamente las propiedades antiguas (usar opción 6 del menú)
