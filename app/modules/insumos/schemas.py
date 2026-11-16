"""Schemas Pydantic v2 y validadores de contrato para el módulo de insumos."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.insumos.models import MotivoAjuste, Unidad

CantidadDecimal = Annotated[Decimal, Field(max_digits=12, decimal_places=3, ge=0)]


def _normalizar_nombre(valor: object) -> object:
    """Recorta espacios externos y colapsa espacios repetidos en cadenas (RN-01)."""
    if isinstance(valor, str):
        return " ".join(valor.split())
    return valor


def _tiene_decimales(valor: Decimal) -> bool:
    """Indica si un Decimal tiene parte fraccionaria distinta de cero."""
    return valor % 1 != 0


class InsumoCreate(BaseModel):
    """Contrato de entrada para dar de alta un insumo (POST /insumos/)."""

    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., min_length=1, max_length=80)
    unidad: Unidad
    stock: CantidadDecimal = Field(default=Decimal("0"))
    stock_minimo: CantidadDecimal = Field(default=Decimal("0"))
    activo: bool = Field(default=True)
    codigo_proveedor: str | None = Field(default=None, pattern=r"^[A-Z]{3}-\d{4}$")

    @field_validator("nombre", mode="before")
    @classmethod
    def normalizar_nombre(cls, valor: object) -> object:
        return _normalizar_nombre(valor)

    @model_validator(mode="after")
    def validar_enteros_para_unidad(self) -> "InsumoCreate":
        """Exige enteros en stock y stock_minimo cuando la unidad es 'unidad' (RN-04)."""
        if self.unidad == Unidad.unidad:
            if _tiene_decimales(self.stock) or _tiene_decimales(self.stock_minimo):
                raise ValueError(
                    "Los insumos medidos en 'unidad' no admiten decimales en stock ni en stock_minimo."
                )
            self.stock = self.stock.quantize(Decimal("1"))
            self.stock_minimo = self.stock_minimo.quantize(Decimal("1"))
        return self


class InsumoUpdate(BaseModel):
    """Contrato de entrada para actualización parcial (PATCH /insumos/{id})."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1, max_length=80)
    stock_minimo: CantidadDecimal | None = Field(default=None)
    activo: bool | None = Field(default=None)
    codigo_proveedor: str | None = Field(default=None, pattern=r"^[A-Z]{3}-\d{4}$")

    @field_validator("nombre", mode="before")
    @classmethod
    def normalizar_nombre(cls, valor: object) -> object:
        return _normalizar_nombre(valor)

    @model_validator(mode="after")
    def validar_campos_no_nulos(self) -> "InsumoUpdate":
        """Permite null solo en codigo_proveedor; lo rechaza en el resto (RN-07)."""
        campos_no_nulables = ("nombre", "stock_minimo", "activo")
        invalidos = [
            campo
            for campo in campos_no_nulables
            if campo in self.model_fields_set and getattr(self, campo) is None
        ]
        if invalidos:
            raise ValueError(
                f"Los siguientes campos no admiten null en PATCH: {', '.join(invalidos)}."
            )
        return self


class AjusteCreate(BaseModel):
    """Contrato de entrada para registrar un ajuste de stock (POST /insumos/{id}/ajustes)."""

    model_config = ConfigDict(extra="forbid")

    cantidad: Decimal = Field(..., max_digits=12, decimal_places=3)
    motivo: MotivoAjuste

    @model_validator(mode="after")
    def validar_signo_y_cantidad(self) -> "AjusteCreate":
        """Valida que la cantidad no sea cero y respete el signo del motivo (RN-08)."""
        if self.cantidad == 0:
            raise ValueError("La cantidad del ajuste no puede ser cero.")
        if self.motivo == MotivoAjuste.compra and self.cantidad < 0:
            raise ValueError("Un ajuste con motivo 'compra' debe tener cantidad positiva.")
        if self.motivo in (MotivoAjuste.consumo, MotivoAjuste.merma) and self.cantidad > 0:
            raise ValueError(
                f"Un ajuste con motivo '{self.motivo.value}' debe tener cantidad negativa."
            )
        return self


class InsumoPublic(BaseModel):
    """Contrato de salida público de un insumo, ocultando codigo_proveedor (RN-05)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    unidad: Unidad
    stock: Decimal
    stock_minimo: Decimal
    activo: bool
    bajo_minimo: bool
    creado_en: datetime


class Pagina(BaseModel):
    """Envoltorio de respuesta paginada para el listado de insumos (RN-10)."""

    items: list[InsumoPublic]
    total: int
    page: int
    size: int
    pages: int
