# Proposal: C-04 Listado Paginado, Filtrado/Orden, Suite .http y Verificación E2E

## Why
Con la base en memoria (`C-01`), los contratos Pydantic (`C-02`) y los endpoints CRUD individuales más ajustes (`C-03`) completados, falta implementar el endpoint de listado `GET /insumos/` con paginación, filtros y ordenamiento seguro, además de la batería reproducible `test/insumos.http` (`C-01` a `C-16` en orden exacto) y la verificación E2E integral del trabajo práctico.

## What Changes
- **Servicio de listado (`app/modules/insumos/service.py`)**:
  - Incorporar `listar_insumos` en Python puro (sin dependencias HTTP):
    - Filtrado previo al conteo (`RN-11`) por `unidad`, `bajo_minimo` y `activo`.
    - Paginación (`RN-10`, Opción A): cálculo de `total` y `pages`; si `total == 0` y `page == 1`, responde vacío con `pages = 0` (`200`); si `(total == 0 and page > 1)` o `(total > 0 and page > pages)`, lanza `PaginaFueraDeRangoError` (`422`).
    - Ordenamiento contra lista blanca (`RN-12`) sobre `nombre`, `stock` y `creado_en` en orden ascendente o descendente (`-campo`).
- **Endpoint de listado (`app/modules/insumos/router.py`)**:
  - Añadir `@router.get("/", response_model=Pagina)` con handler `async def` e inyección `Depends(get_db)`.
  - Declarar parámetros `Query` con validaciones de rango/patrón (`page >= 1`, `1 <= size <= 100`, `sort` con `^-?(nombre|stock|creado_en)$`, `unidad: Unidad | None`, `bajo_minimo: bool | None`, `activo: bool | None`).
  - Traducir `PaginaFueraDeRangoError` a `HTTPException` `422`.
- **Casos `.http` (`test/insumos.http`)**:
  - Reproducir en orden exacto `C-01` a `C-16` desde servidor recién arrancado con comentarios de respuesta esperada, más casos de defensa de la sección 2.13 (Ejercicio 8).
- **Suite E2E (`test/test_listado_y_flujo_e2e.py`)**:
  - Pruebas de filtros combinados, orden asc/desc, `RN-10` (Opción A), `RN-11`, `RN-12`, ocultamiento de `codigo_proveedor` en listados y ejecución secuencial completa `C-01` → `C-16`.

### Fuera de alcance
- No hay base de datos SQL, autenticación ni formato de error RFC 9457 (solo `HTTPException` y `detail`).
- No hay endpoint `PUT`.

## Capabilities

### New Capabilities
- `insumos-listado`: Listado paginado, filtrable antes de contar (`RN-11`) y ordenable contra lista blanca (`RN-12`) en `GET /insumos/` (`Pagina`, Opción A para vacíos), junto con la suite `test/insumos.http` y verificación E2E `C-01` a `C-16`.

### Modified Capabilities
*(Ninguna; `insumos-base`, `insumos-schemas` e `insumos-crud` permanecen intactas.)*

## Impact
- **Archivos modificados**: `app/modules/insumos/service.py`, `app/modules/insumos/router.py`.
- **Archivos nuevos**: `test/insumos.http`, `test/test_listado_y_flujo_e2e.py`.
- **Resultado final**: Contrato completo de 6 endpoints publicado en `/docs` y verificado con `pytest -v`, `uvicorn` y `.http`, listo para merge final en `main`.
