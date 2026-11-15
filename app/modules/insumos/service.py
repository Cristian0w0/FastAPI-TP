"""Lógica de negocio pura para gestión de insumos en memoria (sin dependencias HTTP)."""

from datetime import datetime, timezone
from decimal import Decimal

from app.core.database import InsumosDB
from app.modules.insumos.models import ConflictoInsumoError, Insumo, Unidad
from app.modules.insumos.schemas import AjusteCreate, InsumoCreate, InsumoUpdate


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
