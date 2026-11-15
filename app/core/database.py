"""Base de datos en memoria, datos semilla iniciales y dependencia get_db."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import Request

from app.modules.insumos.models import Insumo, Unidad


@dataclass
class InsumosDB:
    """Almacenamiento en memoria con lista de insumos y contador monotónico de IDs."""

    items: list[Insumo] = field(default_factory=list)
    next_id: int = 1


def crear_base_inicial() -> InsumosDB:
    """Construye una instancia limpia de la base con los seis insumos iniciales."""
    ahora = datetime.now(timezone.utc)
    semilla = [
        Insumo(
            id=1,
            nombre="Harina 000",
            unidad=Unidad.kg,
            stock=Decimal("25.000"),
            stock_minimo=Decimal("10.000"),
            activo=True,
            codigo_proveedor="HAR-0001",
            creado_en=ahora,
        ),
        Insumo(
            id=2,
            nombre="Mozzarella",
            unidad=Unidad.kg,
            stock=Decimal("3.500"),
            stock_minimo=Decimal("5.000"),
            activo=True,
            codigo_proveedor="MOZ-0002",
            creado_en=ahora,
        ),
        Insumo(
            id=3,
            nombre="Aceite de girasol",
            unidad=Unidad.l,
            stock=Decimal("12.000"),
            stock_minimo=Decimal("4.000"),
            activo=True,
            codigo_proveedor="ACE-0003",
            creado_en=ahora,
        ),
        Insumo(
            id=4,
            nombre="Huevos",
            unidad=Unidad.unidad,
            stock=Decimal("60"),
            stock_minimo=Decimal("30"),
            activo=True,
            codigo_proveedor="HUE-0004",
            creado_en=ahora,
        ),
        Insumo(
            id=5,
            nombre="Sal fina",
            unidad=Unidad.g,
            stock=Decimal("800.000"),
            stock_minimo=Decimal("1000.000"),
            activo=True,
            codigo_proveedor="SAL-0005",
            creado_en=ahora,
        ),
        Insumo(
            id=6,
            nombre="Levadura seca",
            unidad=Unidad.g,
            stock=Decimal("250.000"),
            stock_minimo=Decimal("100.000"),
            activo=False,
            codigo_proveedor="LEV-0006",
            creado_en=ahora,
        ),
    ]
    return InsumosDB(items=semilla, next_id=7)


def get_db(request: Request) -> InsumosDB:
    """Devuelve la base en memoria creada en el lifespan y guardada en app.state."""
    return request.app.state.db
