#!/bin/bash
# Script optimizado para ejecutar el sistema completo

cd "$(dirname "$0")"

echo "🚀 SISTEMA DE SCRAPING DE PROPIEDADES - ROSARIO"
echo "================================================"
echo ""

# Verificar venv
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment no encontrado"
    echo "   Ejecuta primero: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate

# Menú
echo "Selecciona una opción:"
echo "1) 🕷️  Scrapear propiedades de ZonaProp (optimizado, último mes)"
echo "2) 📊 Ver estadísticas de la base de datos"
echo "3) 🌐 Iniciar API (http://localhost:8000)"
echo "4) 🎨 Iniciar Frontend (http://localhost:8080)"
echo "5) 🚀 Iniciar TODO (API + Frontend)"
echo "6) 🗑️  Limpiar base de datos"
echo ""
read -p "Opción: " opcion

case $opcion in
    1)
        echo ""
        read -p "¿Cuántas propiedades quieres scrapear? (default: 50): " cantidad
        cantidad=${cantidad:-50}
        echo "📡 Scrapeando $cantidad propiedades de ZonaProp..."
        scrapy crawl zonaprop_simple -s CLOSESPIDER_ITEMCOUNT=$cantidad
        echo ""
        echo "✅ Scraping completado!"
        sqlite3 propiedades.db "SELECT COUNT(*) FROM propiedades;" | xargs echo "Total en BD:"
        ;;
    2)
        echo ""
        echo "📊 ESTADÍSTICAS:"
        echo "=================="
        sqlite3 propiedades.db << EOF
.mode column
.headers on
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT fuente) as fuentes,
    COUNT(DISTINCT barrio) as barrios,
    AVG(precio) as precio_promedio,
    MIN(precio) as precio_min,
    MAX(precio) as precio_max
FROM propiedades
WHERE precio > 0;

SELECT '---' as '---';

SELECT fuente, COUNT(*) as cantidad 
FROM propiedades 
GROUP BY fuente;
EOF
        ;;
    3)
        echo ""
        echo "🌐 Iniciando API en http://localhost:8000"
        echo "   Endpoints disponibles:"
        echo "   - GET /stats"
        echo "   - GET /propiedades"
        echo "   - GET /propiedades/{id}"
        echo "   - GET /buscar?q=..."
        echo ""
        echo "Presiona Ctrl+C para detener"
        cd api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    4)
        echo ""
        echo "🎨 Iniciando Frontend en http://localhost:8080"
        echo "   Asegúrate de que la API esté corriendo en el puerto 8000"
        echo ""
        echo "Presiona Ctrl+C para detener"
        cd frontend && python -m http.server 8080
        ;;
    5)
        echo ""
        echo "🚀 Iniciando sistema completo..."
        echo ""
        
        # Iniciar API en background
        cd api && uvicorn main:app --host 0.0.0.0 --port 8000 &
        API_PID=$!
        echo "✅ API iniciada (PID: $API_PID)"
        sleep 2
        
        # Iniciar Frontend
        cd ../frontend && python -m http.server 8080 &
        FRONT_PID=$!
        echo "✅ Frontend iniciado (PID: $FRONT_PID)"
        
        echo ""
        echo "🌐 Sistema listo!"
        echo "   - API: http://localhost:8000"
        echo "   - Frontend: http://localhost:8080"
        echo ""
        echo "Presiona Ctrl+C para detener todo"
        
        # Esperar y limpiar al salir
        trap "kill $API_PID $FRONT_PID 2>/dev/null" EXIT
        wait
        ;;
    6)
        echo ""
        read -p "⚠️  ¿Seguro que quieres eliminar TODAS las propiedades? (s/N): " confirm
        if [ "$confirm" = "s" ] || [ "$confirm" = "S" ]; then
            sqlite3 propiedades.db "DELETE FROM propiedades;"
            echo "✅ Base de datos limpiada"
            sqlite3 propiedades.db "SELECT COUNT(*) FROM propiedades;" | xargs echo "Propiedades restantes:"
        else
            echo "Cancelado"
        fi
        ;;
    *)
        echo "Opción inválida"
        exit 1
        ;;
esac
