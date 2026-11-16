# Design: C-04 Listado Paginado, Filtrado/Orden, Suite .http y Verificación E2E

## Context
Ver `proposal.md` y las specs consolidadas [insumos-base](../../specs/insumos-base/spec.md), [insumos-schemas](../../specs/insumos-schemas/spec.md) e [insumos-crud](../../specs/insumos-crud/spec.md). `models.py` ya define `PaginaFueraDeRangoError` y `schemas.py` ya define `Pagina`. Este change completa `service.py` y `router.py` con `GET /insumos/` y entrega la batería `.http` y E2E en `feat/c-04-listado-y-pruebas`.

## Goals / Non-Goals

**Goals:**
- Implementar `listar_insumos` en `service.py` sin dependencias HTTP, aplicando filtros antes de contar (`RN-11`), Opción A (`RN-10`) y ordenamiento por lista blanca (`RN-12`).
- Exponer `GET /insumos/` en `router.py` con `async def`, `Depends(get_db)`, `Query(...)`, `response_model=Pagina` y traducción de `PaginaFueraDeRangoError` a HTTP `422`.
- Entregar `test/insumos.http` (`C-01` a `C-16` en orden exacto + defensas 2.13) y `test/test_listado_y_flujo_e2e.py`.

**Non-Goals:**
- Modificar el comportamiento de los 5 endpoints individuales de `C-03` ni agregar persistencia en disco/SQL.

## Decisions

### D1: Paginación con filtros vacíos (Opción A) en `listar_insumos`
- **Decisión**: Calcular `pages = math.ceil(total / size) if total > 0 else 0`; permitir `total == 0 and page == 1` devolviendo `200 OK` con `items=[]` y `pages=0`, y lanzar `PaginaFueraDeRangoError` si `(total == 0 and page > 1)` o `(total > 0 and page > pages)`.
- **Razón**: Acordado explícitamente en `PLAN.md` y `AGENTS.md`, evitando `422` ante búsquedas legítimas sin coincidencias en la página `1`.

### D2: Doble defensa de lista blanca para `sort` (`Query(pattern=...)` + mapa en `service.py`)
- **Decisión**: Validar `sort` en `router.py` mediante `Query(default=None, pattern=r"^-?(nombre|stock|creado_en)$")` y mantener un diccionario `CRITERIOS_ORDEN` cerrado en `service.py` (`nombre` usando `casefold()`, `stock` como `Decimal`, `creado_en` como `datetime`).
- **Razón**: `Query(pattern=...)` garantiza `422` automático en FastAPI antes de llegar al handler (`C-14`), mientras `CRITERIOS_ORDEN` evita `getattr` dinámico sobre atributos privados como `codigo_proveedor`.

### D3: Constante `HTTP_422_UNPROCESSABLE_CONTENT` en FastAPI/Starlette
- **Decisión**: Usar `status.HTTP_422_UNPROCESSABLE_CONTENT` al traducir `PaginaFueraDeRangoError` en `router.py`.
- **Razón**: Evita futuros warnings de deprecación de `HTTP_422_UNPROCESSABLE_ENTITY` manteniendo el código HTTP exacto `422`.

## Risks / Trade-offs
- **[Riesgo] Desincronización entre `test/insumos.http` y los IDs mutados durante `C-04`..`C-16`** → **Mitigación**: En `C-04` se crea `id=7` (`Queso rallado`), `C-08` sube `stock_minimo` de `Harina 000` a `15.000` (`< 25.000`), por lo que en `C-13` `?bajo_minimo=true` sigue dando exactamente `total=2`, y en `C-16` el nuevo alta tras borrar `6` recibe `id=8` (distinto de `6`), verificado todo en orden en `test_listado_y_flujo_e2e.py`.
