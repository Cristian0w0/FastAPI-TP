# insumos-base Specification

## Purpose
Establece la estructura en capas obligatoria, los modelos del dominio de insumos con soporte para cantidades exactas en `Decimal`, el almacenamiento inicial en memoria con 6 registros semilla y la inicialización única mediante `lifespan` e inyección con `get_db`.

## Requirements

### Requirement: Estructura Obligatoria y Ciclo de Vida de la Aplicación
El sistema SHALL inicializar la base en memoria una única vez durante el arranque mediante `lifespan`, almacenándola en el estado de la aplicación (`app.state`) sin construirla ni importarla globalmente desde los routers.

#### Scenario: Arranque limpio con creación única de la base en memoria
- **WHEN** la aplicación FastAPI inicia su ciclo de vida `lifespan`
- **THEN** crea exactamente una instancia de la base en memoria en `app.state.db` lista para ser inyectada vía `Depends(get_db)`.

### Requirement: Modelo de Dominio Insumo y Propiedad Calculada
El modelo `Insumo` SHALL representar `id`, `nombre`, `unidad` (`kg`, `g`, `l`, `ml`, `unidad`), `stock`, `stock_minimo`, `activo`, `codigo_proveedor` (opcional) y `creado_en` en UTC, calculando `bajo_minimo` en cada lectura como `stock < stock_minimo` sin almacenarlo.

#### Scenario: Cálculo dinámico de bajo_minimo en lectura
- **WHEN** se consulta la propiedad `bajo_minimo` de un insumo cuyo `stock` es menor a su `stock_minimo`
- **THEN** retorna `True`, y retorna `False` si `stock` es mayor o igual a `stock_minimo`.

### Requirement: Datos Iniciales y Contador Monotónico de Identificadores
La base en memoria SHALL arrancar con los 6 insumos iniciales de la consigna (`Harina 000`, `Mozzarella`, `Aceite de girasol`, `Huevos`, `Sal fina`, `Levadura seca`) usando `Decimal` exacto (enteros para `unidad`) y un contador `next_id` inicializado en `7` que nunca reutiliza identificadores borrados.

#### Scenario: Estado semilla al iniciar el servidor
- **WHEN** se crea la base inicial en memoria
- **THEN** contiene exactamente 6 insumos con IDs `1` a `6`, `next_id` igual a `7`, `Huevos` con `stock` `Decimal("60")` y exactamente 2 insumos bajo el mínimo (`Mozzarella` y `Sal fina`).

### Requirement: Separación de Capa de Servicio sin HTTP
Las excepciones de dominio (`ConflictoInsumoError` y `PaginaFueraDeRangoError`) SHALL permitir que la capa de servicio comunique errores de negocio sin importar `HTTPException` ni códigos de estado HTTP.

#### Scenario: Excepciones puras de Python para errores de negocio
- **WHEN** la capa de servicio detecta un conflicto de regla de negocio (`409`) o página fuera de rango (`422`)
- **THEN** dispone de excepciones de dominio independientes de FastAPI/HTTP para que el router las traduzca al código correspondiente.
