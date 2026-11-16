# Proposal: C-03 CRUD Individual, Comando de Ajuste y Verbos HTTP

## Why
Con el modelo de dominio en memoria (`C-01`) y el contrato completo de schemas y validadores Pydantic v2 (`C-02`) ya archivados, la API todavía no expone endpoints ni reglas de negocio de persistencia en memoria. Es necesario implementar la capa de servicio pura (`service.py`), las rutas individuales y el comando de ajuste (`router.py`), y conectarlas en `app/main.py` para habilitar las operaciones de consulta puntual, alta, actualización parcial, ajuste de stock y borrado.

## What Changes
- **Capa de servicio sin HTTP (`app/modules/insumos/service.py`)**:
  - `obtener_insumo`: búsqueda puntual por `id` devolviendo `Insumo | None`.
  - `crear_insumo`: alta usando `db.next_id` sin reutilización, asignando `creado_en` en UTC.
  - `actualizar_insumo`: actualización parcial con `model_dump(exclude_unset=True)`, borrado de `codigo_proveedor` con `None`, validación de `RN-04` (`stock_minimo` entero para `unidad == "unidad"`) lanzando `ConflictoInsumoError` (`409`) y normalización a `Decimal` entero.
  - `ajustar_stock_insumo`: comando que valida `RN-04` (`unidad == "unidad"` no admite decimales -> `ConflictoInsumoError`) y `RN-09` (`stock + cantidad < 0` -> `ConflictoInsumoError` sin mutar el insumo), aplicando el ajuste y normalizando `unidad` a entero `Decimal`.
  - `eliminar_insumo`: elimina el registro de `db.items` devolviendo `bool` sin decrementar ni reciclar `db.next_id`.
- **Capa HTTP (`app/modules/insumos/router.py`)**:
  - `APIRouter(prefix="/insumos", tags=["Insumos"])` con todos los handlers `async def` recibiendo `Depends(get_db)` y declarando `response_model=InsumoPublic` en las respuestas con cuerpo:
    - `GET /insumos/{insumo_id}` (`200`, `404`, `422`).
    - `POST /insumos/` (`201` con header `Location: /insumos/{id}`, `422`).
    - `PATCH /insumos/{insumo_id}` (`200`, `404`, `409`, `422`).
    - `POST /insumos/{insumo_id}/ajustes` (`200`, `404`, `409`, `422`).
    - `DELETE /insumos/{insumo_id}` (`204` sin cuerpo, `404`).
  - Sin endpoint `PUT`.
- **Registro de router (`app/main.py`)**:
  - Importar y registrar `insumos_router` mediante `app.include_router(insumos_router)`.
- **Pruebas de endpoints (`test/test_crud_ajustes.py`)**:
  - Suite `pytest` con `TestClient(app)` verificando los casos `C-01` a `C-12`, `C-16`, `RN-04` en `PATCH` (`409`), `RN-09` sin mutación y ocultamiento de `codigo_proveedor`.

### Fuera de alcance
- El endpoint de listado paginado, filtrable y ordenable (`GET /insumos/`), `listar_insumos`, `test/insumos.http` y `test/test_listado_y_flujo_e2e.py` pertenecen a `C-04`.
- No hay base de datos SQL, autenticación ni formato de error RFC 9457 (solo `HTTPException` y `detail`).

## Capabilities

### New Capabilities
- `insumos-crud`: Operaciones CRUD individuales (`GET /{id}`, `POST /`, `PATCH /{id}`, `DELETE /{id}`) y comando `POST /{id}/ajustes` separadas en `service.py` (puro Python) y `router.py` (`async def`, códigos HTTP exactos y `Location`).

### Modified Capabilities
*(Ninguna; `insumos-base` y `insumos-schemas` permanecen intactas.)*

## Impact
- **Archivos nuevos**: `app/modules/insumos/service.py`, `app/modules/insumos/router.py`, `test/test_crud_ajustes.py`.
- **Archivos modificados**: `app/main.py`.
- **Consumidores**: `C-04` extenderá `service.py` y `router.py` para añadir `GET /insumos/` y los archivos `.http`.
