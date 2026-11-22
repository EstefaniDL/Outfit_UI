import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
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

app = FastAPI(title="Recomendador de Outfits — Base UI", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = AlmacenamientoDemo(DATA_DIR)
storage.uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(storage.uploads_dir)), name="uploads")


class LoginRequest(BaseModel):
    identificador: str
    nombre: Optional[str] = None


class ActualizarPrendaRequest(BaseModel):
    tipo_articulo: Optional[str] = None
    color_principal: Optional[str] = None
    tono: Optional[str] = None
    estampado: Optional[str] = None
    material: Optional[str] = None
    corte: Optional[str] = None
    largo: Optional[str] = None
    formalidad: Optional[str] = None
    estilo: Optional[List[str]] = None
    estetica: Optional[List[str]] = None
    temporada: Optional[List[str]] = None
    clima: Optional[List[str]] = None
    ocasiones: Optional[List[str]] = None
    etiquetas_confirmadas: Optional[bool] = None


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


@app.post("/api/auth/register")
def register(payload: LoginRequest) -> Dict[str, Any]:
    if not payload.identificador.strip():
        raise HTTPException(status_code=400, detail="Elige un usuario o correo para crear tu cuenta.")
    if not (payload.nombre and payload.nombre.strip()):
        raise HTTPException(status_code=400, detail="Ingresa tu nombre.")
    resultado = storage.crear_cuenta(payload.identificador, payload.nombre)
    if not resultado.get("ok"):
        raise HTTPException(status_code=409, detail=resultado.get("error", "No se pudo crear la cuenta."))
    usuario = resultado["usuario"]
    return {"usuario": usuario, "total_prendas": 0}


@app.post("/api/auth/register")
def register(payload: LoginRequest) -> Dict[str, Any]:
    if not payload.identificador.strip():
        raise HTTPException(status_code=400, detail="Elige un usuario o correo para crear tu cuenta.")
    resultado = storage.crear_cuenta(payload.identificador, payload.nombre)
    if not resultado.get("ok"):
        raise HTTPException(status_code=409, detail=resultado.get("error", "No se pudo crear la cuenta."))
    usuario = resultado["usuario"]
    return {"usuario": usuario, "total_prendas": 0}


@app.get("/api/closet/{user_id}")
def obtener_closet(user_id: str) -> Dict[str, Any]:
    usuario = storage.obtener_usuario(user_id)
    if not usuario:
        usuario = storage.iniciar_o_registrar_usuario(user_id)
    prendas = storage.listar_prendas(usuario["user_id"])
    return {"usuario": usuario, "prendas": prendas}


@app.post("/api/closet/{user_id}/prendas")
async def subir_prenda(
    user_id: str,
    imagen: UploadFile = File(...),
    tipo_articulo: str = Form("superior"),
    color_principal: str = Form("sin_definir"),
    tono: str = Form("medio"),
    estampado: str = Form("liso"),
    material: str = Form("algodon"),
    corte: str = Form("regular"),
    largo: str = Form("regular"),
    formalidad: str = Form("casual"),
    clima: str = Form("templado"),
    temporada: str = Form("todo_el_ano"),
    ocasiones: str = Form("diario"),
    estilo: str = Form("casual"),
    estetica: str = Form("clasico"),
    metadatos_externos: Optional[str] = Form(None),
) -> Dict[str, Any]:
    usuario = storage.iniciar_o_registrar_usuario(user_id)
    contenido = await imagen.read()
    if not contenido:
        raise HTTPException(status_code=400, detail="La imagen está vacía.")

    imagen_url = storage.guardar_imagen(usuario["user_id"], imagen.filename or "foto.jpg", contenido)
    prenda_id = f"pr_{uuid.uuid4().hex[:8]}"

    base_payload: Dict[str, Any] = {
        "tipo_articulo": tipo_articulo,
        "color_principal": color_principal,
        "tono": tono,
        "estampado": estampado,
        "material": material,
        "corte": corte,
        "largo": largo,
        "formalidad": formalidad,
        "clima": clima,
        "temporada": temporada,
        "ocasiones": ocasiones,
        "estilo": estilo,
        "estetica": estetica,
        "origen_etiqueta": "usuario_o_pendiente",
    }

    if metadatos_externos:
        try:
            externo = json.loads(metadatos_externos)
            if isinstance(externo, dict):
                base_payload.update(externo)
                base_payload["origen_etiqueta"] = externo.get("origen_etiqueta", "modulo_externo")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="metadatos_externos no es un JSON válido.")

    prenda = adaptar_prediccion_externa(
        payload=base_payload,
        user_id=usuario["user_id"],
        imagen_url=imagen_url,
        prenda_id=prenda_id,
    )
    guardada = storage.guardar_prenda(usuario["user_id"], prenda.to_dict())
    return {"prenda": guardada}


@app.patch("/api/closet/{user_id}/prendas/{prenda_id}")
def actualizar_prenda(user_id: str, prenda_id: str, cambios: ActualizarPrendaRequest) -> Dict[str, Any]:
    actualizado = storage.actualizar_prenda(
        user_id=user_id,
        prenda_id=prenda_id,
        cambios={k: v for k, v in cambios.model_dump().items() if v is not None},
    )
    if not actualizado:
        raise HTTPException(status_code=404, detail="Prenda no encontrada.")
    return {"prenda": actualizado}


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
