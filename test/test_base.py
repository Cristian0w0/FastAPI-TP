"""Pruebas base para C-01: lifespan, datos iniciales, modelo Insumo y FastAPI /docs."""

from datetime import timezone
from decimal import Decimal

from fastapi import Depends
from fastapi.testclient import TestClient

from app.core.database import InsumosDB, get_db
from app.main import app
from app.modules.insumos.models import Insumo, Unidad


def test_lifespan_inicializa_base_con_seis_insumos() -> None:
    """El lifespan debe crear exactamente 6 insumos en app.state.db con next_id = 7."""
    with TestClient(app) as client:
        db: InsumosDB = app.state.db
        assert len(db.items) == 6
        assert db.next_id == 7
        assert [item.id for item in db.items] == [1, 2, 3, 4, 5, 6]
        assert [item.nombre for item in db.items] == [
            "Harina 000",
            "Mozzarella",
            "Aceite de girasol",
            "Huevos",
            "Sal fina",
            "Levadura seca",
        ]

        docs_response = client.get("/docs")
        openapi_response = client.get("/openapi.json")
        assert docs_response.status_code == 200
        assert openapi_response.status_code == 200


def test_datos_iniciales_bajo_minimo_y_decimales() -> None:
    """Huevos debe usar enteros Decimal y solo Mozzarella y Sal fina están bajo el mínimo."""
    with TestClient(app):
        db: InsumosDB = app.state.db
        por_id: dict[int, Insumo] = {item.id: item for item in db.items}

        huevos = por_id[4]
        assert huevos.unidad == Unidad.unidad
        assert huevos.stock == Decimal("60")
        assert str(huevos.stock) == "60"
        assert str(huevos.stock_minimo) == "30"

        bajo_minimo = [item.nombre for item in db.items if item.bajo_minimo]
        assert bajo_minimo == ["Mozzarella", "Sal fina"]

        for item in db.items:
            assert item.creado_en.tzinfo == timezone.utc


def test_get_db_inyecta_la_misma_instancia_de_app_state() -> None:
    """La dependencia get_db debe retornar la misma instancia almacenada en app.state.db."""
    @app.get("/_test-db-check", include_in_schema=False)
    async def _check_db(db: InsumosDB = Depends(get_db)) -> dict[str, int]:
        return {"count": len(db.items), "next_id": db.next_id, "id_obj": id(db)}

    try:
        with TestClient(app) as client:
            resp = client.get("/_test-db-check")
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] == 6
            assert data["next_id"] == 7
            assert data["id_obj"] == id(app.state.db)
    finally:
        app.router.routes = [r for r in app.router.routes if getattr(r, "path", None) != "/_test-db-check"]
