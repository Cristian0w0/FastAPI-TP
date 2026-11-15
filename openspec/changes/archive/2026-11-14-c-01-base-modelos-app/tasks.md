# Tasks: C-01 Base, Modelos y Arranque de la App

## 1. Configuración, Higiene Git y Paquetes

- [x] 1.1 Verificar `.gitignore` (excluyendo `.venv/`, `__pycache__/`, `.pytest_cache/`), `requirements.txt` y `pyproject.toml`, comprobando que `python -m pytest --version` reconoce `test/`.
- [x] 1.2 Verificar `AGENTS.md` y `CHANGES.md` con la secuencia `C-01 → C-02 → C-03 → C-04` y la estructura obligatoria de paquetes `app/` y `test/`.

## 2. Modelos de Dominio y Base en Memoria

- [x] 2.1 Implementar `app/modules/insumos/models.py` con `Unidad`, `MotivoAjuste`, `ConflictoInsumoError`, `PaginaFueraDeRangoError` e `Insumo` (con `@property def bajo_minimo`) y verificar los imports desde Python.
- [x] 2.2 Implementar `app/core/database.py` con `InsumosDB`, `crear_base_inicial()` (los 6 insumos iniciales con `Decimal` exacto y `next_id = 7`) y `get_db(request: Request)`.

## 3. Arranque de FastAPI y Tests Base

- [x] 3.1 Implementar `app/main.py` con `lifespan` que carga `app.state.db` una sola vez y verificar que `uvicorn app.main:app` responde `200 OK` en `/docs` y `/openapi.json`.
- [x] 3.2 Crear `test/test_base.py` con `with TestClient(app) as client:` validando la creación única en `lifespan`, los 6 insumos iniciales, `Huevos` en entero `Decimal("60")`, 2 insumos bajo el mínimo y `next_id == 7`, verificando con `pytest -v`.

## Workflow follow-up

- Validar con `openspec validate c-01-base-modelos-app --strict` antes de archivar.
- Archivar el change con `openspec archive c-01-base-modelos-app` y marcar `[x]` en `CHANGES.md`.
