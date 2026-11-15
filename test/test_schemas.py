"""Pruebas unitarias para C-02: schemas segregados y validadores RN-01 a RN-08."""

from datetime import datetime, timezone
from decimal import Decimal
import json

import pytest
from pydantic import ValidationError

from app.modules.insumos.models import Insumo, MotivoAjuste, Unidad
from app.modules.insumos.schemas import (
    AjusteCreate,
    InsumoCreate,
    InsumoPublic,
    InsumoUpdate,
    Pagina,
)


def test_rn01_normaliza_nombre_y_rechaza_solo_espacios() -> None:
    """RN-01: recorta bordes, colapsa espacios internos y rechaza nombres vacíos o solo espacios."""
    creado = InsumoCreate(nombre="  Queso   rallado  ", unidad=Unidad.kg)
    assert creado.nombre == "Queso rallado"

    actualizado = InsumoUpdate(nombre="  Harina   000  ")
    assert actualizado.nombre == "Harina 000"

    for invalido in ("", "   ", "a" * 81):
        with pytest.raises(ValidationError):
            InsumoCreate(nombre=invalido, unidad=Unidad.kg)
        with pytest.raises(ValidationError):
            InsumoUpdate(nombre=invalido)


def test_rn02_rn03_decimal_exacto_y_serializacion_en_texto() -> None:
    """RN-02/RN-03: usa Decimal en texto, rechaza 4 decimales sin redondear y rechaza unidad inválida."""
    insumo = InsumoCreate(
        nombre="Queso rallado",
        unidad="kg",
        stock="2.250",
        stock_minimo="1.000",
    )
    assert isinstance(insumo.stock, Decimal)
    assert insumo.stock == Decimal("2.250")
    payload_json = json.loads(insumo.model_dump_json())
    assert payload_json["stock"] == "2.250"
    assert payload_json["stock_minimo"] == "1.000"

    # Cuatro decimales se rechazan sin redondeo
    with pytest.raises(ValidationError):
        InsumoCreate(nombre="Sal", unidad=Unidad.g, stock="1.2345")

    # Más de 12 dígitos totales se rechaza
    with pytest.raises(ValidationError):
        InsumoCreate(nombre="Sal", unidad=Unidad.g, stock="1234567890.123")

    # Unidad fuera de enumeración se rechaza
    with pytest.raises(ValidationError):
        InsumoCreate(nombre="Huevos", unidad="docena")


def test_rn04_unidad_entera_en_alta_y_normalizacion() -> None:
    """RN-04 en alta: unidad='unidad' rechaza decimales y normaliza enteros sin .000."""
    valido = InsumoCreate(
        nombre="Huevos",
        unidad=Unidad.unidad,
        stock="12",
        stock_minimo="6",
    )
    assert valido.stock == Decimal("12")
    assert str(valido.stock) == "12"
    assert str(valido.stock_minimo) == "6"

    # Caso C-05: unidad con decimal 12.5 se rechaza
    with pytest.raises(ValidationError):
        InsumoCreate(nombre="Huevos", unidad=Unidad.unidad, stock="12.5")

    with pytest.raises(ValidationError):
        InsumoCreate(nombre="Huevos", unidad=Unidad.unidad, stock_minimo="1.25")


def test_c06_multiples_errores_en_misma_respuesta() -> None:
    """C-06: nombre vacío, unidad inválida y stock negativo reportan 3 errores juntos."""
    with pytest.raises(ValidationError) as exc_info:
        InsumoCreate(nombre="", unidad="docena", stock=-1)

    campos_con_error = {err["loc"][0] for err in exc_info.value.errors()}
    assert campos_con_error == {"nombre", "unidad", "stock"}


def test_rn05_rn06_codigo_proveedor_oculto_y_extra_forbid() -> None:
    """RN-05/RN-06: valida formato AAA-9999, rechaza extras y nunca expone codigo_proveedor."""
    creado = InsumoCreate(
        nombre="Queso rallado",
        unidad=Unidad.kg,
        codigo_proveedor="QUE-0007",
    )
    assert creado.codigo_proveedor == "QUE-0007"

    with pytest.raises(ValidationError):
        InsumoCreate(nombre="Queso", unidad=Unidad.kg, codigo_proveedor="que-0007")

    # Extra forbid en entrada (C-07 y C-10)
    with pytest.raises(ValidationError):
        InsumoCreate(nombre="Queso", unidad=Unidad.kg, id=99)
    with pytest.raises(ValidationError):
        InsumoUpdate(stock="10.000")
    with pytest.raises(ValidationError):
        InsumoUpdate(unidad="g")
    with pytest.raises(ValidationError):
        AjusteCreate(cantidad="1.000", motivo=MotivoAjuste.compra, extra_campo=1)

    # InsumoPublic oculta codigo_proveedor
    modelo = Insumo(
        id=7,
        nombre="Queso rallado",
        unidad=Unidad.kg,
        stock=Decimal("2.250"),
        stock_minimo=Decimal("1.000"),
        activo=True,
        codigo_proveedor="QUE-0007",
        creado_en=datetime.now(timezone.utc),
    )
    publico = InsumoPublic.model_validate(modelo)
    assert "codigo_proveedor" not in publico.model_dump()
    assert publico.bajo_minimo is False
    data = json.loads(publico.model_dump_json())
    assert data["stock"] == "2.250"
    assert data["creado_en"].endswith("Z")

    pagina = Pagina(items=[publico], total=1, page=1, size=20, pages=1)
    assert pagina.total == 1
    assert len(pagina.items) == 1


def test_rn07_patch_exclude_unset_y_null_solo_en_codigo_proveedor() -> None:
    """RN-07: null solo es válido en codigo_proveedor; otros campos con null fallan."""
    borrar_codigo = InsumoUpdate(codigo_proveedor=None)
    assert borrar_codigo.model_dump(exclude_unset=True) == {"codigo_proveedor": None}

    solo_minimo = InsumoUpdate(stock_minimo="15.000")
    assert solo_minimo.model_dump(exclude_unset=True) == {"stock_minimo": Decimal("15.000")}

    for campo in ("nombre", "stock_minimo", "activo"):
        with pytest.raises(ValidationError):
            InsumoUpdate(**{campo: None})


def test_rn08_ajuste_create_signo_y_cero() -> None:
    """RN-08: rechaza 0, exige + en compra, - en consumo/merma, y permite ambos en correccion."""
    assert AjusteCreate(cantidad="2.500", motivo=MotivoAjuste.compra).cantidad == Decimal("2.500")
    assert AjusteCreate(cantidad="-1.250", motivo=MotivoAjuste.consumo).cantidad == Decimal("-1.250")
    assert AjusteCreate(cantidad="-0.500", motivo=MotivoAjuste.merma).cantidad == Decimal("-0.500")
    assert AjusteCreate(cantidad="1.000", motivo=MotivoAjuste.correccion).cantidad == Decimal("1.000")
    assert AjusteCreate(cantidad="-1.000", motivo=MotivoAjuste.correccion).cantidad == Decimal("-1.000")

    with pytest.raises(ValidationError):
        AjusteCreate(cantidad="0", motivo=MotivoAjuste.compra)
    with pytest.raises(ValidationError):
        AjusteCreate(cantidad="-1.000", motivo=MotivoAjuste.compra)
    with pytest.raises(ValidationError):
        AjusteCreate(cantidad="1.000", motivo=MotivoAjuste.consumo)
    with pytest.raises(ValidationError):
        AjusteCreate(cantidad="1.000", motivo=MotivoAjuste.merma)
    with pytest.raises(ValidationError):
        AjusteCreate(cantidad="1.2345", motivo=MotivoAjuste.compra)
