from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "innova_services.db"

app = FastAPI(
    title="INNOVA Services API",
    description="Aplicación orientada a servicios para consultar propiedades, agendar visitas y registrar negociaciones.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            operation TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Disponible'
        );
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendiente'
        );
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'En revisión'
        );
        CREATE TABLE IF NOT EXISTS sellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            rating REAL NOT NULL DEFAULT 5.0
        );
        """
    )
    if cur.execute("SELECT COUNT(*) FROM properties").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO properties(title,location,operation,price,status) VALUES(?,?,?,?,?)",
            [
                ("Casa Familiar Cholula", "San Pedro Cholula, Puebla", "Venta", 3250000, "Disponible"),
                ("Residencia La Paz", "La Paz, Puebla", "Renta", 25000, "Disponible"),
                ("Departamento Angelópolis", "Angelópolis, Puebla", "Venta", 2150000, "En negociación"),
                ("Loft Centro Histórico", "Centro, Puebla", "Renta", 14500, "Disponible"),
            ],
        )
    if cur.execute("SELECT COUNT(*) FROM appointments").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO appointments(property_id,client_name,date,time,status) VALUES(?,?,?,?,?)",
            [
                (1, "Mariana López", "2026-09-28", "11:00", "Confirmada"),
                (2, "Carlos Méndez", "2026-09-29", "17:30", "Pendiente"),
            ],
        )
    if cur.execute("SELECT COUNT(*) FROM offers").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO offers(property_id,client_name,amount,status) VALUES(?,?,?,?)",
            [
                (3, "Andrea Ruiz", 2050000, "Contraoferta"),
                (1, "José García", 3100000, "En revisión"),
            ],
        )
    if cur.execute("SELECT COUNT(*) FROM sellers").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO sellers(name,phone,email,rating) VALUES(?,?,?,?)",
            [
                ("Laura Hernández", "222 555 0182", "laura@innova.mx", 4.9),
                ("Miguel Torres", "222 555 0196", "miguel@innova.mx", 4.8),
            ],
        )
    conn.commit()
    conn.close()


class PropertyIn(BaseModel):
    title: str
    location: str
    operation: str = Field(pattern="^(Venta|Renta)$")
    price: float = Field(gt=0)
    status: str = "Disponible"


class AppointmentIn(BaseModel):
    property_id: int
    client_name: str
    date: str
    time: str


class OfferIn(BaseModel):
    property_id: int
    client_name: str
    amount: float = Field(gt=0)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/api/health", tags=["Estado del servicio"])
def health():
    return {
        "service": "INNOVA Services API",
        "status": "online",
        "version": "1.0.0",
        "services": ["properties", "appointments", "offers", "sellers"],
    }


@app.get("/api/properties", tags=["Property Service"])
def list_properties(operation: Optional[str] = None, location: Optional[str] = None):
    conn = db()
    query = "SELECT * FROM properties WHERE 1=1"
    params = []
    if operation:
        query += " AND operation = ?"
        params.append(operation)
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    rows = [dict(r) for r in conn.execute(query, params).fetchall()]
    conn.close()
    return rows


@app.get("/api/properties/{property_id}", tags=["Property Service"])
def get_property(property_id: int):
    conn = db()
    row = conn.execute("SELECT * FROM properties WHERE id=?", (property_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Propiedad no encontrada")
    return dict(row)


@app.post("/api/properties", tags=["Property Service"], status_code=201)
def create_property(item: PropertyIn):
    conn = db()
    cur = conn.execute(
        "INSERT INTO properties(title,location,operation,price,status) VALUES(?,?,?,?,?)",
        (item.title, item.location, item.operation, item.price, item.status),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM properties WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/appointments", tags=["Appointment Service"])
def list_appointments():
    conn = db()
    rows = [dict(r) for r in conn.execute("SELECT * FROM appointments ORDER BY date,time").fetchall()]
    conn.close()
    return rows


@app.post("/api/appointments", tags=["Appointment Service"], status_code=201)
def create_appointment(item: AppointmentIn):
    conn = db()
    if not conn.execute("SELECT 1 FROM properties WHERE id=?", (item.property_id,)).fetchone():
        conn.close()
        raise HTTPException(404, "Propiedad no encontrada")
    cur = conn.execute(
        "INSERT INTO appointments(property_id,client_name,date,time,status) VALUES(?,?,?,?,?)",
        (item.property_id, item.client_name, item.date, item.time, "Pendiente"),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM appointments WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/offers", tags=["Negotiation Service"])
def list_offers():
    conn = db()
    rows = [dict(r) for r in conn.execute("SELECT * FROM offers ORDER BY id DESC").fetchall()]
    conn.close()
    return rows


@app.post("/api/offers", tags=["Negotiation Service"], status_code=201)
def create_offer(item: OfferIn):
    conn = db()
    if not conn.execute("SELECT 1 FROM properties WHERE id=?", (item.property_id,)).fetchone():
        conn.close()
        raise HTTPException(404, "Propiedad no encontrada")
    cur = conn.execute(
        "INSERT INTO offers(property_id,client_name,amount,status) VALUES(?,?,?,?)",
        (item.property_id, item.client_name, item.amount, "En revisión"),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM offers WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/sellers", tags=["Profile Service"])
def list_sellers():
    conn = db()
    rows = [dict(r) for r in conn.execute("SELECT * FROM sellers ORDER BY rating DESC").fetchall()]
    conn.close()
    return rows
