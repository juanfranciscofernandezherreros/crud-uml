"""Casos de uso y reglas de negocio; ninguna decisión de HTTP ni SQL."""
from . import repository as repo
from .errors import Conflicto, NoEncontrado
from .schemas import UsuarioEntrada

def crear(datos: UsuarioEntrada):
    with repo.conexion() as db:
        if repo.existe_email(db, str(datos.email)):
            raise Conflicto("El correo electrónico ya está registrado")
        return repo.crear(db, datos.nombre, str(datos.email))

def obtener(usuario_id: int):
    with repo.conexion() as db:
        usuario = repo.buscar(db, usuario_id)
        if usuario is None:
            raise NoEncontrado("Usuario no encontrado")
        return usuario

def listar():
    with repo.conexion() as db:
        return repo.listar(db)

def actualizar(usuario_id: int, datos: UsuarioEntrada):
    with repo.conexion() as db:
        if repo.buscar(db, usuario_id) is None:
            raise NoEncontrado("Usuario no encontrado")
        if repo.existe_email(db, str(datos.email), excluir_id=usuario_id):
            raise Conflicto("El correo electrónico ya está registrado")
        return repo.actualizar(db, usuario_id, datos.nombre, str(datos.email))

def eliminar(usuario_id: int):
    with repo.conexion() as db:
        if repo.buscar(db, usuario_id) is None:
            raise NoEncontrado("Usuario no encontrado")
        # La FK ON DELETE RESTRICT evita borrar usuarios con dependencias.
        repo.eliminar(db, usuario_id)
