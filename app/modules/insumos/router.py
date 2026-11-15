"""Rutas HTTP para operaciones CRUD individuales y ajustes de stock de insumos."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.database import InsumosDB, get_db
from app.modules.insumos.models import ConflictoInsumoError, Insumo
from app.modules.insumos.schemas import (
    AjusteCreate,
    InsumoCreate,
    InsumoPublic,
    InsumoUpdate,
)
from app.modules.insumos.service import (
    actualizar_insumo,
    ajustar_stock_insumo,
    crear_insumo,
    eliminar_insumo,
    obtener_insumo,
)

router = APIRouter(prefix="/insumos", tags=["Insumos"])


def _asegurar_encontrado(insumo: Insumo | None) -> Insumo:
    """Traduce una ausencia en el servicio a HTTPException 404."""
    if insumo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insumo no encontrado.",
        )
    return insumo


@router.get("/{insumo_id}", response_model=InsumoPublic)
async def obtener_detalle(
    insumo_id: int,
    db: InsumosDB = Depends(get_db),
) -> Insumo:
    """Obtiene el detalle público de un insumo por ID."""
    return _asegurar_encontrado(obtener_insumo(db, insumo_id))


@router.post("/", response_model=InsumoPublic, status_code=status.HTTP_201_CREATED)
async def crear(
    datos: InsumoCreate,
    response: Response,
    db: InsumosDB = Depends(get_db),
) -> Insumo:
    """Crea un nuevo insumo y devuelve 201 con encabezado Location."""
    creado = crear_insumo(db, datos)
    response.headers["Location"] = f"/insumos/{creado.id}"
    return creado


@router.patch("/{insumo_id}", response_model=InsumoPublic)
async def actualizar_parcial(
    insumo_id: int,
    datos: InsumoUpdate,
    db: InsumosDB = Depends(get_db),
) -> Insumo:
    """Actualiza parcialmente los campos permitidos de un insumo."""
    try:
        actualizado = actualizar_insumo(db, insumo_id, datos)
    except ConflictoInsumoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return _asegurar_encontrado(actualizado)


@router.post("/{insumo_id}/ajustes", response_model=InsumoPublic)
async def registrar_ajuste(
    insumo_id: int,
    datos: AjusteCreate,
    db: InsumosDB = Depends(get_db),
) -> Insumo:
    """Registra un ajuste de stock sobre un insumo existente y responde 200 OK."""
    try:
        actualizado = ajustar_stock_insumo(db, insumo_id, datos)
    except ConflictoInsumoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return _asegurar_encontrado(actualizado)


@router.delete("/{insumo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar(
    insumo_id: int,
    db: InsumosDB = Depends(get_db),
) -> Response:
    """Elimina un insumo por ID respondiendo 204 sin cuerpo."""
    if not eliminar_insumo(db, insumo_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insumo no encontrado.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
