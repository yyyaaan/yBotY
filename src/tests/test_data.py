# Yan Pan
from fastapi.testclient import TestClient

from main import app
from dataAPIs.StatFinnPaavo import StatFinPaavo

client = TestClient(app)


def test_paavo():
    """fetch Paavo data from tilastokeskus and create a collection"""
    df = StatFinPaavo().get_data()
    assert df.shape[0] > 0
    assert df.shape[1] > 0
