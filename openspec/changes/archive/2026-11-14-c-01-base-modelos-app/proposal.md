# Proposal: C-01 Base, Modelos y Arranque de la App

## Why
El TP de la unidad FastAPI ("Los insumos de la cocina") requiere construir una API REST en FastAPI con persistencia exclusivamente en memoria y una arquitectura en capas obligatoria. Antes de implementar los schemas de validación, los endpoints CRUD o la suite `.http`, los 4 integrantes necesitan una base común en `main` con el entorno configurado, los modelos de dominio congelados, el almacenamiento inicial en memoria y el ciclo de vida de la aplicación verificado.

## What Changes
- **Higiene del repositorio y configuración Python**: Creación de `.gitignore` (bloqueando `.venv/`, `__pycache__/` y `.pytest_cache/`), `requirements.txt` (`fastapi[standard]`, `pytest`, `httpx`) y `pyproject.toml` para la configuración de `pytest`.
- **Gobernanza OpenSpec (`opsx`)**: Incorporación de `AGENTS.md` y `CHANGES.md` con la secuencia estricta `C-01 → C-02 → C-03 → C-04`.
- **Modelos y excepciones de dominio (`app/modules/insumos/models.py`)**: Definición de `Unidad`, `MotivoAjuste`, modelo `Insumo` con propiedad calculada `bajo_minimo` y excepciones propias `ConflictoInsumoError` y `PaginaFueraDeRangoError`.
- **Base en memoria (`app/core/database.py`)**: Implementación de `InsumosDB` con los 6 insumos iniciales, contador `next_id = 7` (sin reutilización de IDs) y dependencia `get_db`.
- **Aplicación FastAPI (`app/main.py`)**: Inicialización de `FastAPI` con `lifespan` que crea `app.state.db` una sola vez al arrancar.
- **Pruebas base (`test/test_base.py`)**: Verificación con `pytest` y `TestClient` del `lifespan`, los 6 registros iniciales y el cálculo de `bajo_minimo`.

### Fuera de alcance
- No se implementan aún `schemas.py`, `service.py`, `router.py`, `README.md` ni `test/insumos.http` (corresponden a `C-02`, `C-03` y `C-04`).
- No hay base de datos SQL, autenticación ni formato RFC 9457 (fuera del TP según consigna).

## Capabilities

### New Capabilities
- `insumos-base`: Estructura base del proyecto FastAPI en capas, modelos de dominio de insumos con `Decimal` y enumeraciones, base en memoria inicializada en `lifespan` e inyección vía `Depends(get_db)`.

### Modified Capabilities
*(Ninguna; este es el primer change del proyecto.)*

## Impact
- **Archivos nuevos**: `.gitignore`, `requirements.txt`, `pyproject.toml`, `AGENTS.md`, `CHANGES.md`, `app/__init__.py`, `app/core/__init__.py`, `app/core/database.py`, `app/modules/__init__.py`, `app/modules/insumos/__init__.py`, `app/modules/insumos/models.py`, `app/main.py`, `test/__init__.py`, `test/test_base.py`.
- **Dependencias**: Python >= 3.12, `fastapi[standard]>=0.111.0`, `pytest>=8.0.0`, `httpx>=0.27.0`.
- **Consumidores posteriores**: Desbloquea directamente a `C-02` (`schemas.py`), `C-03` (`service.py` + `router.py`) y `C-04` (`GET /insumos/` + `.http`).
