# Spec Delta: insumos-listado

## Purpose
Define el comportamiento de `GET /insumos/` (paginación `RN-10`, filtrado previo al conteo `RN-11`, ordenamiento contra lista blanca `RN-12` y ocultamiento de `codigo_proveedor` `RN-05`), junto con la suite secuencial `test/insumos.http` y las defensas de contrato del Ejercicio 8 (`C-01` a `C-16`).

## ADDED Requirements

### Requirement: Filtrado Previo al Conteo y Ocultamiento en Listado (RN-05, RN-11)
El servicio `listar_insumos` y el endpoint `GET /insumos/` SHALL aplicar los filtros opcionales (`unidad`, `bajo_minimo`, `activo`) antes de calcular `total` y `pages`, devolviendo un objeto `Pagina` cuyos elementos `InsumoPublic` nunca exponen `codigo_proveedor`, y rechazando valores de `unidad` fuera de `Unidad` con `422`.

#### Scenario: Conteo filtrado con bajo_minimo y rechazo de unidad inválida (C-13)
- **WHEN** se consulta `GET /insumos/?bajo_minimo=true` sobre los 6 insumos iniciales (incluso tras el alta de `C-04` y el `PATCH` de `C-08`) o `GET /insumos/?unidad=docena`
- **THEN** el primer caso responde `200 OK` con `total=2` (`Mozzarella` y `Sal fina`) sin `codigo_proveedor` en ningún item, y el segundo responde `422`.

### Requirement: Paginación por Defecto, Límites y Opción A para Vacíos (RN-10)
El endpoint `GET /insumos/` SHALL aceptar `page >= 1` (por defecto `1`) y `1 <= size <= 100` (por defecto `20`), devolviendo `items`, `total`, `page`, `size` y `pages`; si los filtros dejan `total == 0` y `page == 1`, SHALL responder `200 OK` con `items=[]` y `pages=0`, mientras que `page >= 2` con `total == 0` o `page > pages` con `total > 0` SHALL responder `422`.

#### Scenario: Página más allá de la última y resultado vacío filtrado (C-15)
- **WHEN** se consulta `GET /insumos/?page=9`, `GET /insumos/?unidad=ml&page=1` o `GET /insumos/?unidad=ml&page=2`
- **THEN** `?page=9` y `?unidad=ml&page=2` responden `422`, mientras que `?unidad=ml&page=1` responde `200 OK` con `items=[]`, `total=0`, `page=1` y `pages=0`.

### Requirement: Ordenamiento Seguro contra Lista Blanca (RN-12)
El endpoint `GET /insumos/` SHALL aceptar `sort` únicamente para `nombre`, `stock` o `creado_en` con prefijo opcional `-` para orden descendente, comparando `stock` numéricamente como `Decimal`, y rechazando cualquier otro campo (como `codigo_proveedor`) con `422`.

#### Scenario: Orden descendente por stock combinado con filtro y rechazo de campo interno (C-14)
- **WHEN** se consulta `GET /insumos/?unidad=kg&sort=-stock` o `GET /insumos/?sort=codigo_proveedor`
- **THEN** el primero responde `200 OK` ordenado por `stock` `Decimal` descendente y el segundo responde `422`.

### Requirement: Suite Reproducible .http y Flujo Secuencial C-01 a C-16
El proyecto SHALL incluir `test/insumos.http` con los casos `C-01` a `C-16` en orden exacto (con comentarios de respuesta esperada y defensas del Ejercicio 8), y `test/test_listado_y_flujo_e2e.py` verificando la ejecución secuencial completa desde el estado semilla.

#### Scenario: Ejecución secuencial completa C-01 a C-16 en estado semilla limpio
- **WHEN** se ejecutan los casos `C-01` a `C-16` en orden exacto desde el arranque limpio de la aplicación
- **THEN** cada petición reproduce los códigos, headers (`Location: /insumos/7`), cuerpos esperados, `total=2` en `C-13` y alta con `id=8` (nunca `6`) en `C-16`.
