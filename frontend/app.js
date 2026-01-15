// Configuración de la API
const API_URL = 'https://calo-q9g8.onrender.com';

let map;
let markers = [];

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    cargarEstadisticas();
    cargarBarrios();
    cargarFuentes();
    buscarPropiedades();
});

// Inicializar Mapa
function initMap() {
    // Centro de Rosario
    map = L.map('map').setView([-32.95, -60.65], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}

// Cargar estadísticas
async function cargarEstadisticas() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();

        document.getElementById('totalProps').textContent = data.total_propiedades || 0;
        document.getElementById('avgPrice').textContent = data.precio_promedio
            ? `$${formatNumber(data.precio_promedio)}`
            : '-';
        document.getElementById('minPrice').textContent = data.precio_min
            ? `$${formatNumber(data.precio_min)}`
            : '-';
        document.getElementById('maxPrice').textContent = data.precio_max
            ? `$${formatNumber(data.precio_max)}`
            : '-';
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

// Cargar barrios en el select
async function cargarBarrios() {
    try {
        const response = await fetch(`${API_URL}/barrios`);
        const barrios = await response.json();

        const select = document.getElementById('barrio');
        barrios.forEach(item => {
            const option = document.createElement('option');
            option.value = item.barrio;
            option.textContent = `${item.barrio} (${item.cantidad})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error cargando barrios:', error);
    }
}

// Cargar fuentes en el select
async function cargarFuentes() {
    try {
        const response = await fetch(`${API_URL}/fuentes`);
        const fuentes = await response.json();

        const select = document.getElementById('fuente');
        fuentes.forEach(item => {
            const option = document.createElement('option');
            option.value = item.fuente;
            option.textContent = `${capitalize(item.fuente)} (${item.cantidad})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error cargando fuentes:', error);
    }
}

// Buscar propiedades
async function buscarPropiedades() {
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');

    loading.style.display = 'block';
    results.innerHTML = '';

    // Limpiar marcadores antiguos
    markers.forEach(m => map.removeLayer(m));
    markers = [];

    // Construir query params
    const params = new URLSearchParams();

    const precioMin = document.getElementById('precioMin').value;
    const precioMax = document.getElementById('precioMax').value;
    const barrio = document.getElementById('barrio').value;
    const ambientes = document.getElementById('ambientes').value;
    const tipoPropiedad = document.getElementById('tipoPropiedad').value;
    const moneda = document.getElementById('moneda').value;
    const dormitorios = document.getElementById('dormitorios').value;
    const superficie = document.getElementById('superficie').value;
    const fuente = document.getElementById('fuente').value;
    const mascotas = document.getElementById('mascotas').checked;
    const patio = document.getElementById('patio').checked;
    const ordenar = document.getElementById('ordenar').value;

    if (precioMin) params.append('precio_min', precioMin);
    if (precioMax) params.append('precio_max', precioMax);
    if (barrio) params.append('barrio', barrio);
    if (ambientes) params.append('ambientes', ambientes);
    if (tipoPropiedad) params.append('tipo', tipoPropiedad);
    if (moneda) params.append('moneda', moneda);
    if (dormitorios) params.append('dormitorios_min', dormitorios);
    if (superficie) params.append('superficie_min', superficie);
    if (fuente) params.append('fuente', fuente);
    if (mascotas) params.append('mascotas', 'true');
    if (patio) params.append('patio', 'true');
    if (ordenar) params.append('ordenar', ordenar);

    params.append('limit', '100');

    try {
        const response = await fetch(`${API_URL}/propiedades?${params}`);
        const propiedades = await response.json();

        loading.style.display = 'none';

        if (propiedades.length === 0) {
            results.innerHTML = `
                <div class="no-results">
                    <div class="no-results-icon">🏠</div>
                    <h3>No se encontraron propiedades</h3>
                    <p>Intenta ajustar los filtros de búsqueda</p>
                </div>
            `;
            return;
        }

        const bounds = [];

        propiedades.forEach(prop => {
            results.appendChild(crearTarjetaPropiedad(prop));

            // Agregar al mapa si tiene coordenadas
            if (prop.latitud && prop.longitud) {
                const marker = L.marker([prop.latitud, prop.longitud])
                    .bindPopup(`
                        <div style="width: 200px;">
                            <img src="${prop.imagen_principal || ''}" style="width: 100%; border-radius: 5px; margin-bottom: 5px;">
                            <strong style="display:block; margin-bottom:5px;">${prop.moneda} ${formatNumber(prop.precio)}</strong>
                            <p style="font-size: 12px; margin-bottom: 5px;">${prop.titulo}</p>
                            <a href="${prop.url}" target="_blank" style="font-size: 11px; color:#667eea;">Ver en ${capitalize(prop.fuente)}</a>
                        </div>
                    `)
                    .addTo(map);
                markers.push(marker);
                bounds.push([prop.latitud, prop.longitud]);
            }
        });

        // Ajustar mapa para ver todos los pines
        if (bounds.length > 0) {
            map.fitBounds(bounds, { padding: [50, 50] });
        }

    } catch (error) {
        loading.style.display = 'none';
        results.innerHTML = `
            <div class="no-results">
                <div class="no-results-icon">⚠️</div>
                <h3>Error al cargar propiedades</h3>
                <p>Verifica que la API esté corriendo en ${API_URL}</p>
            </div>
        `;
        console.error('Error buscando propiedades:', error);
    }
}

// Crear tarjeta de propiedad
function crearTarjetaPropiedad(prop) {
    const card = document.createElement('div');
    card.className = 'property-card';
    card.onclick = () => window.open(prop.url, '_blank');

    const imagenHtml = prop.imagen_principal
        ? `<img src="${prop.imagen_principal}" alt="${prop.titulo || 'Propiedad'}" onerror="this.parentElement.innerHTML='🏠'">`
        : '🏠';

    const precio = prop.precio
        ? `${prop.moneda === 'USD' ? 'USD' : '$'} ${formatNumber(prop.precio)}`
        : 'Consultar';

    const features = [];
    if (prop.ambientes) features.push(`${prop.ambientes} amb`);
    if (prop.dormitorios) features.push(`${prop.dormitorios} dorm`);
    if (prop.banos) features.push(`${prop.banos} baño${prop.banos > 1 ? 's' : ''}`);
    if (prop.superficie_total) features.push(`${Math.round(prop.superficie_total)} m²`);

    const mascotasHtml = prop.mascotas
        ? '<span class="pet-friendly">🐕 Acepta mascotas</span>'
        : '';

    const patioHtml = prop.patio
        ? '<span class="pet-friendly">🌳 Tiene patio</span>'
        : '';

    card.innerHTML = `
        <div class="property-image">${imagenHtml}</div>
        <div class="property-content">
            <span class="property-badge">${prop.tipo || 'Propiedad'}</span>
            <div class="property-title">${prop.titulo || 'Sin título'}</div>
            <div class="property-location">
                📍 ${prop.barrio || 'Sin barrio'}, ${prop.ciudad || 'Rosario'}
            </div>
            <div class="property-price">${precio}</div>
            <div class="property-features">
                ${features.map(f => `<span class="feature">${f}</span>`).join('')}
                ${mascotasHtml}
                ${patioHtml}
            </div>
            <div class="property-footer">
                <span class="source-badge">${capitalize(prop.fuente)}</span>
                <a href="${prop.url}" class="view-link" target="_blank" onclick="event.stopPropagation()">
                    Ver más →
                </a>
            </div>
        </div>
    `;

    return card;
}

// Limpiar filtros
function limpiarFiltros() {
    document.getElementById('precioMin').value = '';
    document.getElementById('precioMax').value = '';
    document.getElementById('barrio').value = '';
    document.getElementById('ambientes').value = '';
    document.getElementById('dormitorios').value = '';
    document.getElementById('superficie').value = '';
    document.getElementById('fuente').value = '';
    document.getElementById('ordenar').value = '';
    document.getElementById('mascotas').checked = false;
    document.getElementById('patio').checked = false;
    buscarPropiedades();
}

// Utilidades
function formatNumber(num) {
    return new Intl.NumberFormat('es-AR').format(Math.round(num));
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Buscar al presionar Enter en los campos
document.querySelectorAll('input, select').forEach(element => {
    element.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            buscarPropiedades();
        }
    });

    // Buscar automáticamente al cambiar selects
    if (element.tagName === 'SELECT') {
        element.addEventListener('change', buscarPropiedades);
    }
});
