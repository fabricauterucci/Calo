// Configuración de la API
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://tu-api-en-render.onrender.com'; // CAMBIA ESTO por la URL que te dé Render

// API Key de Geoapify
const GEOAPIFY_API_KEY = 'a4f4d7102b8a40968e725e9f529fbdcd';

// Caché simple para evitar llamadas repetidas
const cache = {
    stats: null,
    barrios: null,
    fuentes: null,
    timestamp: {}
};

const CACHE_TIME = 60000; // 1 minuto

// Paginación
let currentPage = 1;
const ITEMS_PER_PAGE = 30;

// Debounce para evitar múltiples búsquedas
let searchTimeout;
function debouncedBuscar() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage = 1; // Reset page on new search
        buscarPropiedades();
    }, 300);
}

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    cargarEstadisticas();
    cargarBarrios();
    cargarFuentes();
    buscarPropiedades();
});

// Cargar estadísticas
async function cargarEstadisticas() {
    try {
        // Usar caché si existe y es reciente
        if (cache.stats && Date.now() - cache.timestamp.stats < CACHE_TIME) {
            const data = cache.stats;
            document.getElementById('totalProps').textContent = data.total_propiedades || 0;
            document.getElementById('avgPrice').textContent = data.precio_promedio ? `$${formatNumber(data.precio_promedio)}` : '-';
            document.getElementById('minPrice').textContent = data.precio_min ? `$${formatNumber(data.precio_min)}` : '-';
            document.getElementById('maxPrice').textContent = data.precio_max ? `$${formatNumber(data.precio_max)}` : '-';
            return;
        }

        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();
        cache.stats = data;
        cache.timestamp.stats = Date.now();

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

// Cargar barrios predefinidos en el select
async function cargarBarrios() {
    const barriosValidos = [
        'Centro',
        'Abasto',
        'Echesortu',
        'España y Hospitales',
        'Barrio Parque',
        'Barrio Agote',
        'Luis Agote',
        'Bella Vista'
    ];

    const select = document.getElementById('barrio');
    // Limpiar opciones previas excepto la primera
    select.innerHTML = '<option value="">Todos los barrios</option>';

    barriosValidos.forEach(nombre => {
        const option = document.createElement('option');
        option.value = nombre;
        option.textContent = nombre;
        select.appendChild(option);
    });
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

    params.append('limit', ITEMS_PER_PAGE.toString());
    params.append('skip', ((currentPage - 1) * ITEMS_PER_PAGE).toString());

    try {
        const response = await fetch(`${API_URL}/propiedades?${params}`);
        const propiedades = await response.json();

        loading.style.display = 'none';

        if (propiedades.length === 0 && currentPage === 1) {
            results.innerHTML = `
                <div class="no-results">
                    <div class="no-results-icon">🏠</div>
                    <h3>No se encontraron propiedades</h3>
                    <p>Intenta ajustar los filtros de búsqueda</p>
                </div>
            `;
            document.getElementById('pagination').style.display = 'none';
            return;
        }

        // El ordenamiento ya viene de la API
        propiedades.forEach(prop => {
            results.appendChild(crearTarjetaPropiedad(prop));
        });

        // Mostrar/ocultar paginación
        updatePagination(propiedades.length);

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

// Cache de geocodificación
const geocodeCache = new Map();

// IntersectionObserver para lazy loading de mapas
const mapObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const container = entry.target;
            const propData = JSON.parse(container.dataset.prop || '{}');
            cargarMapa(container, propData);
            mapObserver.unobserve(container);
        }
    });
}, { rootMargin: '100px' });

// Cargar mapa con coordenadas
async function cargarMapa(container, prop) {
    const location = prop.direccion || prop.barrio || 'Centro, Rosario';

    // Si ya tiene mapa_url pre-generado, usarlo directamente (¡0 llamadas a API!)
    if (prop.mapa_url) {
        container.innerHTML = `<img 
            src="${prop.mapa_url}" 
            alt="Mapa de ${location}"
            style="opacity: 0; transition: opacity 0.3s"
            onload="this.style.opacity=1"
            onerror="this.innerHTML='<div class=\\'map-placeholder\\'>📍 ${location}</div>'">`;
        return;
    }

    // Fallback: construir URL manualmente si no está pre-generada
    let lat, lon;

    if (prop.latitud && prop.longitud) {
        lat = prop.latitud;
        lon = prop.longitud;
    } else {
        // Último recurso: geocodificar
        const coords = await geocodificarDireccion(prop.direccion, prop.barrio);
        lat = coords.lat;
        lon = coords.lon;
    }

    const mapUrl = `https://maps.geoapify.com/v1/staticmap?style=osm-bright-smooth&width=400&height=220&center=lonlat:${lon},${lat}&zoom=15&marker=lonlat:${lon},${lat};type:material;color:%23ff3b30;size:medium;icon:home&apiKey=${GEOAPIFY_API_KEY}`;

    container.innerHTML = `<img 
        src="${mapUrl}" 
        alt="Mapa de ${location}"
        style="opacity: 0; transition: opacity 0.3s"
        onload="this.style.opacity=1"
        onerror="this.innerHTML='<div class=\\'map-placeholder\\'>📍 ${location}</div>'">`;
}

// Función para geocodificar dirección (solo como fallback)
async function geocodificarDireccion(direccion, barrio) {
    // Limpiar términos confusos
    let limpia = (direccion || '').replace(/(Piso|Dto|Dpto|Unidad|CP|Planta|Penthouse).*$/gi, '').trim();
    const location = limpia || barrio || 'Centro';
    const searchQuery = `${location}, Rosario, Santa Fe, Argentina`;

    // Verificar cache
    if (geocodeCache.has(searchQuery)) {
        return geocodeCache.get(searchQuery);
    }

    try {
        const response = await fetch(`https://api.geoapify.com/v1/geocode/search?text=${encodeURIComponent(searchQuery)}&limit=1&apiKey=${GEOAPIFY_API_KEY}`);
        const data = await response.json();

        if (data.features && data.features.length > 0) {
            const coords = data.features[0].geometry.coordinates;
            const result = { lon: coords[0], lat: coords[1] };
            geocodeCache.set(searchQuery, result);
            return result;
        }
    } catch (error) {
        console.error('Error geocodificando:', error);
    }

    // Fallback a coordenadas del centro de Rosario
    return { lon: -60.6505, lat: -32.9442 };
}

// Crear tarjeta de propiedad
function crearTarjetaPropiedad(prop) {
    const card = document.createElement('div');
    card.className = 'property-card';
    card.onclick = () => window.open(prop.url, '_blank');

    const location = prop.direccion || prop.barrio || 'Centro, Rosario';

    // Crear placeholder para lazy loading
    const imagenContainer = document.createElement('div');
    imagenContainer.className = 'property-image';
    imagenContainer.innerHTML = `<div class="map-placeholder">📍 Cargando mapa...</div>`;
    imagenContainer.dataset.prop = JSON.stringify({
        direccion: prop.direccion,
        barrio: prop.barrio,
        latitud: prop.latitud,
        longitud: prop.longitud,
        mapa_url: prop.mapa_url  // URL pre-generada
    });

    // Observar para lazy loading
    mapObserver.observe(imagenContainer);

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

    // Determinar ubicación a mostrar
    let ubicacion = prop.ciudad || 'Rosario';

    // Verificar si el barrio es solo números o muy corto (probablemente inválido)
    const barrioInvalido = !prop.barrio ||
        /^\d+$/.test(prop.barrio.trim()) ||
        prop.barrio.trim().length < 3;

    if (prop.direccion) {
        // Si hay dirección, siempre usarla (es más específica)
        if (!barrioInvalido && prop.barrio) {
            // Si el barrio es válido, mostrarlo junto con la dirección
            ubicacion = `${prop.direccion}, ${prop.barrio}, ${prop.ciudad || 'Rosario'}`;
        } else {
            // Si no hay barrio válido, solo dirección
            ubicacion = `${prop.direccion}, ${prop.ciudad || 'Rosario'}`;
        }
    } else if (prop.barrio && !barrioInvalido) {
        // Si solo hay barrio válido, mostrarlo
        ubicacion = `${prop.barrio}, ${prop.ciudad || 'Rosario'}`;
    }

    // Construir el HTML de la tarjeta
    card.appendChild(imagenContainer);

    const contentDiv = document.createElement('div');
    contentDiv.className = 'property-content';
    contentDiv.innerHTML = `
        <span class="property-badge">${prop.tipo || 'Propiedad'}</span>
        <div class="property-title">${prop.titulo || 'Sin título'}</div>
        <div class="property-location">
            📍 ${ubicacion}
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
    `;

    card.appendChild(contentDiv);

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
    currentPage = 1;
    buscarPropiedades();
}

// Paginación
function updatePagination(resultCount) {
    const pagination = document.getElementById('pagination');
    const hasMore = resultCount === ITEMS_PER_PAGE;

    if (currentPage === 1 && !hasMore) {
        pagination.style.display = 'none';
        return;
    }

    pagination.style.display = 'flex';
    pagination.innerHTML = `
        <button onclick="previousPage()" ${currentPage === 1 ? 'disabled' : ''}>
            ← Anterior
        </button>
        <span>Página ${currentPage}</span>
        <button onclick="nextPage()" ${!hasMore ? 'disabled' : ''}>
            Siguiente →
        </button>
    `;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        buscarPropiedades();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function nextPage() {
    currentPage++;
    buscarPropiedades();
    window.scrollTo({ top: 0, behavior: 'smooth' });
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
