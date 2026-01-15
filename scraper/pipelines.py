import re
from datetime import datetime
from itemadapter import ItemAdapter
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Propiedad(Base):
    """Modelo de base de datos para propiedades"""
    __tablename__ = 'propiedades'
    
    id = Column(Integer, primary_key=True)
    
    # Identificación
    fuente = Column(String(50), nullable=False, index=True)
    url = Column(String(500), unique=True, nullable=False)
    id_externo = Column(String(100))
    
    # Básicos
    titulo = Column(String(500))
    descripcion = Column(Text)
    tipo = Column(String(50))
    operacion = Column(String(50))
    
    # Ubicación
    provincia = Column(String(100))
    ciudad = Column(String(100), index=True)
    barrio = Column(String(100), index=True)
    direccion = Column(String(500))
    
    # Características
    precio = Column(Float, index=True)
    moneda = Column(String(10))
    expensas = Column(Float)
    
    ambientes = Column(Integer, index=True)
    dormitorios = Column(Integer)
    banos = Column(Integer)
    cocheras = Column(Integer)
    
    superficie_total = Column(Float, index=True)
    superficie_cubierta = Column(Float)
    
    # Extras
    mascotas = Column(Boolean, default=False, index=True)
    amoblado = Column(Boolean, default=False)
    patio = Column(Boolean, default=False, index=True)
    
    # Imagenes
    imagenes = Column(Text)  # JSON array as string
    imagen_principal = Column(String(500))
    
    # Metadata
    fecha_scraping = Column(DateTime, default=datetime.utcnow)
    fecha_publicacion = Column(DateTime)
    activa = Column(Boolean, default=True)


class NormalizacionPipeline:
    """Pipeline para normalizar datos"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Normalizar precio
        if adapter.get('precio'):
            adapter['precio'] = self._normalizar_precio(adapter['precio'])
        
        # Normalizar superficie
        for campo in ['superficie_total', 'superficie_cubierta']:
            if adapter.get(campo):
                adapter[campo] = self._normalizar_superficie(adapter[campo])
        
        # Normalizar números enteros
        for campo in ['ambientes', 'dormitorios', 'banos', 'cocheras']:
            if adapter.get(campo):
                adapter[campo] = self._normalizar_entero(adapter[campo])
        
        # Normalizar booleanos
        for campo in ['mascotas', 'amoblado', 'patio']:
            if campo in adapter:
                adapter[campo] = self._normalizar_bool(adapter[campo])
        
        # Limpiar texto
        for campo in ['titulo', 'descripcion', 'barrio', 'direccion']:
            if adapter.get(campo):
                adapter[campo] = self._limpiar_texto(adapter[campo])
        
        # Fecha de scraping
        adapter['fecha_scraping'] = datetime.now()
        
        # Defaults
        adapter.setdefault('provincia', 'Santa Fe')
        adapter.setdefault('ciudad', 'Rosario')
        adapter.setdefault('moneda', 'ARS')
        adapter.setdefault('operacion', 'Alquiler')
        adapter.setdefault('tipo', 'Departamento')
        
        return item
    
    def _normalizar_precio(self, precio):
        """Extrae el número del precio"""
        if isinstance(precio, (int, float)):
            return float(precio)
        
        # Remover símbolos y texto
        precio_str = str(precio).replace('$', '').replace('U$S', '').replace('USD', '')
        precio_str = re.sub(r'[^\d,.]', '', precio_str)
        precio_str = precio_str.replace('.', '').replace(',', '.')
        
        try:
            return float(precio_str)
        except (ValueError, AttributeError):
            return None
    
    def _normalizar_superficie(self, superficie):
        """Extrae m² como float"""
        if isinstance(superficie, (int, float)):
            return float(superficie)
        
        match = re.search(r'(\d+(?:[.,]\d+)?)', str(superficie))
        if match:
            return float(match.group(1).replace(',', '.'))
        return None
    
    def _normalizar_entero(self, valor):
        """Extrae entero"""
        if isinstance(valor, int):
            return valor
        
        match = re.search(r'(\d+)', str(valor))
        if match:
            return int(match.group(1))
        return None
    
    def _normalizar_bool(self, valor):
        """Normaliza a booleano"""
        if isinstance(valor, bool):
            return valor
        
        valor_str = str(valor).lower()
        return valor_str in ['true', 'si', 'sí', '1', 'yes', 'permitido', 'acepta']
    
    def _limpiar_texto(self, texto):
        """Limpia espacios y caracteres extraños"""
        if not texto:
            return None
        
        texto = str(texto).strip()
        texto = re.sub(r'\s+', ' ', texto)
        return texto if texto else None


class DatabasePipeline:
    """Pipeline para guardar en base de datos"""
    
    def __init__(self, database_url):
        self.database_url = database_url
        self.engine = None
        self.Session: sessionmaker = None  # type: ignore
    
    @classmethod
    def from_crawler(cls, crawler):
        database_url = crawler.settings.get('DATABASE_URL', 'sqlite:///propiedades.db')
        return cls(database_url)
    
    def open_spider(self, spider):
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.items_vistos = [] # Guardaremos las URLs vistas en esta sesión
    
    def close_spider(self, spider):
        if not self.engine:
            return

        # LOGICA DE DESACTIVACIÓN: 
        # Al terminar el spider, marcamos como inactivas las casas de ESTA FUENTE 
        # que no hayamos visto en este proceso.
        session = self.Session()
        try:
            fuente = spider.name.split('_')[0] # Obtener nombre base (ej: zonaprop)
            
            if self.items_vistos:
                filas_afectadas = session.query(Propiedad).filter(
                    Propiedad.fuente.ilike(f"%{fuente}%"),
                    Propiedad.activa == True,
                    ~Propiedad.url.in_(self.items_vistos)
                ).update({"activa": False}, synchronize_session=False)
                
                session.commit()
                spider.logger.info(f"🔴 Se marcaron {filas_afectadas} propiedades de {fuente} como inactivas (alquiladas/borradas).")
        except Exception as e:
            spider.logger.error(f"Error desactivando items antiguos: {e}")
            session.rollback()
        finally:
            session.close()
            self.engine.dispose()
    
    def process_item(self, item, spider):
        session = self.Session()
        
        try:
            adapter = ItemAdapter(item)
            
            # Buscar si existe
            propiedad = session.query(Propiedad).filter_by(
                url=adapter['url']
            ).first()
            
            if propiedad:
                # Actualizar
                for key, value in adapter.items():
                    if key == 'imagenes' and isinstance(value, list):
                        value = ','.join(value)
                    setattr(propiedad, key, value)
                
                # Asegurarnos de que vuelva a estar activa si reaparece
                propiedad.activa = True
                spider.logger.info(f"Actualizado: {adapter['url']}")
            else:
                # Crear nuevo
                data = dict(adapter)
                if isinstance(data.get('imagenes'), list):
                    data['imagenes'] = ','.join(data['imagenes'])
                
                propiedad = Propiedad(**data)
                session.add(propiedad)
                spider.logger.info(f"Nuevo: {adapter['url']}")
            
            # Registrar URL vista
            self.items_vistos.append(adapter['url'])
            session.commit()
            
        except Exception as e:
            session.rollback()
            spider.logger.error(f"Error guardando item: {e}")
            raise
        
        finally:
            session.close()
        
        return item
