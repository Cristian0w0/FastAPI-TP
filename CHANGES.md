# CHANGES — Secuencia de Implementación

> Índice canónico de los 4 changes del TP **Los insumos de la cocina (UTN Programación III)**.
> **Leer este archivo y [AGENTS.md](AGENTS.md) antes de ejecutar cualquier `/opsx:propose`.**

---

## Flujo Secuencial en GitHub y OpenSpec

```text
main (Integrante 1: C-01)
  └── feat/c-02-schemas-validaciones (Integrante 2: C-02)
        └── feat/c-03-crud-y-ajustes (Integrante 3: C-03)
              └── feat/c-04-listado-y-pruebas (Integrante 4: C-04) ──▶ Merge final a main
```

1. Verificar que el change anterior esté archivado en `openspec/changes/archive/` y marcado `[x]`.
2. Crear la nueva rama **desde la rama del integrante anterior** (excepto `C-01` que vive en `main`).
3. Ejecutar `/opsx:propose <nombre-del-change>`.
4. Implementar tareas (`/opsx:apply <nombre-del-change>`) y verificar con `pytest -v`.
5. Archivar con `/opsx:archive <nombre-del-change>`, marcar `[x]` aquí y pushear la rama.

---

## Etapas y Dependencias

### [C-01] `c-01-base-modelos-app` — Integrante 1 (`main`)
- **Estado**: `[x]` completado (archivado en `openspec/changes/archive/2026-11-14-c-01-base-modelos-app`)
- **Dependencias**: ninguna
- **Scope**:
  - `.gitignore` (excluyendo `.venv/`, `__pycache__/`, `.pytest_cache/`), `requirements.txt`, `pyproject.toml`, OpenSpec (`AGENTS.md`, `CHANGES.md`, `openspec/config.yaml`).
  - `app/modules/insumos/models.py`: enumeraciones `Unidad` y `MotivoAjuste`, excepciones de dominio (`ConflictoInsumoError`, `PaginaFueraDeRangoError`) y modelo `Insumo` con propiedad calculada `bajo_minimo`.
  - `app/core/database.py`: `InsumosDB`, seed inicial de los 6 insumos (`next_id = 7`), y dependencia `get_db`.
  - `app/main.py`: `lifespan` que crea la base una sola vez en `app.state.db`.
  - `test/test_base.py`: tests iniciales de arranque y datos semilla.
- **Leer antes**: `TP_Cap2_Consigna.pdf`, `PLAN.md`.

---

### [C-02] `c-02-schemas-validaciones` — Integrante 2 (rama `feat/c-02-schemas-validaciones` desde `main`)
- **Estado**: `[x]` completado (archivado en `openspec/changes/archive/2026-11-15-c-02-schemas-validaciones`)
- **Dependencias**: `C-01`
- **Scope**:
  - `app/modules/insumos/schemas.py`: `InsumoCreate`, `InsumoUpdate`, `AjusteCreate`, `InsumoPublic`, `Pagina`, validadores `RN-01` a `RN-08`, `extra="forbid"`, `Decimal` en texto y enteros para `unidad == "unidad"`.
  - `README.md`: guía de ejecución, por qué son 3 schemas separados (Objetivo 1) y explicación en 2-3 oraciones de por qué `RN-04` da `422` en alta y `409` en `PATCH` (Ejercicio 3).
  - `test/test_schemas.py`: pruebas unitarias de validadores y contratos.
- **Leer antes**: `AGENTS.md`, `app/modules/insumos/models.py`, `openspec/specs/insumos-base/spec.md`.

---

### [C-03] `c-03-crud-y-ajustes` — Integrante 3 (rama `feat/c-03-crud-y-ajustes` desde `feat/c-02-schemas-validaciones`)
- **Estado**: `[x]` completado (archivado en `openspec/changes/archive/2026-11-15-c-03-crud-y-ajustes`)
- **Dependencias**: `C-02`
- **Scope**:
  - `app/modules/insumos/service.py`: funciones puras (sin HTTP) para `obtener_insumo`, `crear_insumo`, `actualizar_insumo` (`exclude_unset=True`, borrado de `codigo_proveedor`, `RN-04` -> `ConflictoInsumoError`), `ajustar_stock_insumo` (`RN-04` y `RN-09` -> `ConflictoInsumoError` sin mutar) y `eliminar_insumo` (sin reutilizar IDs).
  - `app/modules/insumos/router.py`: rutas `async def` (`GET /{id}`, `POST /` con `201` + `Location`, `PATCH /{id}`, `POST /{id}/ajustes` con `200`, `DELETE /{id}` con `204`).
  - `app/main.py`: registrar `insumos_router`.
  - `test/test_crud_ajustes.py`: pruebas de endpoints individuales y casos `C-01` a `C-12` y `C-16`.
- **Leer antes**: `AGENTS.md`, `app/modules/insumos/schemas.py`, `app/core/database.py`.

---

### [C-04] `c-04-listado-y-pruebas` — Integrante 4 (rama `feat/c-04-listado-y-pruebas` desde `feat/c-03-crud-y-ajustes` → merge final a `main`)
- **Estado**: `[x]` completado (archivado en `openspec/changes/archive/2026-11-15-c-04-listado-y-pruebas`)
- **Dependencias**: `C-03`
- **Scope**:
  - `app/modules/insumos/service.py` y `router.py`: `GET /insumos/` paginado, filtrable (`unidad`, `bajo_minimo`, `activo`) antes de contar (`RN-11`), ordenable contra lista blanca (`RN-12`) y validación de rango de página (`RN-10`, Opción A).
  - `test/insumos.http`: casos `C-01` a `C-16` en orden exacto + defensas de la sección 2.13 (Ejercicio 8).
  - `test/test_listado_y_flujo_e2e.py`: suite E2E completa en `pytest`.
- **Leer antes**: `AGENTS.md`, `app/modules/insumos/service.py`, `app/modules/insumos/router.py`.
