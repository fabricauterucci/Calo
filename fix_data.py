import sqlite3
import re

def extract_number(text):
    if not text:
        return None
    if isinstance(text, (int, float)):
        return text
    # Quitar símbolos de moneda, puntos de miles y espacios
    t = str(text).replace('$', '').replace('.', '').replace(' ', '')
    match = re.search(r'(\d+)', t)
    if match:
         return match.group(1)
    return None

def limpiar_db():
    conn = sqlite3.connect('propiedades.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, precio, ambientes, dormitorios, banos, superficie_total, titulo, direccion FROM propiedades")
    rows = cursor.fetchall()
    
    for row in rows:
        pid, precio, ambientes, dormitorios, banos, superficie, titulo, direccion = row
        
        updates = {}
        
        # Limpiar precio
        if isinstance(precio, str):
            num = extract_number(precio)
            updates['precio'] = float(num) if num else 0.0
            
        # Limpiar ambientes
        if isinstance(ambientes, str):
            num = extract_number(ambientes)
            updates['ambientes'] = int(num) if num else 0
            
        # Limpiar dormitorios
        if isinstance(dormitorios, str):
            num = extract_number(dormitorios)
            if num:
                updates['dormitorios'] = int(num)
            else:
                if 'dormitorio' in dormitorios.lower():
                    updates['dormitorios'] = 1
                else:
                    updates['dormitorios'] = 0
                    
        # Limpiar banos
        if isinstance(banos, str):
            num = extract_number(banos)
            if num:
                updates['banos'] = int(num)
            else:
                if 'baño' in banos.lower():
                    updates['banos'] = 1
                else:
                    updates['banos'] = 0

        # Limpiar superficie
        if isinstance(superficie, str):
            num = extract_number(superficie)
            updates['superficie_total'] = float(num) if num else 0.0

        # Limpiar texto
        new_titulo = re.sub(r'\s+', ' ', titulo).strip()
        if new_titulo != titulo:
            updates['titulo'] = new_titulo
            
        new_direccion = re.sub(r'\s+', ' ', direccion).strip()
        if new_direccion != direccion:
            updates['direccion'] = new_direccion

        if updates:
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            params = list(updates.values()) + [pid]
            cursor.execute(f"UPDATE propiedades SET {set_clause} WHERE id = ?", params)
            print(f"ID {pid} actualizado: {updates}")

    conn.commit()
    conn.close()
    print("Limpieza de base de datos completada.")

if __name__ == "__main__":
    limpiar_db()
