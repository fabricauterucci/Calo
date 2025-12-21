import re

BARRIOS_VALIDOS = {
	"centro", "abasto", "echesortu", "echeosortu", "españa y hospitales", 
    "barrio parque", "agote", "luis agote", "bella vista", "distrito centro"
}

CALLES_NORTE_SUR = {
    "castellanos", "buenos aires", "oroño", "balcarce", "moreno", "dorrego", "italia", "españa", 
    "presidente roca", "pte roca", "paraguay", "corrientes", "entre rios", "mitre", "sarmiento", 
    "san martin", "maipu", "laprida", "juan manuel de rosas", "1 de mayo", "alem", "ayacucho", 
    "colon", "necochea", "chacabuco", "pueyrredon", "suipacha", "richieri", "ov lagos", "ovidio lagos",
    "callao", "rodriguez", "pichincha", "vera mujica", "crespo", "iriondo"
}
CALLES_ESTE_OESTE = {
    "santa fe", "segui", "seguí", "pellegrini", "montevideo", "zeballos", "9 de julio", 
    "3 de febrero", "mendoza", "san juan", "san luis", "rioja", "cordoba", "san lorenzo", 
    "urquiza", "tucuman", "catamarca", "salta", "jujuy", "brown", "guemes", "wheelwright", 
    "rivadavia", "velez sarsfield", "junin", "uriburu", "ameghino", "garibaldi"
}

def normalizar_calle(calle):
	if not calle:
		return ""
	# Pasar a minúsculas y quitar acentos
	c = calle.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
	# Quitar prefijos comunes
	c = re.sub(r'^(av\.|av|avenida|bv\.|bv|bulevar|calle|pasaje|pje\.|pje)\s+', '', c)
	return c.strip()

def extraer_calle_altura(direccion):
	if not direccion:
		return None, None
	# Buscar patrón: Calle Altura (ej: Santa Fe 1200)
	m = re.search(r"([A-Za-zÁÉÍÓÚÑáéíóúñ ]+)[ ,]*([0-9]{2,5})", direccion)
	if m:
		calle = m.group(1).strip()
		altura = m.group(2)
		return calle, int(altura)
	# Buscar patrón: Calle al Altura (ej: Santa Fe al 1200)
	m = re.search(r"([A-Za-zÁÉÍÓÚÑáéíóúñ ]+) al ([0-9]{2,5})", direccion)
	if m:
		calle = m.group(1).strip()
		altura = m.group(2)
		return calle, int(altura)
	return direccion.strip(), None

def es_calle_norte_sur(calle):
	return normalizar_calle(calle) in CALLES_NORTE_SUR

def es_calle_este_oeste(calle):
	return normalizar_calle(calle) in CALLES_ESTE_OESTE

from scrapy.exceptions import DropItem

def esta_dentro_del_rectangulo_rosario(direccion, barrio):
    # Check barrio first if present (STRICT FILTER)
    if barrio:
        b_norm = normalizar_calle(barrio).lower()
        if b_norm not in BARRIOS_VALIDOS:
             # Si el barrio es explícito y no está en la lista blanca, lo descartamos.
             # Esto descarta "Distrito Noroeste", "Zona Sur", etc.
             return False, f"Barrio no permitido: {barrio}"
         
    if not direccion or len(direccion) < 5:
        # Si no hay dirección y estamos en modo estricto -> RECHAZAR
        return False, "Sin dirección válida para verificar zona"

    calle, altura = extraer_calle_altura(direccion)

    if not calle or not altura:
        # Si no podemos extraer calle y altura -> RECHAZAR
        return False, "No se pudo extraer calle y altura"

    calle_n = normalizar_calle(calle)

    # --- FILTRO ZONA PELIGROSA (VILLA) ---
    # Calles: Rueda(~2800), Amenabar, Gaboto, Garay, Dean Funes(~3200)
    # Cruzando: Corrientes, Paraguay, Pte Roca, España
    # Rango de altura estimado para las calles N-S en esa zona: 2800 a 3300
    calles_peligrosas_ns = {"corrientes", "paraguay", "presidente roca", "pte roca", "españa", "italia", "dorrego", "moreno", "balcarce"} 
    # Agrego aledañas por seguridad si estan en "Abasto/Hospitales" 
    # (El usuario especificó: Corrientes, Paraguay, Pte Roca, España. Me limitaré a sus explicitas + buffer si necesario)
    
    zona_latas_ns = {"corrientes", "paraguay", "presidente roca", "pte roca", "españa"}
    if calle_n in zona_latas_ns:
        # Altura aprox Rueda(2800) a Dean Funes(3200). Damos un margen.
        if 2750 <= altura <= 3350:
            return False, f"Zona excluida (Villa) - {calle} {altura}"
            
    # --- Límites Norte / Sur ---
    if calle_n == "castellanos":
        if altura < 600:
            return False, "Al norte de Castellanos"
        return True, "OK"

    if calle_n == "buenos aires":
        if altura > 3500:
            return False, "Al sur de Buenos Aires"
        return True, "OK"

    # --- Límites Este / Oeste ---
    if calle_n == "santa fe":
        if altura < 500:
            return False, "Al este de Santa Fe"
        return True, "OK"

    if calle_n in {"segui", "seguí"}:
        if altura > 3900:
            return False, "Al oeste de Seguí"
        return True, "OK"

    # --- Calles internas ---
    if calle_n in CALLES_NORTE_SUR:
        if not (600 <= altura <= 3500):
            return False, f"Fuera de rango N-S ({altura}) para {calle}"
        return True, "OK"

    if calle_n in CALLES_ESTE_OESTE:
        if not (500 <= altura <= 3900):
            return False, f"Fuera de rango E-O ({altura}) para {calle}"
        return True, "OK"

    # --- Desconocida ---
    # Si la calle no está en ninguna de nuestras listas blancas -> RECHAZAR
    return False, f"Calle no permitida: {calle}"

class ZonaPipeline:
    def process_item(self, item, spider):
        # --- FILTRO POR TIPO (CASA/PH) ---
        tipo = item.get('tipo', '').lower().strip()
        # A veces viene sucio, aseguramos match básico
        # Si es departamento o monoambiente, chau
        if 'departamento' in tipo or 'monoambiente' in tipo:
             spider.logger.info(f"❌ Descartado por tipo: {tipo}")
             raise DropItem(f"Tipo no permitido: {tipo}")
        
        # Validar lista blanca estricta si es posible, o lista negra
        # Tipos vistos: "casa", "ph", "departamento", "monoambiente".
        # Si no es casa o ph (y no es vacio?), chau.
        # Asumimos que si no dice casa o ph explícitamente, no nos interesa (terrenos, locales, etc)
        # Ojo: roomix a veces pone cosas raras.
        # Vamos a ser permisivos con vacíos pero restrictivos con "departamento" y "monoambiente"
        if tipo and tipo not in {'casa', 'ph'}:
             spider.logger.info(f"❌ Descartado por tipo: {tipo}")
             raise DropItem(f"Tipo no permitido: {tipo}")

        # Filtrar por barrio primero si es explícito y no válido (Regla de negocio adicional para seguridad)
        barrio = item.get("barrio", "")
        if barrio:
            b_norm = normalizar_calle(barrio).lower()
            if b_norm not in BARRIOS_VALIDOS:
                 spider.logger.info(f"❌ Descartado por barrio: {barrio}")
                 raise DropItem(f"Barrio no permitido: {barrio}")

        ok, razon = esta_dentro_del_rectangulo_rosario(item.get("direccion", ""), item.get("barrio", ""))
        if not ok:
            spider.logger.info(f"❌ Descartado por zona: {item.get('direccion', '')} ({razon})")
            raise DropItem(f"Fuera de zona: {razon}")
        return item


# --- NormalizacionPipeline ---
import re

class NormalizacionPipeline:
    def _extract_number(self, text):
        if not text:
            return None
        # Quitar símbolos de moneda, puntos de miles y espacios
        text = text.replace('$', '').replace('.', '').replace(' ', '')
        # Buscar el primer número (entero o decimal)
        match = re.search(r'(\d+)', text)
        if match:
             return match.group(1)
        return None

    def process_item(self, item, spider):
        # Normalizar precios
        if 'precio' in item and isinstance(item['precio'], str):
            num = self._extract_number(item['precio'])
            if num:
                 try:
                     item['precio'] = float(num)
                 except Exception:
                     item['precio'] = 0.0
            else:
                 item['precio'] = 0.0
                 
        # Normalizar superficies
        for campo in ['superficie_total', 'superficie_cubierta']:
            if campo in item and isinstance(item[campo], str):
                num = self._extract_number(item[campo])
                if num:
                    try:
                        item[campo] = float(num)
                    except Exception:
                        item[campo] = 0.0
                else:
                    item[campo] = 0.0

        # Normalizar ambientes, dormitorios, baños
        for campo in ['ambientes', 'dormitorios', 'banos', 'cocheras']:
            if campo in item and isinstance(item[campo], str):
                num = self._extract_number(item[campo])
                if num:
                    try:
                        item[campo] = int(num)
                    except Exception:
                        item[campo] = 0
                else:
                    # Si no hay número pero hay texto tipo "Dormitorio" o "Baño" sin número, a veces significa 1
                    t = item[campo].lower()
                    if 'dormitorio' in t or 'baño' in t or 'ambiente' in t:
                        item[campo] = 1
                    else:
                        item[campo] = 0
        
        # Normalizar texto (quitar saltos de línea y excesos de Argenprop)
        for campo in ['titulo', 'descripcion', 'barrio', 'direccion', 'ciudad']:
            if campo in item and isinstance(item[campo], str):
                # Limpiar espacios, tabs y saltos de línea múltiples
                item[campo] = re.sub(r'\s+', ' ', item[campo]).strip()
        
        return item

# --- DatabasePipeline ---
import sqlite3
import os
from datetime import datetime

class DatabasePipeline:
	def open_spider(self, spider):
		db_path = os.environ.get('SCRAPER_DB_PATH', 'propiedades.db')
		self.conn = sqlite3.connect(db_path)
		self.cursor = self.conn.cursor()
		self.cursor.execute('''CREATE TABLE IF NOT EXISTS propiedades (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			fuente TEXT,
			url TEXT UNIQUE,
			id_externo TEXT,
			titulo TEXT,
			descripcion TEXT,
			tipo TEXT,
			operacion TEXT,
			provincia TEXT,
			ciudad TEXT,
			barrio TEXT,
			direccion TEXT,
			latitud REAL,
			longitud REAL,
			mapa_url TEXT,
			precio REAL,
			moneda TEXT,
			expensas REAL,
			ambientes INTEGER,
			dormitorios INTEGER,
			banos INTEGER,
			cocheras INTEGER,
			superficie_total REAL,
			superficie_cubierta REAL,
			mascotas BOOLEAN,
			amoblado BOOLEAN,
			patio BOOLEAN,
			imagenes TEXT,
			imagen_principal TEXT,
			fecha_scraping TEXT,
			fecha_publicacion TEXT
		)''')
		self.conn.commit()

	def close_spider(self, spider):
		self.conn.commit()
		self.conn.close()

	def process_item(self, item, spider):
		# Convertir lista de imágenes a string
		imagenes = item.get('imagenes')
		if isinstance(imagenes, list):
			item['imagenes'] = ','.join(imagenes)
		columnas = [
			'fuente','url','id_externo','titulo','descripcion','tipo','operacion','provincia','ciudad','barrio','direccion','latitud','longitud','mapa_url','precio','moneda','expensas','ambientes','dormitorios','banos','cocheras','superficie_total','superficie_cubierta','mascotas','amoblado','patio','imagenes','imagen_principal','fecha_scraping','fecha_publicacion','activa'
		]
		# Asegurar que activa esté en el item o por defecto True
		if 'activa' not in item:
			item['activa'] = True
			
		valores = [item.get(col) for col in columnas]
		placeholders = ','.join(['?'] * len(columnas))
		try:
			self.cursor.execute(f"INSERT OR IGNORE INTO propiedades ({','.join(columnas)}) VALUES ({placeholders})", valores)
			self.conn.commit()
		except Exception as e:
			spider.logger.warning(f"Error guardando en DB: {e}")
		return item
 