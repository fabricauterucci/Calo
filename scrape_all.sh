#!/bin/bash
# Script para ejecutar todos los spiders optimizados

echo "🏠 Iniciando scraping desde todas las fuentes"
echo "=============================================="

# Activar entorno virtual
source venv/bin/activate

# Limpiar base de datos (opcional - comentar si no quieres borrar datos)
# sqlite3 propiedades.db "DELETE FROM propiedades;"

# Spiders optimizados con límite de 30 propiedades cada uno
SPIDERS=(
    "zonaprop_simple"
    "argenprop_simple"
    "remax_simple"
    "mapropiedades_simple"
    "lacapital_simple"
    "bienesrosario_simple"
)

# Contador
TOTAL_SPIDERS=${#SPIDERS[@]}
CURRENT=0

for spider in "${SPIDERS[@]}"; do
    CURRENT=$((CURRENT + 1))
    echo ""
    echo "[$CURRENT/$TOTAL_SPIDERS] 🕷️  Ejecutando spider: $spider"
    echo "---------------------------------------------"
    
    scrapy crawl "$spider" -s CLOSESPIDER_ITEMCOUNT=30 2>&1 | grep -E "INFO|ERROR|Extraída|items scraped"
    
    if [ $? -eq 0 ]; then
        echo "✅ $spider completado"
    else
        echo "⚠️  $spider tuvo errores (puede que no haya encontrado propiedades)"
    fi
done

echo ""
echo "=============================================="
echo "✅ Scraping completado desde todas las fuentes"
echo ""
echo "📊 Estadísticas:"
sqlite3 propiedades.db << EOF
SELECT 
    fuente,
    COUNT(*) as cantidad,
    AVG(CASE WHEN precio > 0 THEN precio END) as precio_promedio
FROM propiedades 
GROUP BY fuente
ORDER BY cantidad DESC;
EOF

echo ""
echo "📈 Total de propiedades en la base de datos:"
sqlite3 propiedades.db "SELECT COUNT(*) FROM propiedades;"
