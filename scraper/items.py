import scrapy
from scrapy.loader import ItemLoader


class PropiedadItem(scrapy.Item):
    """Item normalizado para todas las propiedades"""
    
    # Identificación
    fuente = scrapy.Field()  # zonaprop, argenprop, remax, etc.
    url = scrapy.Field()
    id_externo = scrapy.Field()  # ID del sitio original
    
    # Básicos
    titulo = scrapy.Field()
    descripcion = scrapy.Field()
    tipo = scrapy.Field()  # departamento, casa, etc.
    operacion = scrapy.Field()  # alquiler, venta
    
    # Ubicación
    provincia = scrapy.Field()
    ciudad = scrapy.Field()
    barrio = scrapy.Field()
    direccion = scrapy.Field()
    latitud = scrapy.Field()  # float
    longitud = scrapy.Field()  # float
    mapa_url = scrapy.Field()  # URL del mapa estático
    
    # Características
    precio = scrapy.Field()  # float normalizado
    moneda = scrapy.Field()  # ARS, USD
    expensas = scrapy.Field()  # float o None
    
    ambientes = scrapy.Field()  # int
    dormitorios = scrapy.Field()  # int
    banos = scrapy.Field()  # int
    cocheras = scrapy.Field()  # int
    
    superficie_total = scrapy.Field()  # m² float
    superficie_cubierta = scrapy.Field()  # m² float
    
    # Extras
    mascotas = scrapy.Field()  # bool
    amoblado = scrapy.Field()  # bool
    patio = scrapy.Field()  # bool
    
    # Imagenes
    imagenes = scrapy.Field()  # list de URLs
    imagen_principal = scrapy.Field()
    
    # Metadata
    fecha_scraping = scrapy.Field()
    fecha_publicacion = scrapy.Field()
    activa = scrapy.Field()
