"""Lógica de negocio pura para gestión de insumos en memoria (sin dependencias HTTP)."""

from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal
import math
from typing import Any

from app.core.database import InsumosDB
from app.modules.insumos.models import (
    ConflictoInsumoError,
    Insumo,
    PaginaFueraDeRangoError,
    Unidad,
)
from app.modules.insumos.schemas import AjusteCreate, InsumoCreate, InsumoUpdate

CRITERIOS_ORDEN: dict[str, Callable[[Insumo], Any]] = {
    "nombre": lambda item: item.nombre.casefold(),
    "stock": lambda item: item.stock,
    "creado_en": lambda item: item.creado_en,
}


def _validar_entero_unidad(valor: Decimal, unidad: Unidad, contexto: str) -> Decimal:
    """Exige y normaliza a Decimal entero cuando la unidad del insumo es 'unidad' (RN-04)."""
    if unidad != Unidad.unidad:
        return valor
    if valor % 1 != 0:
        raise ConflictoInsumoError(
            f"Un insumo medido en 'unidad' no admite decimales en {contexto}."
        )
    return valor.quantize(Decimal("1"))


def obtener_insumo(db: InsumosDB, insumo_id: int) -> Insumo | None:
    """Busca un insumo por su ID y devuelve None si no existe."""
    for item in db.items:
        if item.id == insumo_id:
            return item
    return None


def crear_insumo(db: InsumosDB, datos: InsumoCreate) -> Insumo:
    """Crea y almacena un nuevo insumo asignando un ID único que nunca se reutiliza."""
    nuevo = Insumo(
        id=db.next_id,
        nombre=datos.nombre,
        unidad=datos.unidad,
        stock=datos.stock,
        stock_minimo=datos.stock_minimo,
        activo=datos.activo,
        codigo_proveedor=datos.codigo_proveedor,
        creado_en=datetime.now(timezone.utc),
    )
    db.next_id += 1
    db.items.append(nuevo)
    return nuevo


def actualizar_insumo(
    db: InsumosDB,
    insumo_id: int,
    datos: InsumoUpdate,
) -> Insumo | None:
    """Aplica cambios parciales usando exclude_unset=True y validando RN-04 contra la unidad."""
    insumo = obtener_insumo(db, insumo_id)
    if insumo is None:
        return None

    cambios = datos.model_dump(exclude_unset=True)
    if "stock_minimo" in cambios:
        cambios["stock_minimo"] = _validar_entero_unidad(
            cambios["stock_minimo"],
            insumo.unidad,
            "stock_minimo",
        )

    for campo, valor in cambios.items():
        setattr(insumo, campo, valor)
    return insumo


def ajustar_stock_insumo(
    db: InsumosDB,
    insumo_id: int,
    datos: AjusteCreate,
) -> Insumo | None:
    """Registra un ajuste de stock validando unidad entera (RN-04) y stock no negativo (RN-09)."""
    insumo = obtener_insumo(db, insumo_id)
    if insumo is None:
        return None

    _validar_entero_unidad(datos.cantidad, insumo.unidad, "un ajuste")
    nuevo_stock = insumo.stock + datos.cantidad
    if nuevo_stock < 0:
        raise ConflictoInsumoError(
            "El ajuste dejaría el stock del insumo por debajo de cero."
        )

    insumo.stock = _validar_entero_unidad(nuevo_stock, insumo.unidad, "stock")
    return insumo


def eliminar_insumo(db: InsumosDB, insumo_id: int) -> bool:
    """Elimina un insumo por ID sin decrementar ni reutilizar el contador next_id."""
    for indice, item in enumerate(db.items):
        if item.id == insumo_id:
            del db.items[indice]
            return True
    return False


def listar_insumos(
    db: InsumosDB,
    *,
    page: int = 1,
    size: int = 20,
    sort: str | None = None,
    unidad: Unidad | None = None,
    bajo_minimo: bool | None = None,
    activo: bool | None = None,
) -> dict[str, Any]:
    """Filtra antes de contar, ordena contra lista blanca y pagina los insumos (RN-10 a RN-12)."""
    filtrados = [
        item
        for item in db.items
        if (unidad is None or item.unidad == unidad)
        and (bajo_minimo is None or item.bajo_minimo == bajo_minimo)
        and (activo is None or item.activo == activo)
    ]

    total = len(filtrados)
    pages = math.ceil(total / size) if total > 0 else 0

    if (total == 0 and page > 1) or (total > 0 and page > pages):
        raise PaginaFueraDeRangoError(
            f"La página {page} excede el total de páginas disponibles ({pages})."
        )

    if sort is not None:
        descendente = sort.startswith("-")
        campo = sort[1:] if descendente else sort
        clave = CRITERIOS_ORDEN.get(campo)
        if clave is None:
            raise ValueError(f"Criterio de ordenamiento no permitido: {sort}")
        ordenados = sorted(filtrados, key=clave, reverse=descendente)
    else:
        ordenados = filtrados

    inicio = (page - 1) * size
    return {
        "items": ordenados[inicio : inicio + size],
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }
