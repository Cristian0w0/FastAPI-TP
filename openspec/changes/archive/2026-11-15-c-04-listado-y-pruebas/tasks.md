# Tasks: C-04 Listado Paginado, Filtrado/Orden, Suite .http y Verificación E2E

## 1. Listado en Servicio y Router (`GET /insumos/`)

- [x] 1.1 Implementar `listar_insumos` en `app/modules/insumos/service.py` (sin imports HTTP) con filtros previos al conteo (`RN-11`), Opción A de paginación (`RN-10`) y ordenamiento por lista blanca (`RN-12`).
- [x] 1.2 Añadir `GET /insumos/` (`async def`, `Depends(get_db)`, `response_model=Pagina`, `Query` con validación `RN-10`/`RN-12` y captura de `PaginaFueraDeRangoError` → `422`) en `app/modules/insumos/router.py`.

## 2. Suite `.http` y Verificación E2E

- [x] 2.1 Crear `test/insumos.http` con los casos `C-01` a `C-16` en orden exacto desde servidor limpio, comentarios de resultado esperado y defensas 2.13 (Ejercicio 8).
- [x] 2.2 Crear `test/test_listado_y_flujo_e2e.py` probando filtros, orden, `RN-10` Opción A, `RN-11`, `RN-12` y la secuencia E2E completa `C-01` → `C-16`, verificando con `python -m pytest -v`.

## 3. Verificación Integral del Servidor

- [x] 3.1 Verificar `uvicorn app.main:app` probando `/docs`, `/openapi.json` (6 endpoints publicados sin `PUT`) y una corrida E2E real contra el servidor HTTP.

## Workflow follow-up

- Validar con `openspec validate c-04-listado-y-pruebas --strict` antes de archivar.
- Archivar el change con `openspec archive c-04-listado-y-pruebas --yes` y marcar `[x]` en `CHANGES.md`.
