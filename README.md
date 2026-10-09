# Microservicio CRUD de usuarios

Implementación del [diagrama UML de secuencia CRUD con excepciones](https://juanfranciscofernandezherreros.github.io/arquitectura/diagrama-secuencia-uml-crud-excepciones/es/).

## Arquitectura

Cliente HTTP → Controller (`app/main.py`) → Service (`app/service.py`) → Repository (`app/repository.py`) → SQLite. La base de datos garantiza UNIQUE(email, sin distinción de mayúsculas) y FK restrictivas. Los errores se traducen en la frontera HTTP. Cada escritura utiliza una transacción que se revierte si falla.

## Ejecutar

Se requiere Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export API_KEY='cambia-esta-clave'
export ADMIN_API_KEY='cambia-esta-otra-clave'
uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs. Salud: `GET /health`. BD persistente: `./data/usuarios.sqlite3` (configurable mediante `DATABASE_PATH`).

```bash
curl -i -X POST http://localhost:8000/usuarios -H 'X-API-Key: cambia-esta-clave' -H 'Content-Type: application/json' -d '{"nombre":"Ana","email":"ana@example.com"}'
curl -H 'X-API-Key: cambia-esta-clave' http://localhost:8000/usuarios
curl -i -X DELETE -H 'X-API-Key: cambia-esta-otra-clave' http://localhost:8000/usuarios/1
```

## Docker

```bash
docker build -t crud-uml .
docker run --rm -p 8000:8000 -e API_KEY='clave-lectura' -e ADMIN_API_KEY='clave-admin' -v crud-uml-data:/app/data crud-uml
```

## Contrato REST

| Método | Ruta | Éxito |
|---|---|---|
| POST | /usuarios | 201 + Location |
| GET | /usuarios | 200, lista vacía permitida |
| GET | /usuarios/{id} | 200 |
| PUT | /usuarios/{id} | 200 |
| DELETE | /usuarios/{id} | 204 |

- 400: datos o ID inválidos (incluye errores de validación de FastAPI, en vez de 422).
- 401: API key ausente/inválida.
- 403: borrar sin clave administrativa.
- 404: recurso individual inexistente.
- 409: email duplicado, carrera UNIQUE o dependencias que impiden borrado.
- 500: error inesperado (sin detalles internos).
- 503: almacenamiento temporalmente no disponible o claves del servidor sin configurar.

Autenticación: cabecera `X-API-Key`, con permisos de borrado reservados a `ADMIN_API_KEY`. Este es un mecanismo sencillo para la demostración; en producción se recomienda OAuth2/OIDC, secretos gestionados, TLS, límites de tasa y registros de auditoría. No publicar claves reales.

## Pruebas

```bash
pytest -q
```

Incluye flujo completo CRUD, validación, autenticación, autorización, conflictos de unicidad/FK, errores 404 y fallo de infraestructura. Se documenta el diagrama original en `docs/secuencia.puml`. La tabla `dependencias` se incluye para ejercitar la restricción de borrado del diagrama.
