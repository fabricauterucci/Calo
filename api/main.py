from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import List, Optional
import sys
import os

# Agregar path del scraper
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.database import get_db, engine
from api.models import (
    Propiedad, 
    PropiedadResponse, 
    PropiedadDetalle,
    FiltrosPropiedades,
    Base
)

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Propiedades Rosario",
    description="API para consultar propiedades en alquiler scrapeadas de múltiples portales",
    version="1.0.0"
)

# CORS para permitir frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "mensaje": "API de Propiedades Rosario",
        "version": "1.0.0",
        "endpoints": {
            "propiedades": "/propiedades",
            "detalle": "/propiedades/{id}",
            "stats": "/stats",
            "barrios": "/barrios",
            "fuentes": "/fuentes"
        }
    }


@app.get("/propiedades", response_model=List[PropiedadResponse])
async def listar_propiedades(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de registros"),
    precio_min: Optional[float] = Query(None, description="Precio mínimo"),
    precio_max: Optional[float] = Query(None, description="Precio máximo"),
    barrio: Optional[str] = Query(None, description="Filtrar por barrio"),
    ambientes: Optional[int] = Query(None, ge=1, le=10, description="Cantidad de ambientes"),
    dormitorios_min: Optional[int] = Query(None, ge=0, description="Mínimo de dormitorios"),
    superficie_min: Optional[float] = Query(None, ge=0, description="Superficie mínima en m²"),
    mascotas: Optional[bool] = Query(None, description="Permite mascotas"),
    patio: Optional[bool] = Query(None, description="Tiene patio"),
    fuente: Optional[str] = Query(None, description="Filtrar por fuente"),
    tipo: Optional[str] = Query(None, description="Tipo de propiedad"),
    moneda: Optional[str] = Query(None, description="Filtrar por moneda: ARS o USD"),
    ordenar: Optional[str] = Query(None, description="Ordenar por: precio_asc, precio_desc, superficie_desc, reciente"),
    db: Session = Depends(get_db)
):
    """
    Lista propiedades con filtros opcionales
    
    - **precio_min/max**: Rango de precios
    - **barrio**: Nombre del barrio
    - **ambientes**: Cantidad exacta de ambientes
    - **dormitorios_min**: Mínimo de dormitorios
    - **superficie_min**: Superficie mínima
    - **mascotas**: true/false para permitidas
    - **patio**: true/false para patio
    - **fuente**: zonaprop, argenprop, remax, etc.
    - **tipo**: Departamento, Casa, etc.
    - **ordenar**: precio_asc, precio_desc, superficie_desc, reciente
    """
    
    query = db.query(Propiedad).filter(Propiedad.activa == True)
    
    # Aplicar filtros
    if precio_min is not None:
        query = query.filter(Propiedad.precio >= precio_min)
    
    if precio_max is not None:
        query = query.filter(Propiedad.precio <= precio_max)
    
    if barrio:
        query = query.filter(Propiedad.barrio.ilike(f"%{barrio}%"))
    
    if ambientes is not None:
        query = query.filter(Propiedad.ambientes == ambientes)
    
    if dormitorios_min is not None:
        query = query.filter(Propiedad.dormitorios >= dormitorios_min)
    
    if superficie_min is not None:
        query = query.filter(Propiedad.superficie_total >= superficie_min)
    
    if mascotas is not None:
        query = query.filter(Propiedad.mascotas == mascotas)
    
    if patio is not None:
        query = query.filter(Propiedad.patio == patio)
    
    if fuente:
        query = query.filter(Propiedad.fuente.ilike(f"%{fuente}%"))
    
    if tipo:
        query = query.filter(Propiedad.tipo.ilike(f"%{tipo}%"))
    
    if moneda:
        query = query.filter(Propiedad.moneda == moneda)
    
    # Aplicar ordenamiento
    if ordenar == 'precio_asc':
        query = query.order_by(Propiedad.precio.asc().nulls_last())
    elif ordenar == 'precio_desc':
        query = query.order_by(Propiedad.precio.desc().nulls_last())
    elif ordenar == 'superficie_desc':
        query = query.order_by(Propiedad.superficie_total.desc().nulls_last())
    elif ordenar == 'reciente':
        query = query.order_by(Propiedad.fecha_scraping.desc())
    else:
        # Por defecto: más recientes primero
        query = query.order_by(Propiedad.fecha_scraping.desc())
    
    # Paginación
    propiedades = query.offset(skip).limit(limit).all()
    
    return propiedades


@app.get("/propiedades/{propiedad_id}", response_model=PropiedadDetalle)
async def detalle_propiedad(
    propiedad_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene el detalle completo de una propiedad"""
    propiedad = db.query(Propiedad).filter(Propiedad.id == propiedad_id).first()
    
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    
    return propiedad


@app.get("/stats")
async def estadisticas(db: Session = Depends(get_db)):
    """Estadísticas generales"""
    total = db.query(func.count(Propiedad.id)).filter(Propiedad.activa == True).scalar()
    
    por_fuente = db.query(
        Propiedad.fuente,
        func.count(Propiedad.id).label('cantidad')
    ).filter(Propiedad.activa == True).group_by(Propiedad.fuente).all()
    
    precio_promedio = db.query(func.avg(Propiedad.precio)).filter(
        and_(Propiedad.activa == True, Propiedad.precio.isnot(None))
    ).scalar()
    
    precio_min = db.query(func.min(Propiedad.precio)).filter(
        and_(Propiedad.activa == True, Propiedad.precio.isnot(None))
    ).scalar()
    
    precio_max = db.query(func.max(Propiedad.precio)).filter(
        and_(Propiedad.activa == True, Propiedad.precio.isnot(None))
    ).scalar()
    
    return {
        "total_propiedades": total,
        "por_fuente": [{"fuente": f, "cantidad": c} for f, c in por_fuente],
        "precio_promedio": round(precio_promedio, 2) if precio_promedio else None,
        "precio_min": precio_min,
        "precio_max": precio_max
    }


@app.get("/barrios")
async def listar_barrios(db: Session = Depends(get_db)):
    """Lista todos los barrios disponibles con cantidad de propiedades"""
    barrios = db.query(
        Propiedad.barrio,
        func.count(Propiedad.id).label('cantidad')
    ).filter(
        and_(Propiedad.activa == True, Propiedad.barrio.isnot(None))
    ).group_by(Propiedad.barrio).order_by(func.count(Propiedad.id).desc()).all()
    
    return [{"barrio": b, "cantidad": c} for b, c in barrios if b]


@app.get("/fuentes")
async def listar_fuentes(db: Session = Depends(get_db)):
    """Lista todas las fuentes disponibles"""
    fuentes = db.query(
        Propiedad.fuente,
        func.count(Propiedad.id).label('cantidad')
    ).filter(Propiedad.activa == True).group_by(Propiedad.fuente).all()
    
    return [{"fuente": f, "cantidad": c} for f, c in fuentes]


@app.get("/buscar")
async def buscar_propiedades(
    q: str = Query(..., min_length=3, description="Término de búsqueda"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Búsqueda de texto libre en título y descripción"""
    propiedades = db.query(Propiedad).filter(
        and_(
            Propiedad.activa == True,
            or_(
                Propiedad.titulo.ilike(f"%{q}%"),
                Propiedad.descripcion.ilike(f"%{q}%"),
                Propiedad.barrio.ilike(f"%{q}%")
            )
        )
    ).limit(limit).all()
    
    return propiedades


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
