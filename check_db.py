import sqlite3
import re
import os
import sys

# Definición de límites (copiado de pipelines.py para consistencia inmediata)
BARRIOS_VALIDOS = {
	"centro", "abasto", "echesortu", "echeosortu", "españa y hospitales", 
    "barrio parque", "agote", "luis agote", "bella vista"
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

def es_zona_valida(direccion, barrio):
    # Check barrio first if present (STRICT FILTER)
    if barrio:
        b_norm = normalizar_calle(barrio).lower()
        if b_norm not in BARRIOS_VALIDOS:
             return False, f"Barrio no permitido: {barrio}"

    if not direccion or len(direccion) < 5:
        return False, "Sin dirección válida"

    calle, altura = extraer_calle_altura(direccion)
    
    if not calle or not altura:
        return False, "No se pudo extraer calle y altura"
        
    calle_n = normalizar_calle(calle)

    # --- FILTRO ZONA PELIGROSA (VILLA) ---
    zona_latas_ns = {"corrientes", "paraguay", "presidente roca", "pte roca", "españa"}
    if calle_n in zona_latas_ns:
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
    return False, f"Calle no permitida: {calle}"

def limpiar_db():
    print("Conectando a BD...")
    conn = sqlite3.connect('propiedades.db')
    cursor = conn.cursor()
    
    # Get all properties
    cursor.execute("SELECT id, direccion, barrio, titulo, tipo FROM propiedades")
    props = cursor.fetchall()
    
    eliminados = 0
    total = len(props)
    
    print(f"Analizando {total} propiedades...")
    
    ids_to_delete = []
    
    for pid, direccion, barrio, titulo, tipo in props:
        # --- FILTRO POR TIPO ---
        t = (tipo or "").lower().strip()
        if 'departamento' in t or 'monoambiente' in t:
             print(f"❌ Eliminando ID {pid}: {direccion} (Tipo no permitido: {t})")
             ids_to_delete.append(pid)
             eliminados += 1
             continue
        if t and t not in {'casa', 'ph'}:
             print(f"❌ Eliminando ID {pid}: {direccion} (Tipo no permitido: {t})")
             ids_to_delete.append(pid)
             eliminados += 1
             continue
        
        # Use direccion or try to extract from title if direccion is poor
        dir_to_check = direccion
        if not dir_to_check or len(dir_to_check) < 5:
            # Try finding address in title
            dir_to_check = titulo 
            
        es_valida, razon = es_zona_valida(dir_to_check, barrio)
        
        if not es_valida:
            print(f"❌ Eliminando ID {pid}: {dir_to_check} ({razon})")
            ids_to_delete.append(pid)
            eliminados += 1
            
    if ids_to_delete:
        placeholders = ','.join(['?'] * len(ids_to_delete))
        cursor.execute(f"DELETE FROM propiedades WHERE id IN ({placeholders})", ids_to_delete)
        conn.commit()
        
    print(f"\nResumen:")
    print(f"Total analizado: {total}")
    print(f"Eliminados: {eliminados}")
    print(f"Restantes: {total - eliminados}")
    
    conn.close()

if __name__ == "__main__":
    limpiar_db()
