"""Rutas HTTP para operaciones CRUD individuales y ajustes de stock de insumos."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.database import InsumosDB, get_db
from app.modules.insumos.models import (
    ConflictoInsumoError,
    Insumo,
    PaginaFueraDeRangoError,
    Unidad,
)
from app.modules.insumos.schemas import (
    AjusteCreate,
    InsumoCreate,
    InsumoPublic,
    InsumoUpdate,
    Pagina,
)
from app.modules.insumos.service import (
    actualizar_insumo,
    ajustar_stock_insumo,
    crear_insumo,
    eliminar_insumo,
    listar_insumos,
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


@router.get("/", response_model=Pagina)
async def listar(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    sort: str | None = Query(default=None, pattern=r"^-?(nombre|stock|creado_en)$"),
    unidad: Unidad | None = Query(default=None),
    bajo_minimo: bool | None = Query(default=None),
    activo: bool | None = Query(default=None),
    db: InsumosDB = Depends(get_db),
) -> dict[str, object]:
    """Lista insumos paginados, filtrables antes de contar y ordenables contra lista blanca."""
    try:
        return listar_insumos(
            db,
            page=page,
            size=size,
            sort=sort,
            unidad=unidad,
            bajo_minimo=bajo_minimo,
            activo=activo,
        )
    except PaginaFueraDeRangoError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


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
