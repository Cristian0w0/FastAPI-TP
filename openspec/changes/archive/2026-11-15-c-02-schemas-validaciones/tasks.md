# Tasks: C-02 Schemas Segregados, Validadores y Documentación

## 1. Schemas Pydantic v2 y Validadores (`schemas.py`)

- [x] 1.1 Implementar `CantidadDecimal`, normalizador `RN-01` y helpers de entero `Decimal` en `app/modules/insumos/schemas.py`.
- [x] 1.2 Implementar `InsumoCreate`, `InsumoUpdate` y `AjusteCreate` con `extra="forbid"`, `RN-01` a `RN-08` y validación de `null` con `model_fields_set`.
- [x] 1.3 Implementar `InsumoPublic` (`from_attributes=True`, sin `codigo_proveedor`, con `bajo_minimo`) y `Pagina`.

## 2. Documentación y Pruebas de Contrato

- [x] 2.1 Crear `README.md` con guía de instalación/ejecución, justificación de los 3 schemas separados (Objetivo 1) y explicación en 2-3 oraciones de `RN-04` (`422` en alta vs `409` en `PATCH`, Ejercicio 3).
- [x] 2.2 Crear `test/test_schemas.py` cubriendo `RN-01` a `RN-08`, múltiples errores simultáneos (`C-06`), serialización JSON de `Decimal` y exclusión de `codigo_proveedor`, verificando con `python -m pytest -v`.

## Workflow follow-up

- Validar con `openspec validate c-02-schemas-validaciones --strict` antes de archivar.
- Archivar el change con `openspec archive c-02-schemas-validaciones --yes` y marcar `[x]` en `CHANGES.md`.
