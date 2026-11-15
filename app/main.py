"""Punto de entrada de la aplicación FastAPI y configuración de su lifespan."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import crear_base_inicial


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base en memoria una única vez al arrancar el servidor."""
    app.state.db = crear_base_inicial()
    yield


app = FastAPI(
    title="Los insumos de la cocina",
    description="Contrato completo con FastAPI para gestión de insumos en memoria (UTN Programación III).",
    version="0.1.0",
    lifespan=lifespan,
)

# Integrante 3 (C-03): importar y registrar insumos_router aquí con app.include_router(insumos_router)
