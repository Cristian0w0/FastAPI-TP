# Spec Delta: insumos-crud

## Purpose
Define el comportamiento de la capa de servicio pura y los endpoints HTTP individuales y de ajuste de stock (`GET /insumos/{id}`, `POST /insumos/`, `PATCH /insumos/{id}`, `POST /insumos/{id}/ajustes`, `DELETE /insumos/{id}`), garantizando los códigos de estado esperados, las reglas `RN-04`, `RN-05`, `RN-07` y `RN-09`, la no reutilización de identificadores y los casos `C-01` a `C-12` y `C-16`.

## ADDED Requirements

### Requirement: Aislamiento de Service sin Dependencias HTTP
El módulo `app/modules/insumos/service.py` SHALL implementar todas las operaciones CRUD individuales y de ajuste de stock en Python puro sin importar `fastapi`, `HTTPException` ni códigos de estado HTTP, comunicando ausencias con `None` o `False` y conflictos de negocio con `ConflictoInsumoError`.

#### Scenario: Comunicación de ausencia y conflicto sin HTTPException
- **WHEN** `service.py` intenta operar sobre un `insumo_id` inexistente o detecta un conflicto de regla de negocio (`RN-04`, `RN-09`)
- **THEN** devuelve `None`/`False` o lanza `ConflictoInsumoError` sin depender de objetos HTTP ni mutar el estado guardado ante error.

### Requirement: Consulta Puntual, Alta con Location y Borrado sin Reutilizar IDs
Los endpoints `GET /insumos/{id}`, `POST /insumos/` y `DELETE /insumos/{id}` SHALL ejecutarse con handlers `async def`, inyectar la base vía `Depends(get_db)`, usar `response_model=InsumoPublic` en las respuestas con cuerpo, devolver `201 Created` con encabezado `Location: /insumos/{id}` al crear, `204 No Content` sin cuerpo al borrar y nunca reutilizar identificadores eliminados (`C-01` a `C-07`, `C-16`).

#### Scenario: Alta con nombre normalizado, Location y ocultamiento de proveedor (C-03, C-04)
- **WHEN** se envía un `POST /insumos/` válido con `"  Queso   rallado  "` y `codigo_proveedor="QUE-0007"` o se consulta `GET /insumos/2`
- **THEN** responde `201 Created` con header `Location: /insumos/7` y el nombre normalizado `"Queso rallado"`, y ninguna respuesta incluye `codigo_proveedor`.

#### Scenario: ID inválido, ID inexistente y borrado sin reciclaje de IDs (C-01, C-02, C-16)
- **WHEN** se solicita `GET /insumos/abc`, `GET /insumos/99`, o se ejecuta dos veces `DELETE /insumos/6` seguido de un `POST /insumos/`
- **THEN** responde `422` sin ejecutar el handler en `/insumos/abc`, `404` en `/insumos/99`, `204` sin cuerpo y luego `404` en el doble borrado, y `201` con un `id` igual a `7` (nunca `6`) en el nuevo alta.

### Requirement: Actualización Parcial Segura en PATCH (RN-04, RN-06, RN-07)
El endpoint `PATCH /insumos/{id}` SHALL aplicar únicamente los campos enviados mediante `model_dump(exclude_unset=True)`, borrar `codigo_proveedor` si llega `null`, rechazar con `422` `null` en otros campos o campos prohibidos (`stock`, `unidad`), y responder `409 Conflict` si se envía `stock_minimo` con decimales sobre un insumo cuya unidad guardada es `"unidad"`.

#### Scenario: Modificación parcial, borrado de código y conflicto con unidad entera (C-08, C-09, C-10)
- **WHEN** se envía `PATCH /insumos/1` solo con `stock_minimo`, luego `{"codigo_proveedor": null}`, después `{"nombre": null}` o `{"stock": "10.000"}`, o un `PATCH /insumos/4` (Huevos) con `stock_minimo="30.5"`
- **THEN** responde `200` manteniendo intactos los campos omitidos, `200` borrando el código, `422` ante `nombre: null` o `stock`, y `409` sin modificar el insumo cuando el mínimo decimal choca con `unidad="unidad"`.

### Requirement: Comando de Ajuste de Stock con Reglas RN-04 y RN-09
El endpoint `POST /insumos/{id}/ajustes` SHALL funcionar como un comando que suma `cantidad` al `stock` devolviendo `200 OK` con `InsumoPublic`, responder `404` si el insumo no existe, y responder `409 Conflict` sin modificar el stock si el resultado sería negativo (`RN-09`) o si se intenta ajustar con decimales un insumo medido en `"unidad"` (`RN-04`).

#### Scenario: Ajuste válido seguido de ajuste negativo o decimal sobre unidad entera (C-11, C-12)
- **WHEN** sobre Mozzarella (`stock="3.500"`) se envía `{"cantidad": "-1.250", "motivo": "consumo"}` y luego `{"cantidad": "-5.000", "motivo": "consumo"}`, o sobre Huevos se envía `{"cantidad": "-0.5", "motivo": "merma"}`
- **THEN** el primer ajuste responde `200` con `stock="2.250"`, y tanto el ajuste que dejaría stock negativo como el decimal sobre Huevos responden `409` manteniendo intacto el stock guardado.
