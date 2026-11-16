# Tasks: C-03 CRUD Individual, Comando de Ajuste y Verbos HTTP

## 1. Capa de Servicio Pura (`service.py`)

- [x] 1.1 Implementar `obtener_insumo`, `crear_insumo` y `eliminar_insumo` en `app/modules/insumos/service.py` sin imports HTTP ni reciclaje de IDs.
- [x] 1.2 Implementar `actualizar_insumo` (`exclude_unset=True`, borrado de `codigo_proveedor`, `RN-04` con `ConflictoInsumoError` y normalización entera para `unidad`) y `ajustar_stock_insumo` (`RN-04` y `RN-09` atómicos sin mutar ante error).

## 2. Router HTTP, Registro en App y Pruebas de Integración

- [x] 2.1 Implementar `app/modules/insumos/router.py` con `router = APIRouter(prefix="/insumos", tags=["Insumos"])`, handlers `async def`, `Depends(get_db)`, `response_model=InsumoPublic`, `Location` en `POST` (`201`) y `204` sin cuerpo en `DELETE`, y registrar el router en `app/main.py`.
- [x] 2.2 Crear `test/test_crud_ajustes.py` cubriendo `C-01` a `C-12`, `C-16`, `RN-04` en `PATCH` (`409`), `RN-09` sin mutación y ocultamiento de `codigo_proveedor`, verificando con `python -m pytest -v`.

## 3. Verificación de Servidor

- [x] 3.1 Verificar el arranque real de `uvicorn app.main:app` probando `/docs`, `/openapi.json` y un endpoint `/insumos/2`.

## Workflow follow-up

- Validar con `openspec validate c-03-crud-y-ajustes --strict` antes de archivar.
- Archivar el change con `openspec archive c-03-crud-y-ajustes --yes` y marcar `[x]` en `CHANGES.md`.
