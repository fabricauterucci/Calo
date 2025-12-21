from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

Base = declarative_base()


class Propiedad(Base):
    """Modelo de base de datos"""
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
    latitud = Column(Float)
    longitud = Column(Float)
    mapa_url = Column(String(1000))
    
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
    imagenes = Column(Text)
    imagen_principal = Column(String(500))
    
    # Metadata
    fecha_scraping = Column(DateTime, default=datetime.utcnow)
    fecha_publicacion = Column(DateTime)
    activa = Column(Boolean, default=True)


# Pydantic models para API

class PropiedadResponse(BaseModel):
    """Response schema para propiedades"""
    id: int
    fuente: str
    url: str
    titulo: Optional[str]
    tipo: Optional[str]
    operacion: Optional[str]
    
    precio: Optional[float]
    moneda: Optional[str]
    expensas: Optional[float]
    
    direccion: Optional[str]
    barrio: Optional[str]
    ciudad: Optional[str]
    latitud: Optional[float]
    longitud: Optional[float]
    mapa_url: Optional[str]
    
    ambientes: Optional[int]
    dormitorios: Optional[int]
    banos: Optional[int]
    superficie_total: Optional[float]
    
    mascotas: Optional[bool]
    patio: Optional[bool]
    imagen_principal: Optional[str]
    fecha_scraping: Optional[datetime]
    
    class Config:
        from_attributes = True


class PropiedadDetalle(PropiedadResponse):
    """Response detallado con más campos"""
    descripcion: Optional[str]
    direccion: Optional[str]
    superficie_cubierta: Optional[float]
    cocheras: Optional[int]
    amoblado: Optional[bool]
    imagenes: Optional[str]
    
    class Config:
        from_attributes = True


class FiltrosPropiedades(BaseModel):
    """Filtros para búsqueda"""
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None
    barrio: Optional[str] = None
    ambientes: Optional[int] = None
    dormitorios_min: Optional[int] = None
    superficie_min: Optional[float] = None
    mascotas: Optional[bool] = None
    patio: Optional[bool] = None
    fuente: Optional[str] = None
    tipo: Optional[str] = None
