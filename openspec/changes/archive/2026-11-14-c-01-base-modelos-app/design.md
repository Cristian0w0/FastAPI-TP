# Design: C-01 Base, Modelos y Arranque de la App

## Context
Ver `proposal.md` para la motivación. El repositorio arranca únicamente con la consigna PDF y `PLAN.md`. Los 4 integrantes trabajarán secuencialmente por ramas en GitHub (`main` → `C-02` → `C-03` → `C-04` → merge a `main`), por lo que `C-01` debe fijar nombres de tipos, excepciones y firmas de dependencia definitivos.

## Goals / Non-Goals

**Goals:**
- Alinear el proyecto a la estructura obligatoria (`app/main.py`, `app/core/database.py`, `app/modules/insumos/models.py`, `test/`).
- Configurar higiene Git (`.gitignore` bloqueando `.venv/`, `__pycache__/` y `.pytest_cache/`) y dependencias (`requirements.txt`, `pyproject.toml`).
- Dejar funcionando `lifespan` + `app.state.db` + `get_db` y el seed exacto de 6 insumos.
- Definir `Unidad`, `MotivoAjuste`, `Insumo`, `ConflictoInsumoError` y `PaginaFueraDeRangoError` como contrato interno para `C-02`, `C-03` y `C-04`.

**Non-Goals:**
- Implementar schemas Pydantic (`C-02`), lógica CRUD/ajustes (`C-03`) o listado `.http` (`C-04`).
- Configurar Docker, base de datos SQL o despliegues remotos.

## Decisions

### D1: `Insumo` como `@dataclass` con propiedad `@property def bajo_minimo`
- **Decisión**: Modelar `Insumo` en `app/modules/insumos/models.py` con `@dataclass` y calcular `bajo_minimo` como `@property` (`self.stock < self.stock_minimo`).
- **Razón**: Evita almacenar un estado derivado que podría quedar desactualizado tras un `PATCH` o ajuste, y funciona directo con `ConfigDict(from_attributes=True)` de `InsumoPublic` en `C-02`.
- **Alternativas**: Diccionarios planos (`dict`). Descartado por falta de tipado fuerte, autocompletado e invariantes claros entre los 4 integrantes.

### D2: `InsumosDB` en `app.state.db` + `get_db(request: Request)`
- **Decisión**: `app/core/database.py` expone `InsumosDB(items, next_id)`, `crear_base_inicial()` y `get_db(request: Request) -> InsumosDB`, mientras `app/main.py` inicializa `app.state.db` dentro de `@asynccontextmanager async def lifespan(app: FastAPI)`.
- **Razón**: Cumple el Ejercicio 1 (el router no construye ni importa una lista global, sino que la recibe vía `Depends(get_db)`) y aísla el estado entre corridas de `with TestClient(app) as client:`.
- **Alternativas**: Lista global a nivel de módulo en `database.py`. Descartado porque violaría la consigna y contaminaría el estado entre tests.

### D3: Cantidades iniciales con `Decimal` textual exacto
- **Decisión**: Inicializar insumos continuos (`kg`, `l`, `g`) con 3 decimales exactos (ej. `Decimal("25.000")`) y `Huevos` (`unidad`) con enteros (`Decimal("60")`, `Decimal("30")`), usando `datetime.now(timezone.utc)` para `creado_en`.
- **Razón**: Mantiene compatibilidad exacta con `RN-03`, `RN-04` y la tabla de datos iniciales de la consigna.

### D4: Excepciones propias de dominio para aislar `service.py`
- **Decisión**: Definir `ConflictoInsumoError` (para reglas 409 en PATCH/ajustes) y `PaginaFueraDeRangoError` (para página fuera de rango 422 en listado) en `models.py`.
- **Razón**: Permite que `service.py` (en `C-03` y `C-04`) permanezca 100% libre de imports de FastAPI/HTTP.

## Risks / Trade-offs
- **[Riesgo] `pytest` sin `TestClient` como context manager no dispara `lifespan`** → **Mitigación**: Documentar en `AGENTS.md` y usar siempre `with TestClient(app) as client:` en `test/test_*.py`.
- **[Riesgo] Subir accidentalmente `.venv/` o cachés de Python al hacer `git add .`** → **Mitigación**: Incluir `.venv/`, `__pycache__/` y `.pytest_cache/` en `.gitignore` desde el primer commit.
