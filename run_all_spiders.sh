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

spiders=("zonaprop" "argenprop" "remax" "mapropiedades" "lacapital" "bienesrosario")

for spider in "${spiders[@]}"; do
    echo "▶ Ejecutando spider: $spider"
    scrapy crawl "$spider" -L INFO
    echo ""
    echo "✓ Completado: $spider"
    echo "---"
    sleep 2
done

echo ""
echo "✅ Scraping completado para todas las fuentes"
echo ""
echo "Para ver los resultados:"
echo "  cd api && uvicorn main:app --reload"
