# Proposal: C-02 Schemas Segregados, Validadores y Documentación

## Why
Con la base en memoria y los modelos de dominio listos en `main` (`C-01`), la API necesita declarar formalmente su contrato de entrada y salida en Pydantic v2 antes de implementar la lógica de negocio y los endpoints. Separar el modelo almacenado de los schemas de entrada (`InsumoCreate`, `InsumoUpdate`, `AjusteCreate`) y de salida (`InsumoPublic`, `Pagina`) permite rechazar datos inválidos o campos no permitidos (`422`) antes de ejecutar el servicio y proteger datos internos como `codigo_proveedor`.

## What Changes
- **Contrato de schemas (`app/modules/insumos/schemas.py`)**:
  - `InsumoCreate`: alta con normalización de `nombre` (`RN-01`), `unidad` (`RN-02`), cantidades `Decimal` de hasta 12 dígitos y 3 decimales (`RN-03`), validación entera para `unidad == "unidad"` normalizada a `Decimal` entero (`RN-04`), patrón `^[A-Z]{3}-\d{4}$` en `codigo_proveedor` (`RN-05`) y rechazo de campos extra (`extra="forbid"`, `RN-06`).
  - `InsumoUpdate`: actualización parcial omitiendo `unidad`, `stock`, `id`, `creado_en` y `bajo_minimo` (`extra="forbid"`, `RN-06`), permitiendo `null` únicamente en `codigo_proveedor` (`RN-07`).
  - `AjusteCreate`: `cantidad` `Decimal` distinta de cero con validación de signo según `motivo` (`compra` positiva; `consumo` y `merma` negativas; `correccion` positiva o negativa) y `extra="forbid"` (`RN-08`).
  - `InsumoPublic` y `Pagina`: respuestas tipadas con `from_attributes=True`, serialización de `Decimal` en texto, cálculo de `bajo_minimo` y exclusión absoluta de `codigo_proveedor` (`RN-05`, `RN-10`).
- **Documentación (`README.md`)**: Guía de instalación/arranque local, justificación de los 3 modelos/schemas separados (Objetivo 1) y explicación en 2-3 oraciones de por qué `RN-04` responde `422` en el alta y `409` en `PATCH` (Ejercicio 3).
- **Pruebas unitarias (`test/test_schemas.py`)**: Batería `pytest` cubriendo `RN-01` a `RN-08`, serialización JSON de `Decimal` y ocultamiento de `codigo_proveedor`.

### Fuera de alcance
- No se implementan `app/modules/insumos/service.py`, `app/modules/insumos/router.py`, el registro del router en `app/main.py` ni `test/insumos.http` (corresponden a `C-03` y `C-04`).

## Capabilities

### New Capabilities
- `insumos-schemas`: Contrato completo de entrada y salida con Pydantic v2 (`InsumoCreate`, `InsumoUpdate`, `AjusteCreate`, `InsumoPublic`, `Pagina`) y validadores de campo y de modelo para `RN-01` a `RN-08` y ocultamiento de `codigo_proveedor`.

### Modified Capabilities
*(Ninguna; `insumos-base` permanece intacto.)*

## Impact
- **Archivos nuevos**: `app/modules/insumos/schemas.py`, `README.md`, `test/test_schemas.py`.
- **Consumidores**: `C-03` (`service.py` y `router.py`) y `C-04` (`GET /insumos/` con `Pagina`) importarán estos 5 schemas sin modificar `models.py` ni `database.py`.
