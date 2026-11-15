"""Modelos del dominio, enumeraciones y excepciones de negocio para insumos."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class Unidad(str, Enum):
    """Unidades válidas de medida para un insumo."""

    kg = "kg"
    g = "g"
    l = "l"
    ml = "ml"
    unidad = "unidad"


class MotivoAjuste(str, Enum):
    """Motivos permitidos para registrar un ajuste de stock."""

    compra = "compra"
    consumo = "consumo"
    merma = "merma"
    correccion = "correccion"


class ConflictoInsumoError(Exception):
    """Error de negocio cuando la operación entra en conflicto con el insumo guardado (HTTP 409)."""


class PaginaFueraDeRangoError(Exception):
    """Error cuando se solicita una página más allá del total disponible (HTTP 422)."""


@dataclass
class Insumo:
    """Representación interna de un insumo almacenado en memoria."""

    id: int
    nombre: str
    unidad: Unidad
    stock: Decimal
    stock_minimo: Decimal
    activo: bool
    codigo_proveedor: str | None
    creado_en: datetime

    @property
    def bajo_minimo(self) -> bool:
        """Indica en tiempo real si el stock está por debajo del mínimo configurado."""
        return self.stock < self.stock_minimo
