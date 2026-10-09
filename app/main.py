"""Controller HTTP y traducción centralizada de excepciones."""
import hmac
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Path, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import repository, service
from .errors import Conflicto, InfraestructuraNoDisponible, NoEncontrado
from .schemas import UsuarioEntrada, UsuarioSalida

@asynccontextmanager
async def lifespan(app: FastAPI):
    repository.inicializar()
    yield

app = FastAPI(title="CRUD de usuarios", version="1.0.0", lifespan=lifespan)

@app.exception_handler(RequestValidationError)
async def error_validacion(request, exc):
    return JSONResponse(status_code=400, content={"error": "VALIDACION", "mensaje": "Datos o parámetros inválidos"})

@app.exception_handler(NoEncontrado)
async def error_404(request, exc):
    return JSONResponse(status_code=404, content={"error": "NO_ENCONTRADO", "mensaje": str(exc)})

@app.exception_handler(Conflicto)
async def error_409(request, exc):
    return JSONResponse(status_code=409, content={"error": "CONFLICTO", "mensaje": str(exc)})

@app.exception_handler(InfraestructuraNoDisponible)
async def error_503(request, exc):
    return JSONResponse(status_code=503, content={"error": "NO_DISPONIBLE", "mensaje": "Persistencia temporalmente no disponible"})

@app.exception_handler(Exception)
async def error_500(request, exc):
    return JSONResponse(status_code=500, content={"error": "INTERNO", "mensaje": "Error interno del servidor"})

def autenticar(x_api_key: str | None = Header(default=None)):
    normal = os.environ.get("API_KEY")
    admin = os.environ.get("ADMIN_API_KEY")
    if not normal or not admin:
        raise HTTPException(503, detail="Credenciales del servidor no configuradas")
    if x_api_key and hmac.compare_digest(x_api_key, admin):
        return "admin"
    if x_api_key and hmac.compare_digest(x_api_key, normal):
        return "usuario"
    raise HTTPException(401, detail="Credenciales ausentes o inválidas", headers={"WWW-Authenticate": "ApiKey"})

def autorizar_borrado(rol: str = Depends(autenticar)):
    if rol != "admin":
        raise HTTPException(403, detail="Permisos insuficientes")

def id_valido(usuario_id: int = Path(ge=1)):
    return usuario_id

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/usuarios", response_model=UsuarioSalida, status_code=201, dependencies=[Depends(autenticar)])
def crear(datos: UsuarioEntrada, response: Response):
    usuario = service.crear(datos)
    response.headers["Location"] = f"/usuarios/{usuario['id']}"
    return usuario

@app.get("/usuarios", response_model=list[UsuarioSalida], dependencies=[Depends(autenticar)])
def listar():
    return service.listar()

@app.get("/usuarios/{usuario_id}", response_model=UsuarioSalida, dependencies=[Depends(autenticar)])
def obtener(usuario_id: int = Depends(id_valido)):
    return service.obtener(usuario_id)

@app.put("/usuarios/{usuario_id}", response_model=UsuarioSalida, dependencies=[Depends(autenticar)])
def actualizar(datos: UsuarioEntrada, usuario_id: int = Depends(id_valido)):
    return service.actualizar(usuario_id, datos)

@app.delete("/usuarios/{usuario_id}", status_code=204, dependencies=[Depends(autorizar_borrado)])
def eliminar(usuario_id: int = Depends(id_valido)):
    service.eliminar(usuario_id)
    return Response(status_code=204)
