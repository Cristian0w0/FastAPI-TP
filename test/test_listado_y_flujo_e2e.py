"""Pruebas para C-04: listado GET /insumos/ (RN-10..RN-12) y secuencia E2E C-01 a C-16."""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app


def test_listado_filtros_previos_al_conteo_y_ocultamiento() -> None:
    """RN-05 y RN-11: filtros unidad, bajo_minimo y activo cuentan después de filtrar sin exponer proveedor."""
    with TestClient(app) as client:
        resp_all = client.get("/insumos/")
        assert resp_all.status_code == 200
        data_all = resp_all.json()
        assert data_all["total"] == 6
        assert data_all["page"] == 1
        assert data_all["size"] == 20
        assert data_all["pages"] == 1
        assert len(data_all["items"]) == 6
        assert all("codigo_proveedor" not in item for item in data_all["items"])

        # ?bajo_minimo=true con datos semilla -> total 2 (Mozzarella y Sal fina)
        resp_bm = client.get("/insumos/?bajo_minimo=true")
        assert resp_bm.status_code == 200
        bm = resp_bm.json()
        assert bm["total"] == 2
        assert [item["nombre"] for item in bm["items"]] == ["Mozzarella", "Sal fina"]

        # Filtros combinados: unidad=g y activo=true -> solo Sal fina (Levadura seca está inactiva)
        resp_comb = client.get("/insumos/?unidad=g&activo=true")
        assert resp_comb.status_code == 200
        comb = resp_comb.json()
        assert comb["total"] == 1
        assert comb["items"][0]["nombre"] == "Sal fina"

        # Filtro por unidad inválida -> 422
        assert client.get("/insumos/?unidad=docena").status_code == 422


def test_listado_paginacion_y_opcion_a_vacios() -> None:
    """RN-10 (Opción A): paginación, límites de query, vacío page=1 -> 200 y page>=2 -> 422."""
    with TestClient(app) as client:
        # Paginación con size=2 sobre 6 items -> 3 páginas
        resp_p2 = client.get("/insumos/?page=2&size=2")
        assert resp_p2.status_code == 200
        p2 = resp_p2.json()
        assert p2["total"] == 6
        assert p2["page"] == 2
        assert p2["size"] == 2
        assert p2["pages"] == 3
        assert [item["id"] for item in p2["items"]] == [3, 4]

        # Más allá de la última página -> 422
        assert client.get("/insumos/?page=4&size=2").status_code == 422

        # Límites de page y size -> 422
        assert client.get("/insumos/?page=0").status_code == 422
        assert client.get("/insumos/?size=0").status_code == 422
        assert client.get("/insumos/?size=101").status_code == 422

        # Opción A: filtro sin resultados (?unidad=ml)
        resp_vacio = client.get("/insumos/?unidad=ml&page=1")
        assert resp_vacio.status_code == 200
        assert resp_vacio.json() == {
            "items": [],
            "total": 0,
            "page": 1,
            "size": 20,
            "pages": 0,
        }
        assert client.get("/insumos/?unidad=ml&page=2").status_code == 422


def test_listado_ordenamiento_lista_blanca() -> None:
    """RN-12: ordena por nombre, stock (Decimal) y creado_en; rechaza campos fuera de lista blanca."""
    with TestClient(app) as client:
        # Agregar uno nuevo para probar -creado_en y -stock en kg
        resp_nuevo = client.post(
            "/insumos/",
            json={"nombre": "albahaca", "unidad": "kg", "stock": "1.500"},
        )
        assert resp_nuevo.status_code == 201

        # ?unidad=kg&sort=-stock compara numéricamente (25.000 > 3.500 > 1.500)
        resp_kg = client.get("/insumos/?unidad=kg&sort=-stock")
        assert resp_kg.status_code == 200
        stocks = [Decimal(item["stock"]) for item in resp_kg.json()["items"]]
        assert stocks == [Decimal("25.000"), Decimal("3.500"), Decimal("1.500")]

        # ?sort=-stock global: Sal fina ("800.000") queda antes que Harina ("25.000")
        resp_global = client.get("/insumos/?sort=-stock")
        assert resp_global.status_code == 200
        assert resp_global.json()["items"][0]["nombre"] == "Sal fina"

        # ?sort=nombre ordena alfabéticamente sin sensibilidad a mayúsculas
        resp_nombre = client.get("/insumos/?sort=nombre")
        assert resp_nombre.status_code == 200
        nombres = [item["nombre"] for item in resp_nombre.json()["items"]]
        assert nombres[0] == "Aceite de girasol"
        assert nombres[1] == "albahaca"

        # ?sort=-creado_en pone primero el recién creado
        resp_creado = client.get("/insumos/?sort=-creado_en")
        assert resp_creado.status_code == 200
        assert resp_creado.json()["items"][0]["id"] == 7

        # Lista blanca: ?sort=codigo_proveedor y ?sort=-activo -> 422
        assert client.get("/insumos/?sort=codigo_proveedor").status_code == 422
        assert client.get("/insumos/?sort=-activo").status_code == 422


def test_flujo_completo_c01_a_c16_en_orden_exacto() -> None:
    """Ejecuta en orden estricto C-01 a C-16 desde el estado semilla limpio (6 insumos)."""
    with TestClient(app) as client:
        # C-01: GET /insumos/abc -> 422
        assert client.get("/insumos/abc").status_code == 422

        # C-02: GET /insumos/99 -> 404
        assert client.get("/insumos/99").status_code == 404

        # C-03: GET /insumos/2 -> 200 sin codigo_proveedor
        r_c03 = client.get("/insumos/2")
        assert r_c03.status_code == 200
        assert "codigo_proveedor" not in r_c03.json()

        # C-04: Alta del ejemplo -> 201, Location: /insumos/7, nombre normalizado
        r_c04 = client.post(
            "/insumos/",
            json={
                "nombre": "  Queso   rallado  ",
                "unidad": "kg",
                "stock": "2.250",
                "stock_minimo": "1.000",
                "codigo_proveedor": "QUE-0007",
            },
        )
        assert r_c04.status_code == 201
        assert r_c04.headers["location"] == "/insumos/7"
        assert r_c04.json()["nombre"] == "Queso rallado"
        assert "codigo_proveedor" not in r_c04.json()

        # C-05: Alta por unidad con stock="12.5" -> 422
        assert (
            client.post(
                "/insumos/",
                json={"nombre": "Tapas de empanada", "unidad": "unidad", "stock": "12.5"},
            ).status_code
            == 422
        )

        # C-06: Alta con 3 errores juntos -> 422 con los 3 errores
        r_c06 = client.post(
            "/insumos/",
            json={"nombre": "", "unidad": "docena", "stock": -1},
        )
        assert r_c06.status_code == 422
        assert len(r_c06.json()["detail"]) == 3

        # C-07: Alta con id en cuerpo -> 422
        assert (
            client.post(
                "/insumos/",
                json={"id": 99, "nombre": "Pimienta", "unidad": "g"},
            ).status_code
            == 422
        )

        # C-08: PATCH /insumos/1 solo stock_minimo -> 200, resto intacto
        r_c08 = client.patch("/insumos/1", json={"stock_minimo": "15.000"})
        assert r_c08.status_code == 200
        assert r_c08.json()["stock_minimo"] == "15.000"
        assert r_c08.json()["nombre"] == "Harina 000"
        assert r_c08.json()["stock"] == "25.000"

        # C-09: PATCH /insumos/1 codigo_proveedor=null (200) y nombre=null (422)
        assert client.patch("/insumos/1", json={"codigo_proveedor": None}).status_code == 200
        assert client.patch("/insumos/1", json={"nombre": None}).status_code == 422

        # C-10: PATCH /insumos/1 con stock -> 422
        assert client.patch("/insumos/1", json={"stock": "10.000"}).status_code == 422

        # C-11: Ajuste "-1.250" (200, "2.250") y luego "-5.000" (409 sin cambios)
        r_c11_a = client.post(
            "/insumos/2/ajustes",
            json={"cantidad": "-1.250", "motivo": "consumo"},
        )
        assert r_c11_a.status_code == 200
        assert r_c11_a.json()["stock"] == "2.250"

        r_c11_b = client.post(
            "/insumos/2/ajustes",
            json={"cantidad": "-5.000", "motivo": "consumo"},
        )
        assert r_c11_b.status_code == 409
        assert client.get("/insumos/2").json()["stock"] == "2.250"

        # C-12: Ajuste "-0.5" sobre Huevos (id=4) -> 409
        assert (
            client.post(
                "/insumos/4/ajustes",
                json={"cantidad": "-0.5", "motivo": "merma"},
            ).status_code
            == 409
        )

        # C-13: GET /insumos/?bajo_minimo=true -> 200 con total 2
        r_c13 = client.get("/insumos/?bajo_minimo=true")
        assert r_c13.status_code == 200
        assert r_c13.json()["total"] == 2

        # C-14: GET /insumos/?sort=codigo_proveedor -> 422
        assert client.get("/insumos/?sort=codigo_proveedor").status_code == 422

        # C-15: GET /insumos/?page=9 -> 422
        assert client.get("/insumos/?page=9").status_code == 422

        # C-16: Borrar insumo 6 dos veces (204, 404) y alta posterior sin reutilizar 6
        r_c16_del1 = client.delete("/insumos/6")
        assert r_c16_del1.status_code == 204
        assert r_c16_del1.content == b""
        assert client.delete("/insumos/6").status_code == 404

        r_c16_post = client.post(
            "/insumos/",
            json={"nombre": "Orégano seco", "unidad": "g", "stock": "150.000"},
        )
        assert r_c16_post.status_code == 201
        assert r_c16_post.json()["id"] != 6
        assert r_c16_post.json()["id"] == 8
        assert r_c16_post.headers["location"] == "/insumos/8"
