import requests
import json

# Intentar diferentes códigos de ciudad para encontrar Rosario
# Basado en el patrón V1-C-XXXXXX

url = "https://www.zonaprop.com.ar/rplis-api/postings"

headers = {
    'accept': 'application/json',
    'accept-language': 'es-AR,es;q=0.9',
    'content-type': 'application/json',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# Códigos posibles para Rosario (provincia de Santa Fe)
# Rafaela es 1004884, Rosario probablemente cerca
ciudades_test = {
    "1004856": "Posible Rosario 1",
    "1004880": "Posible Rosario 2", 
    "1004890": "Posible Rosario 3",
    "1004900": "Posible Rosario 4",
}

# Mejor estrategia: buscar sin filtro de ciudad y ver qué locationId tienen las de Rosario
payload = {
    "moneda": 1,
    "preciomin": "200000",
    "preciomax": "500000",
    "tipoDeOperacion": "2",
    "tipoAnunciante": "ALL",
    "sort": "relevance",
    "pagina": 1,
}

print("Buscando propiedades sin filtro de ciudad...")
try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    if response.status_code == 200:
        data = response.json()
        postings = data.get('listPostings', [])[:10]
        
        ciudades_encontradas = {}
        for p in postings:
            loc = p.get('postingLocation', {}).get('location', {})
            ciudad = loc.get('name', '')
            loc_id = loc.get('locationId', '')
            if ciudad:
                if ciudad not in ciudades_encontradas:
                    ciudades_encontradas[ciudad] = loc_id
        
        print("\nCiudades encontradas:")
        for ciudad, loc_id in ciudades_encontradas.items():
            print(f"  {ciudad}: {loc_id}")
            
except Exception as e:
    print(f"Error: {e}")
