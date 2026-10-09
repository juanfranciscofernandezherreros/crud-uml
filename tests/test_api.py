import os
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app

HEADERS = {"X-API-Key": "clave-lectura"}
ADMIN = {"X-API-Key": "clave-admin"}
ANA = {"nombre": "Ana", "email": "ana@example.com"}

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("API_KEY", "clave-lectura")
    monkeypatch.setenv("ADMIN_API_KEY", "clave-admin")
    with TestClient(app) as client:
        yield client

def test_crud_completo(client):
    assert client.get("/usuarios", headers=HEADERS).json() == []
    creado = client.post("/usuarios", headers=HEADERS, json=ANA)
    assert creado.status_code == 201
    uid = creado.json()["id"]
    assert creado.headers["location"] == f"/usuarios/{uid}"
    assert client.get(f"/usuarios/{uid}", headers=HEADERS).json()["nombre"] == "Ana"
    assert len(client.get("/usuarios", headers=HEADERS).json()) == 1
    editado = client.put(f"/usuarios/{uid}", headers=HEADERS, json={"nombre": "Ana 2", "email": "ana2@example.com"})
    assert editado.status_code == 200
    assert editado.json()["nombre"] == "Ana 2"
    assert client.delete(f"/usuarios/{uid}", headers=ADMIN).status_code == 204
    assert client.get(f"/usuarios/{uid}", headers=HEADERS).status_code == 404

def test_errores_autenticacion_y_autorizacion(client):
    assert client.get("/usuarios").status_code == 401
    assert client.get("/usuarios", headers={"X-API-Key": "incorrecta"}).status_code == 401
    creado = client.post("/usuarios", headers=HEADERS, json=ANA)
    assert client.delete(f"/usuarios/{creado.json()['id']}", headers=HEADERS).status_code == 403

def test_validaciones_y_no_encontrado(client):
    assert client.post("/usuarios", headers=HEADERS, json={"nombre": " ", "email": "incorrecto"}).status_code == 400
    assert client.get("/usuarios/no-es-entero", headers=HEADERS).status_code == 400
    assert client.get("/usuarios/0", headers=HEADERS).status_code == 400
    assert client.get("/usuarios/10000", headers=HEADERS).status_code == 404
    assert client.put("/usuarios/10000", headers=HEADERS, json=ANA).status_code == 404
    assert client.delete("/usuarios/10000", headers=ADMIN).status_code == 404

def test_conflicto_email_y_restriccion_bd(client):
    creado = client.post("/usuarios", headers=HEADERS, json=ANA)
    uid = creado.json()["id"]
    assert client.post("/usuarios", headers=HEADERS, json={"nombre": "Otro", "email": "ANA@example.com"}).status_code == 409
    assert client.post("/usuarios", headers=HEADERS, json={"nombre": "Bea", "email": "bea@example.com"}).status_code == 201
    assert client.put(f"/usuarios/{uid}", headers=HEADERS, json={"nombre": "Ana", "email": "bea@example.com"}).status_code == 409
    with sqlite3.connect(os.environ["DATABASE_PATH"]) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("INSERT INTO dependencias(usuario_id) VALUES (?)", (uid,))
    assert client.delete(f"/usuarios/{uid}", headers=ADMIN).status_code == 409
    assert client.get(f"/usuarios/{uid}", headers=HEADERS).status_code == 200

def test_bd_no_disponible(client, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "/dev/null/usuarios.sqlite3")
    assert client.get("/usuarios", headers=HEADERS).status_code == 503
