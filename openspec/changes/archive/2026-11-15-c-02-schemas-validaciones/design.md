# Design: C-02 Schemas Segregados, Validadores y Documentación

## Context
Ver `proposal.md` y [spec.md](../../specs/insumos-base/spec.md) para el modelo de dominio existente (`Unidad`, `MotivoAjuste`, `Insumo`). Este change implementa `app/modules/insumos/schemas.py`, `README.md` y `test/test_schemas.py` sobre la rama `feat/c-02-schemas-validaciones`.

## Goals / Non-Goals

**Goals:**
- Declarar los 5 schemas obligatorios (`InsumoCreate`, `InsumoUpdate`, `AjusteCreate`, `InsumoPublic`, `Pagina`) en Pydantic v2.
- Garantizar en el contrato de entrada/salida las reglas `RN-01` a `RN-08` y el ocultamiento de `codigo_proveedor` (`RN-05`).
- Documentar en `README.md` la arquitectura de 3 schemas y la distinción `422` vs `409` en `RN-04`.
- Proveer pruebas unitarias completas en `test/test_schemas.py`.

**Non-Goals:**
- Implementar la lógica de negocio de `service.py` ni rutas HTTP en `router.py` (`C-03` y `C-04`).

## Decisions

### D1: Normalización de `nombre` en `@field_validator(..., mode="before")`
- **Decisión**: Normalizar `nombre` con `" ".join(v.split())` en `mode="before"` cuando `isinstance(v, str)`.
- **Razón**: Garantiza que `"   "` se reduzca a `""` antes de la restricción `min_length=1` (emitiendo un error de campo estándar junto a otros errores simultáneos como en `C-06`), que `"  " + "a"*80 + "  "` no falle injustamente `max_length=80`, y que tipos no-`str` o `None` en `InsumoUpdate` pasen intactos a la validación estándar y al detector `RN-07`.
- **Alternativas**: Usar `mode="after"`. Descartado porque permitiría rechazar `"  " + "a"*80 + "  "` antes de limpiarlo.

### D2: `Decimal` entero para `unidad == "unidad"` en `InsumoCreate`
- **Decisión**: Validar `valor % 1 != 0` en `@model_validator(mode="after")` cuando `self.unidad == Unidad.unidad` y normalizar `stock` y `stock_minimo` con `valor.quantize(Decimal("1"))`.
- **Razón**: Mantiene el tipo `Decimal` (sin usar `float`) y asegura que los insumos contables por unidad viajen en JSON como enteros en texto (`"60"`, `"12"`), rechazando `"12.5"` con `422`.

### D3: Detección de `null` explícito en `InsumoUpdate` con `model_fields_set`
- **Decisión**: Declarar `nombre`, `stock_minimo`, `activo` y `codigo_proveedor` con `default=None` y validar en `@model_validator(mode="after")` que ninguno de los tres primeros esté presente en `self.model_fields_set` con valor `None`.
- **Razón**: Distingue exactamente «campo omitido» (`exclude_unset=True` no lo incluye) de «campo enviado como `null`» (`422` en `nombre`/`stock_minimo`/`activo`; permitido en `codigo_proveedor` para borrarlo).

### D4: Reglas de signo y cero en `AjusteCreate`
- **Decisión**: Declarar `cantidad: Decimal = Field(..., max_digits=12, decimal_places=3)` sin `ge=0` y validar `!= 0` y coherencia de signo frente a `motivo` en `@model_validator(mode="after")`.
- **Razón**: Permite consumos/mermas/correcciones negativas mientras bloquea en el contrato `cantidad == 0`, compras negativas y consumos/mermas positivos.

## Risks / Trade-offs
- **[Riesgo] Envío de `float` JSON nativo con imprecisión binaria (ej. `0.1` o `12.5`)** → **Mitigación**: Pydantic v2 parsea números a `Decimal` respetando `max_digits=12` y `decimal_places=3` sin redondear silenciosamente excesos decimales, y serializa siempre `Decimal` a texto en JSON (`model_dump_json` / respuestas FastAPI).
