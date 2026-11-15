"""Pruebas de integración para C-03: endpoints CRUD individuales, ajustes y casos C-01..C-12, C-16."""

import ast
import inspect
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.modules.insumos import router as insumos_router_mod


def test_c01_c02_c03_detalle_y_validacion_id(monkeypatch) -> None:
    """C-01: ID no entero da 422 sin ejecutar el handler; C-02: 404; C-03: oculta codigo_proveedor."""
    llamadas: list[int] = []
    original = insumos_router_mod.obtener_insumo

    def _spy(db, insumo_id: int):
        llamadas.append(insumo_id)
        return original(db, insumo_id)

    monkeypatch.setattr(insumos_router_mod, "obtener_insumo", _spy)

    with TestClient(app) as client:
        # C-01: verificar 422 antes de invocar el handler/servicio
        resp_c01 = client.get("/insumos/abc")
        assert resp_c01.status_code == 422
        assert llamadas == []

        # C-02: recurso inexistente
        resp_c02 = client.get("/insumos/99")
        assert resp_c02.status_code == 404
        assert "detail" in resp_c02.json()

        # C-03: detalle existente sin codigo_proveedor y con bajo_minimo calculado
        resp_c03 = client.get("/insumos/2")
        assert resp_c03.status_code == 200
        body = resp_c03.json()
        assert body["id"] == 2
        assert body["nombre"] == "Mozzarella"
        assert body["stock"] == "3.500"
        assert body["bajo_minimo"] is True
        assert "codigo_proveedor" not in body


def test_c04_c05_c06_c07_alta_y_defensas_contrato() -> None:
    """C-04..C-07: alta con Location y normalización, errores RN-04, multi-error y extra='forbid'."""
    with TestClient(app) as client:
        # C-04: alta del ejemplo de la consigna
        payload_c04 = {
            "nombre": "  Queso   rallado  ",
            "unidad": "kg",
            "stock": "2.250",
            "stock_minimo": "1.000",
            "codigo_proveedor": "QUE-0007",
        }
        resp_c04 = client.post("/insumos/", json=payload_c04)
        assert resp_c04.status_code == 201
        assert resp_c04.headers["location"] == "/insumos/7"
        data = resp_c04.json()
        assert data["id"] == 7
        assert data["nombre"] == "Queso rallado"
        assert data["stock"] == "2.250"
        assert data["stock_minimo"] == "1.000"
        assert data["activo"] is True
        assert data["bajo_minimo"] is False
        assert data["creado_en"].endswith("Z")
        assert "codigo_proveedor" not in data

        # C-05: unidad='unidad' con decimales en stock
        resp_c05 = client.post(
            "/insumos/",
            json={"nombre": "Tapas", "unidad": "unidad", "stock": "12.5"},
        )
        assert resp_c05.status_code == 422

        # C-06: nombre vacío, unidad inválida y stock negativo juntos
        resp_c06 = client.post(
            "/insumos/",
            json={"nombre": "", "unidad": "docena", "stock": -1},
        )
        assert resp_c06.status_code == 422
        campos = {err["loc"][1] for err in resp_c06.json()["detail"]}
        assert campos == {"nombre", "unidad", "stock"}

        # C-07: id en cuerpo rechazado por extra='forbid'
        resp_c07 = client.post(
            "/insumos/",
            json={"id": 99, "nombre": "Pimienta", "unidad": "g"},
        )
        assert resp_c07.status_code == 422


def test_c08_c09_c10_patch_parcial_null_y_rn04_409() -> None:
    """C-08..C-10 y RN-04 en PATCH: parcial sin borrar, null solo en proveedor, 409 en unidad."""
    with TestClient(app) as client:
        # C-08: solo cambia stock_minimo; el resto queda intacto
        resp_c08 = client.patch("/insumos/1", json={"stock_minimo": "15.000"})
        assert resp_c08.status_code == 200
        body = resp_c08.json()
        assert body["nombre"] == "Harina 000"
        assert body["unidad"] == "kg"
        assert body["stock"] == "25.000"
        assert body["stock_minimo"] == "15.000"
        assert body["activo"] is True

        # C-09: codigo_proveedor=null permitido (lo borra), nombre=null rechazado con 422
        resp_null_ok = client.patch("/insumos/1", json={"codigo_proveedor": None})
        assert resp_null_ok.status_code == 200
        assert app.state.db.items[0].codigo_proveedor is None

        resp_null_bad = client.patch("/insumos/1", json={"nombre": None})
        assert resp_null_bad.status_code == 422

        # C-10: stock prohibido en PATCH
        resp_c10 = client.patch("/insumos/1", json={"stock": "10.000"})
        assert resp_c10.status_code == 422

        # RN-04 en PATCH sobre Huevos (id=4, unidad='unidad'): decimal -> 409 sin mutar
        resp_409 = client.patch(
            "/insumos/4",
            json={"stock_minimo": "35.5", "nombre": "No debería cambiar"},
        )
        assert resp_409.status_code == 409
        huevos = client.get("/insumos/4").json()
        assert huevos["nombre"] == "Huevos"
        assert huevos["stock_minimo"] == "30"

        # PATCH válido sobre Huevos con entero Decimal normaliza sin .000
        resp_huevos_ok = client.patch("/insumos/4", json={"stock_minimo": "35.000"})
        assert resp_huevos_ok.status_code == 200
        assert resp_huevos_ok.json()["stock_minimo"] == "35"

        # PATCH sobre inexistente -> 404
        assert client.patch("/insumos/999", json={"activo": False}).status_code == 404


def test_c11_c12_comando_ajuste_y_errores_409() -> None:
    """C-11 y C-12: ajuste 200, rechazo 409 sin mutar por stock negativo o decimal en unidad."""
    with TestClient(app) as client:
        # C-11 parte 1: consumo válido de Mozzarella ("3.500" -> "2.250")
        resp_ok = client.post(
            "/insumos/2/ajustes",
            json={"cantidad": "-1.250", "motivo": "consumo"},
        )
        assert resp_ok.status_code == 200
        assert resp_ok.json()["stock"] == "2.250"
        assert "codigo_proveedor" not in resp_ok.json()

        # C-11 parte 2: consumo que dejaría negativo -> 409 sin cambiar "2.250"
        resp_neg = client.post(
            "/insumos/2/ajustes",
            json={"cantidad": "-5.000", "motivo": "consumo"},
        )
        assert resp_neg.status_code == 409
        assert client.get("/insumos/2").json()["stock"] == "2.250"

        # C-12: ajuste con decimales sobre Huevos (unidad='unidad') -> 409 sin cambios
        resp_dec = client.post(
            "/insumos/4/ajustes",
            json={"cantidad": "-0.5", "motivo": "merma"},
        )
        assert resp_dec.status_code == 409
        assert client.get("/insumos/4").json()["stock"] == "60"

        # Ajuste entero sobre Huevos sí mantiene entero sin .000
        resp_huevos_ok = client.post(
            "/insumos/4/ajustes",
            json={"cantidad": "-10.000", "motivo": "consumo"},
        )
        assert resp_huevos_ok.status_code == 200
        assert resp_huevos_ok.json()["stock"] == "50"

        # Ajuste sobre insumo inexistente -> 404
        assert (
            client.post(
                "/insumos/999/ajustes",
                json={"cantidad": "1.000", "motivo": "compra"},
            ).status_code
            == 404
        )


def test_c16_doble_delete_y_no_reutilizacion_de_id() -> None:
    """C-16: DELETE 6 -> 204 sin cuerpo, segundo DELETE -> 404, nuevo POST recibe id != 6."""
    with TestClient(app) as client:
        resp_del1 = client.delete("/insumos/6")
        assert resp_del1.status_code == 204
        assert resp_del1.content == b""

        resp_del2 = client.delete("/insumos/6")
        assert resp_del2.status_code == 404

        resp_nuevo = client.post(
            "/insumos/",
            json={"nombre": "Orégano", "unidad": "g", "stock": "150.000"},
        )
        assert resp_nuevo.status_code == 201
        assert resp_nuevo.json()["id"] == 7
        assert resp_nuevo.headers["location"] == "/insumos/7"


def test_reglas_arquitectura_service_sin_http_y_sin_put() -> None:
    """Verifica aislamiento de service.py, handlers async def en router.py y ausencia de PUT."""
    source = Path("app/modules/insumos/service.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert not any(mod.startswith(("fastapi", "starlette")) for mod in imports)

    for route in insumos_router_mod.router.routes:
        assert inspect.iscoroutinefunction(route.endpoint)

    with TestClient(app) as client:
        resp_put = client.put(
            "/insumos/1",
            json={"nombre": "Harina 000", "unidad": "kg"},
        )
        assert resp_put.status_code == 405
