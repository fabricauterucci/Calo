#!/bin/bash

# Script para scrapear de todas las fuentes optimizadas
# Uso: ./scrapear_todas_fuentes.sh [LIMITE]

LIMITE=${1:-20}  # Default: 20 propiedades por fuente

echo "🚀 Iniciando scraping de todas las fuentes..."
echo "📊 Límite por fuente: $LIMITE propiedades"
echo ""

source venv/bin/activate

# Array de spiders optimizados (solo los más confiables)
SPIDERS=(
    "zonaprop_simple"
    # Otros spiders comentados temporalmente por problemas de carga
    # "argenprop_simple"
    # "remax_simple"
    # "mapropiedades_simple"
    # "lacapital_simple"
    # "bienesrosario_simple"
)

# Contador de éxitos
EXITOSOS=0
FALLIDOS=0

for spider in "${SPIDERS[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🕷️  Scrapeando: $spider"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if scrapy crawl "$spider" -s CLOSESPIDER_ITEMCOUNT=$LIMITE 2>&1 | tail -20; then
        EXITOSOS=$((EXITOSOS + 1))
        echo "✅ $spider completado"
    else
        FALLIDOS=$((FALLIDOS + 1))
        echo "❌ $spider falló"
    fi
    
    echo ""
    sleep 2  # Pequeña pausa entre spiders
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 RESUMEN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Spiders exitosos: $EXITOSOS"
echo "❌ Spiders fallidos: $FALLIDOS"
echo ""

# Mostrar estadísticas de la base de datos
echo "📈 Estadísticas de la base de datos:"
sqlite3 propiedades.db << EOF
SELECT 
    fuente,
    COUNT(*) as cantidad,
    ROUND(AVG(precio), 0) as precio_promedio
FROM propiedades 
GROUP BY fuente
ORDER BY cantidad DESC;
EOF

echo ""
echo "🎉 Scraping completado!"
