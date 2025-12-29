from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient


def test_metrics_page(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == HTTP_200_OK
    assert "MÉTRICAS DE CUÑADISMO" in response.text
    assert "Ranking de Contribuidores" in response.text
