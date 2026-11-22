import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.adapter_modelo import adaptar_prediccion_externa
from backend.rules_engine import recomendar_outfits
from backend.storage_service import AlmacenamientoDemo

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
DATA_DIR = BASE_DIR / "data"

app = FastAPI(title="Estudio de Outfits", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = AlmacenamientoDemo(DATA_DIR)
storage.uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(storage.uploads_dir)), name="uploads")


class AuthRequest(BaseModel):
    identificador: str
    nombre: Optional[str] = None


class RecomendacionRequest(BaseModel):
    ocasion: str = "diario"
    clima: str = "templado"
    limite: int = 5


@app.get("/", response_class=HTMLResponse)
def servir_inicio() -> HTMLResponse:
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="No se encontró frontend/index.html")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


@app.get("/styles.css")
def servir_css() -> FileResponse:
    css_file = FRONTEND_DIR / "styles.css"
    if not css_file.exists():
        raise HTTPException(status_code=404, detail="No se encontró frontend/styles.css")
    return FileResponse(css_file, media_type="text/css")


@app.get("/app.js")
def servir_js() -> FileResponse:
    js_file = FRONTEND_DIR / "app.js"
    if not js_file.exists():
        raise HTTPException(status_code=404, detail="No se encontró frontend/app.js")
    return FileResponse(js_file, media_type="application/javascript")


@app.post("/api/auth/login")
def login(payload: AuthRequest) -> Dict[str, Any]:
    if not payload.identificador.strip():
        raise HTTPException(status_code=400, detail="Ingresa tu usuario o correo.")
    resultado = storage.iniciar_sesion(payload.identificador, payload.nombre)
    if not resultado.get("ok"):
        raise HTTPException(status_code=404, detail=resultado.get("error", "Cuenta no encontrada."))
    usuario = resultado["usuario"]
    prendas = storage.listar_prendas(usuario["user_id"])
    return {"usuario": usuario, "total_prendas": len(prendas)}


@app.post("/api/auth/register")
def register(payload: AuthRequest) -> Dict[str, Any]:
    if not payload.identificador.strip():
        raise HTTPException(status_code=400, detail="Ingresa un usuario o correo.")
    if not (payload.nombre and payload.nombre.strip()):
        raise HTTPException(status_code=400, detail="Ingresa tu nombre.")
    resultado = storage.crear_cuenta(payload.identificador, payload.nombre)
    if not resultado.get("ok"):
        raise HTTPException(status_code=409, detail=resultado.get("error", "No se pudo crear la cuenta."))
    usuario = resultado["usuario"]
    return {"usuario": usuario, "total_prendas": 0}


@app.get("/api/closet/{user_id}")
def obtener_closet(user_id: str) -> Dict[str, Any]:
    usuario = storage.obtener_usuario(user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    prendas = storage.listar_prendas(usuario["user_id"])
    return {"usuario": usuario, "prendas": prendas}


@app.post("/api/closet/{user_id}/prendas")
async def subir_prenda(
    user_id: str,
    imagen: UploadFile = File(...),
) -> Dict[str, Any]:
    usuario = storage.obtener_usuario(user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    contenido = await imagen.read()
    if not contenido:
        raise HTTPException(status_code=400, detail="La imagen está vacía.")

    imagen_url = storage.guardar_imagen(usuario["user_id"], imagen.filename or "foto.jpg", contenido)
    prenda_id = f"pr_{uuid.uuid4().hex[:8]}"
    prenda = adaptar_prediccion_externa(
        payload={"origen_etiqueta": "pendiente_modelo"},
        user_id=usuario["user_id"],
        imagen_url=imagen_url,
        prenda_id=prenda_id,
    )
    guardada = storage.guardar_prenda(usuario["user_id"], prenda.to_dict())
    return {"prenda": guardada}


@app.delete("/api/closet/{user_id}/prendas/{prenda_id}")
def borrar_prenda(user_id: str, prenda_id: str) -> Dict[str, Any]:
    eliminada = storage.eliminar_prenda(user_id=user_id, prenda_id=prenda_id)
    if not eliminada:
        raise HTTPException(status_code=404, detail="Prenda no encontrada.")
    return {"eliminada": True, "prenda_id": prenda_id}


@app.post("/api/recomendar/{user_id}")
def recomendar(user_id: str, req: RecomendacionRequest) -> Dict[str, Any]:
    prendas = storage.listar_prendas(user_id)
    limite = max(1, min(15, int(req.limite)))
    outfits = recomendar_outfits(prendas=prendas, ocasion=req.ocasion, clima=req.clima, limite=limite)
    return {
        "user_id": user_id,
        "ocasion": req.ocasion,
        "clima": req.clima,
        "total_recomendaciones": len(outfits),
        "outfits": outfits,
    }
