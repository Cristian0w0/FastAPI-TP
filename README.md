# Los insumos de la cocina — API REST con FastAPI

Trabajo Práctico de la **Unidad FastAPI (Contratos: schemas, validación y CRUD)** de Programación III (UTN).
Implementa un contrato completo con FastAPI y Pydantic v2 sobre almacenamiento en memoria (sin base de datos SQL, sin autenticación y sin formato RFC 9457).

---

## Instalación y ejecución local

Con Python `>= 3.12` instalado:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Levantar el servidor local y abrir la documentación interactiva en `/docs`:

```powershell
uvicorn app.main:app --reload
```

* Swagger UI: `http://127.0.0.1:8000/docs`
* Pruebas automatizadas:

```powershell
pytest -v
```

---

## Por qué se separa el modelo guardado de los schemas de entrada y salida

En el proyecto se utilizan piezas distintas para representar lo que se guarda y lo que viaja por HTTP porque cada una cumple un rol diferente en el contrato:

1. **Modelo de dominio (`Insumo` en `app/modules/insumos/models.py`)**: representa el estado interno completo almacenado en memoria, incluyendo datos privados como `codigo_proveedor` y campos controlados por el servidor (`id`, `creado_en`), sin almacenar atributos derivados como `bajo_minimo`.
2. **Schemas de entrada (`InsumoCreate`, `InsumoUpdate`, `AjusteCreate`)**: definen estrictamente qué puede enviar el cliente en cada operación (`extra="forbid"`), impidiendo que fije `id`, `creado_en` o `bajo_minimo`, excluyendo `unidad` y `stock` en el `PATCH`, y ejecutando validaciones sintácticas y de coherencia antes de llegar al servicio.
3. **Schemas de salida (`InsumoPublic`, `Pagina`)**: controlan exactamente qué se expone en las respuestas JSON (`response_model`), incorporando el valor calculado `bajo_minimo` y ocultando siempre `codigo_proveedor` (`RN-05`).

---

## Por qué RN-04 devuelve 422 en el alta y 409 en el PATCH

En el alta (`POST /insumos/`), `InsumoCreate` recibe tanto `unidad` como las cantidades en el mismo payload, por lo que el validador de modelo de Pydantic detecta la inconsistencia antes de ejecutar la lógica de negocio y responde `422` por incumplir el contrato de entrada. En cambio, en el `PATCH /insumos/{id}`, `InsumoUpdate` no incluye el campo `unidad` (la unidad no se envía ni se modifica); recién el `service` puede comparar el nuevo `stock_minimo` con la unidad ya guardada en memoria, por lo que el rechazo constituye un conflicto con el estado persistido (`409`).
