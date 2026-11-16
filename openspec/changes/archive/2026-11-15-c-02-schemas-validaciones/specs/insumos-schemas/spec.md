# Spec Delta: insumos-schemas

## Purpose
Define el contrato de validación y serialización en Pydantic v2 mediante cinco schemas segregados (`InsumoCreate`, `InsumoUpdate`, `AjusteCreate`, `InsumoPublic` y `Pagina`), garantizando `RN-01` a `RN-08` y la exclusión de datos internos en las respuestas.

## ADDED Requirements

### Requirement: Normalización y Restricciones de Nombre (RN-01)
Los schemas `InsumoCreate` e `InsumoUpdate` SHALL validar `nombre` de 1 a 80 caracteres recortando espacios en los extremos y colapsando espacios internos repetidos a uno, rechazando nombres vacíos o compuestos solo por espacios.

#### Scenario: Normalización de espacios y rechazo de nombre en blanco
- **WHEN** se valida `"  Queso   rallado  "` en `InsumoCreate` o `InsumoUpdate`
- **THEN** se guarda normalizado como `"Queso rallado"`, y si se envía `"   "` o `""` se rechaza con error de validación (`422`).

### Requirement: Cantidades Exactas con Decimal y Enteros por Unidad (RN-02, RN-03, RN-04)
Las cantidades SHALL declararse como `Decimal` (nunca `float`) con máximo 12 dígitos totales, hasta 3 decimales sin redondeo automático y `>= 0` para `stock` y `stock_minimo`, serializándose en JSON como texto; en `InsumoCreate`, si `unidad` es `"unidad"`, `stock` y `stock_minimo` SHALL ser enteros y normalizarse sin decimales.

#### Scenario: Rechazo de cuatro decimales y decimales en unidad entera
- **WHEN** se envía `stock` con `"1.2345"` o un alta con `unidad="unidad"` y `stock="12.5"`
- **THEN** Pydantic rechaza la entrada con error de validación (`422`) sin redondear ni aceptar fracciones.

#### Scenario: Múltiples errores simultáneos de contrato en alta
- **WHEN** se envía un alta con `nombre=""`, `unidad="docena"` y `stock=-1`
- **THEN** el `ValidationError` reporta los tres errores de campo en la misma respuesta (`422`).

### Requirement: Contrato Estricto y Ocultamiento de Código de Proveedor (RN-05, RN-06)
Todos los schemas de entrada (`InsumoCreate`, `InsumoUpdate`, `AjusteCreate`) SHALL configurarse con `extra="forbid"`, validar `codigo_proveedor` con patrón `^[A-Z]{3}-\d{4}$` cuando esté presente, y `InsumoPublic` SHALL omitir `codigo_proveedor` e incluir `bajo_minimo`.

#### Scenario: Campos prohibidos en entrada y exclusión en salida
- **WHEN** se envía `id` en `InsumoCreate` o `stock`/`unidad` en `InsumoUpdate`
- **THEN** se rechaza con error de validación (`422`), mientras que `InsumoPublic.model_validate(insumo)` nunca expone `codigo_proveedor`.

### Requirement: Actualización Parcial y Manejo de Null en PATCH (RN-07)
El schema `InsumoUpdate` SHALL aceptar campos opcionales excluyendo `unidad` y `stock`, permitiendo `null` únicamente en `codigo_proveedor` y rechazando `null` explícito en `nombre`, `stock_minimo` y `activo`.

#### Scenario: Borrado de código de proveedor frente a null inválido
- **WHEN** se envía `{"codigo_proveedor": null}` en `InsumoUpdate`
- **THEN** es válido y `model_dump(exclude_unset=True)` conserva `{"codigo_proveedor": None}`, mientras que `{"nombre": null}`, `{"stock_minimo": null}` o `{"activo": null}` fallan con error de validación (`422`).

### Requirement: Validación de Ajustes de Stock y Envoltorio Paginado (RN-08, RN-10)
El schema `AjusteCreate` SHALL exigir `motivo` en `MotivoAjuste` y `cantidad` `Decimal` distinta de cero (`> 0` para `compra`, `< 0` para `consumo` y `merma`, `!= 0` para `correccion`), y `Pagina` SHALL envolver `items`, `total`, `page`, `size` y `pages`.

#### Scenario: Regla de signo según motivo de ajuste
- **WHEN** se intenta crear `AjusteCreate` con `cantidad="0"`, `compra` negativa o `consumo`/`merma` positivos
- **THEN** la validación falla con error de contrato (`422`), aceptando `correccion` tanto positiva como negativa distinta de cero.
