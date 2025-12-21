#!/bin/bash
# Script para ejecutar todos los spiders

echo "🕷️  Iniciando scraping de todas las fuentes..."
echo ""

# Verificar si el entorno virtual está activado
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Entorno virtual no activado. Activando..."
    source venv/bin/activate
fi

cd "$(dirname "$0")"

spiders=("zonaprop_api" "argenprop" "roomix")

for spider in "${spiders[@]}"; do
    echo "▶ Ejecutando spider: $spider"
    # Limitar recursos para reducir carga del CPU
    nice -n 19 scrapy crawl "$spider" -L INFO -s CONCURRENT_REQUESTS=4 -s DOWNLOAD_DELAY=1 -s CONCURRENT_REQUESTS_PER_DOMAIN=2
    echo ""
    echo "✓ Completado: $spider"
    echo "---"
    sleep 3
done

echo ""
echo "✅ Scraping completado para todas las fuentes"
echo ""
echo "Para ver los resultados:"
echo "  cd api && uvicorn main:app --reload"
