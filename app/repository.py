"""Repositorio SQLite: el servicio no contiene SQL y la BD garantiza UNIQUE/FK."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .errors import Conflicto, InfraestructuraNoDisponible

def db_path() -> str:
    return os.environ.get("DATABASE_PATH", "./data/usuarios.sqlite3")

@contextmanager
def conexion():
    path = db_path()
    try:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(path, timeout=5)
    except OSError as exc:
        raise InfraestructuraNoDisponible() from exc
    try:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        yield db
        db.commit()
    except sqlite3.IntegrityError as exc:
        db.rollback()
        raise Conflicto("Conflicto de unicidad o dependencias protegidas") from exc
    except sqlite3.OperationalError as exc:
        db.rollback()
        raise InfraestructuraNoDisponible() from exc
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def inicializar():
    with conexion() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL COLLATE NOCASE UNIQUE
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS dependencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT
        )""")

def existe_email(db, email: str, excluir_id: int | None = None) -> bool:
    sql = "SELECT 1 FROM usuarios WHERE email = ?"
    params = [email]
    if excluir_id is not None:
        sql += " AND id != ?"
        params.append(excluir_id)
    return db.execute(sql, params).fetchone() is not None

def buscar(db, usuario_id: int):
    row = db.execute("SELECT id, nombre, email FROM usuarios WHERE id=?", (usuario_id,)).fetchone()
    return dict(row) if row else None

def listar(db):
    return [dict(row) for row in db.execute("SELECT id, nombre, email FROM usuarios ORDER BY id")]

def crear(db, nombre: str, email: str):
    cursor = db.execute("INSERT INTO usuarios(nombre, email) VALUES (?, ?)", (nombre, email))
    return buscar(db, cursor.lastrowid)

def actualizar(db, usuario_id: int, nombre: str, email: str):
    db.execute("UPDATE usuarios SET nombre=?, email=? WHERE id=?", (nombre, email, usuario_id))
    return buscar(db, usuario_id)

def eliminar(db, usuario_id: int):
    db.execute("DELETE FROM usuarios WHERE id=?", (usuario_id,))
