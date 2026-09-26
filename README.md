# INNOVA Services

Aplicación orientada a servicios basada en una API REST para el dominio inmobiliario de INNOVA.

## Servicios incluidos
- Property Service: catálogo y consulta de inmuebles.
- Appointment Service: agenda de visitas.
- Negotiation Service: ofertas y negociación.
- Profile Service: perfiles de vendedores.

## Tecnologías
- Python 3
- FastAPI
- Uvicorn
- SQLite
- HTML, CSS y JavaScript para el panel demostrativo
- OpenAPI / Swagger UI generado automáticamente por FastAPI

## Ejecución en Windows
1. Instala Python 3.
2. Ejecuta `run.bat`.
3. Abre `http://127.0.0.1:8000/`.
4. Documentación interactiva: `http://127.0.0.1:8000/docs`.

## Endpoints principales
- `GET /api/health`
- `GET /api/properties`
- `POST /api/properties`
- `GET /api/appointments`
- `POST /api/appointments`
- `GET /api/offers`
- `POST /api/offers`
- `GET /api/sellers`
