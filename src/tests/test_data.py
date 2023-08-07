# Yan Pan
from fastapi.testclient import TestClient

from main import app
from dataAPIs.StatFinnPaavo import StatFinPaavo
from prompts.VectorStorage import VectorStorage

client = TestClient(app)

def test_paavo():
    """fetch Paavo data from tilastokeskus and create a collection"""
    df = StatFinPaavo().get_data()
    df.to_csv("/mnt/shared/upload/tmptmp.csv")

