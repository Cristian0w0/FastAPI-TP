# Design: C-03 CRUD Individual, Comando de Ajuste y Verbos HTTP

## Context
Ver `proposal.md`, [spec insumos-base](../../specs/insumos-base/spec.md) y [spec insumos-schemas](../../specs/insumos-schemas/spec.md). La aplicación ya cuenta con `Insumo`, `Unidad`, `MotivoAjuste`, `ConflictoInsumoError`, `InsumosDB` (con 6 items y `next_id=7`), `get_db`, `app/main.py` y los cinco schemas en `schemas.py`. Este change implementa la capa de negocio individual y su exposición HTTP en la rama `feat/c-03-crud-y-ajustes`.

## Goals / Non-Goals

**Goals:**
- Implementar `obtener_insumo`, `crear_insumo`, `actualizar_insumo`, `ajustar_stock_insumo` y `eliminar_insumo` en `app/modules/insumos/service.py` libres de dependencias HTTP.
- Exponer los 5 endpoints individuales (`GET /{id}`, `POST /`, `PATCH /{id}`, `POST /{id}/ajustes`, `DELETE /{id}`) en `app/modules/insumos/router.py` con `async def`, `Depends(get_db)` y `response_model=InsumoPublic`.
- Registrar el router en `app/main.py` y cubrir `C-01` a `C-12` + `C-16` en `test/test_crud_ajustes.py`.

**Non-Goals:**
- Implementar `GET /insumos/` (listado paginado/filtrado/ordenable), `listar_insumos` ni `test/insumos.http` (corresponden a `C-04`).

## Decisions

### D1: Validación previa a mutar en `actualizar_insumo` y `ajustar_stock_insumo`
- **Decisión**: Verificar `ConflictoInsumoError` (`RN-04` y `RN-09`) antes de aplicar cualquier cambio sobre los atributos del objeto `Insumo`.
- **Razón**: Garantiza que un `PATCH` con múltiples campos o un ajuste inválido (`-5.000` o `-0.5` sobre `unidad`) fallen con `409` de manera atómica, dejando la entidad exactamente como estaba.

### D2: Normalización de enteros `Decimal` para `unidad == "unidad"` en el servicio
- **Decisión**: Reutilizar el criterio de `schemas.py` (`valor % 1 != 0` y `quantize(Decimal("1"))`) en `actualizar_insumo` (para `stock_minimo`) y `ajustar_stock_insumo` (para `datos.cantidad` y `nuevo_stock`) cuando `insumo.unidad == Unidad.unidad`.
- **Razón**: Si un cliente envía `"35.000"` en `PATCH` o un ajuste entero sobre `Huevos` (`60`), se acepta como entero válido y continúa serializando como entero sin decimales (`"35"`, `"50"`), mientras que `"35.5"` o `"-0.5"` disparan `ConflictoInsumoError` → `409`.

### D3: Respuesta `204 No Content` sin cuerpo en `DELETE`
- **Decisión**: El handler `eliminar` retorna `Response(status_code=status.HTTP_204_NO_CONTENT)`.
- **Razón**: Evita serialización JSON accidental y asegura que la respuesta `204` cumpla estrictamente con la consigna (*"204 sin cuerpo al borrar"*).

### D4: Encabezado `Location` relativo al recurso creado
- **Decisión**: En `POST /insumos/`, fijar `response.headers["Location"] = f"/insumos/{creado.id}"` devolviendo el recurso serializado con `status_code=201`.
- **Razón**: Coincide literalmente con el ejemplo de la consigna (`Location: /insumos/7`).

## Risks / Trade-offs
- **[Riesgo] En memoria compartida durante pruebas secuenciales** → **Mitigación**: Cada función de prueba en `test/test_crud_ajustes.py` crea su propia sesión `with TestClient(app) as client:` para ejecutar el `lifespan` desde la semilla limpia de 6 insumos.
