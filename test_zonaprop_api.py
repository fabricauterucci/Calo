import requests
import json

url = "https://www.zonaprop.com.ar/rplis-api/postings"

headers = {
    'accept': 'application/json',
    'accept-language': 'es-AR,es;q=0.9',
    'content-type': 'application/json',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

payload = {
    "moneda": 1,
    "preciomin": "30000",
    "preciomax": "1000000",
    "tipoDeOperacion": "2",
    "tipoAnunciante": "ALL",
    "sort": "relevance",
    "city": "1004884",
    "pagina": 1,
}

response = requests.post(url, headers=headers, json=payload)
data = response.json()

print("=" * 80)
print("RESPUESTA DE LA API")
print("=" * 80)

if 'listPostings' in data:
    postings = data['listPostings'][:3]  # Primeras 3 propiedades
    
    for i, posting in enumerate(postings, 1):
        print(f"\n{'=' * 80}")
        print(f"PROPIEDAD {i}")
        print(f"{'=' * 80}")
        print(f"ID: {posting.get('postingId')}")
        print(f"Título: {posting.get('title')}")
        print(f"URL: {posting.get('url')}")
        print(f"\n--- TIPO DE PROPIEDAD ---")
        print(f"propertyType: {posting.get('propertyType')}")
        print(f"postingType: {posting.get('postingType')}")
        
        print(f"\n--- OPERACIÓN ---")
        if 'priceOperationTypes' in posting:
            operations = posting['priceOperationTypes']
            for op in operations:
                print(f"  Tipo operación: {op.get('operationType')}")
                print(f"  Precios: {op.get('prices')}")
        
        print(f"\n--- UBICACIÓN ---")
        if 'location' in posting:
            loc = posting['location']
            print(f"  name: {loc.get('name')}")
            print(f"  fullLocation: {loc.get('fullLocation')}")
        
        print(f"\n--- CARACTERÍSTICAS PRINCIPALES ---")
        if 'mainFeatures' in posting:
            main_feat = posting['mainFeatures']
            print(f"  Tipo: {type(main_feat)}")
            if isinstance(main_feat, dict):
                for key, val in list(main_feat.items())[:5]:
                    print(f"  {key}: {val}")
        
        print(f"\n--- TAGS/AMENITIES ---")
        if 'tags' in posting:
            print(f"  tags: {posting['tags']}")
        if 'features' in posting:
            features = posting['features']
            print(f"  features type: {type(features)}")
            if features:
                print(f"  features sample: {list(features.items())[:3] if isinstance(features, dict) else features[:3]}")
