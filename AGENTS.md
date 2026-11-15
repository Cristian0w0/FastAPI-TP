# Los insumos de la cocina — Instrucciones para Agentes y Equipo

> Este archivo es la referencia principal al entrar al repositorio.
> La fuente de verdad de los requisitos es [TP_Cap2_Consigna.pdf](TP_Cap2_Consigna.pdf) y el plan maestro está en [PLAN.md](PLAN.md).

---

## Stack Técnico

| Capa | Tecnología | Versión / Criterio |
|---|---|---|
| Lenguaje | Python | `>= 3.12` |
| Framework API | FastAPI | `>= 0.111` (todos los handlers con `async def`) |
| Validación / Contrato | Pydantic v2 | Viene con `fastapi[standard]` |
| Servidor ASGI | Uvicorn | Local en `/docs` (sin deploy remoto) |
| Persistencia | Lista en memoria | `app.state.db` inicializada en `lifespan` |
| Tests | `pytest` + `.http` | `test/test_*.py` + `test/insumos.http` |

---

## Estructura Obligatoria del Proyecto

```text
app/
├── main.py                      # FastAPI, lifespan y registro del router
├── core/
│   └── database.py              # InsumosDB en memoria, seed inicial (6 items) y get_db
└── modules/
    └── insumos/
        ├── models.py            # Unidad, MotivoAjuste, Insumo y excepciones de dominio
        ├── schemas.py           # InsumoCreate, InsumoUpdate, AjusteCreate, InsumoPublic, Pagina
        ├── service.py           # Lógica pura sin HTTP (devuelve datos, None o error propio)
        └── router.py            # Rutas HTTP async def con Depends(get_db) y response_model
test/
├── insumos.http                 # Casos C-01 a C-16 en orden + defensas 2.13
└── test_*.py                    # Suite pytest con TestClient
```

---

## Reglas Duras del Proyecto

1. **Sin base de datos, sin autenticación y sin RFC 9457**: Los errores HTTP salen exclusivamente con `HTTPException` y su `detail`.
2. **Aislamiento de `service.py`**: `app/modules/insumos/service.py` **NUNCA** importa `fastapi`, `HTTPException` ni códigos de estado HTTP. Comunica ausencias devolviendo `None` (o `bool`) y conflictos/bordes mediante `ConflictoInsumoError` / `PaginaFueraDeRangoError`.
3. **Todos los handlers del router son `async def`** y reciben la base con `Depends(get_db)`.
4. **Cantidades con `Decimal`, nunca `float`**:
   * Máximo 12 dígitos y 3 decimales (`RN-03`); una cantidad con 4 decimales se rechaza (`422`), no se redondea.
   * Si `unidad == "unidad"`, solo se admiten enteros (`valor % 1 == 0`) y se normaliza como `Decimal` entero sin `.000` (`"60"`, `"30"`, `"12"`).
5. **Seguridad del contrato**:
   * `codigo_proveedor` (`^[A-Z]{3}-\d{4}$`) se guarda internamente pero **nunca** aparece en `InsumoPublic` (`RN-05`).
   * Schemas de entrada con `extra="forbid"` (`RN-06`).
   * `PATCH` usa `model_dump(exclude_unset=True)`; `null` solo es válido en `codigo_proveedor` (`RN-07`).
   * Los IDs eliminados **no se reutilizan**.
   * `GET /insumos/` con filtros vacíos (`total == 0`) y `page == 1` devuelve `200` (`items: []`, `pages: 0`); `page >= 2` con `total == 0` o `page > pages` devuelve `422` (`RN-10`, Opción A).
6. **Higiene Git**: NUNCA commitear `.venv/`, `__pycache__/` ni `.pytest_cache/`.
7. **Dependencias estrictas de OpenSpec (`CHANGES.md`)**: NUNCA proponer (`/opsx:propose`) ni implementar un change cuyo predecesor no esté archivado en `openspec/changes/archive/` y marcado con `[x]` en [CHANGES.md](CHANGES.md).

---

## Flujo de Trabajo OpenSpec (`opsx`) y Ramas Secuenciales

Repositorio remoto: `https://github.com/Cristian0w0/FastAPI-TP`

```text
1. Leer CHANGES.md y confirmar que el change anterior esté [x] y archivado
2. Posicionarse en la rama correspondiente (Integrante 1 en main; 2→3→4 en cadena)
3. /opsx:propose c-0X-nombre         → proposal.md + specs/ + design.md + tasks.md
4. /opsx:apply c-0X-nombre           → implementar código + tests
5. Verificar con pytest -v y uvicorn
6. /opsx:archive c-0X-nombre         → archivar y marcar [x] en CHANGES.md
7. Commit y push de la rama (Integrante 4 realiza el merge final a main)
```
