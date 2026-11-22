import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class AlmacenamientoDemo:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.usuarios_file = self.base_dir / "usuarios.json"
        self.uploads_dir = self.base_dir / "uploads"
        self.closets_dir = self.base_dir / "closets"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.closets_dir.mkdir(parents=True, exist_ok=True)
        if not self.usuarios_file.exists():
            self._escribir_json(self.usuarios_file, {"usuarios": {}})

    def _leer_json(self, ruta: Path) -> Dict[str, Any]:
        if not ruta.exists():
            return {"usuarios": {}}
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {"usuarios": {}}
        except Exception:
            return {"usuarios": {}}

    def _escribir_json(self, ruta: Path, datos: Dict[str, Any]) -> None:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        temp_ruta = ruta.parent / f".{ruta.name}.{uuid.uuid4().hex[:8]}.tmp"
        with open(temp_ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_ruta, ruta)

    @staticmethod
    def normalizar_user_id(identificador: str) -> str:
        limpio = re.sub(r"[^a-zA-Z0-9_-]+", "_", (identificador or "").strip().lower()).strip("_")
        return limpio or "usuario_demo"

    def _preparar_espacio_usuario(self, user_id: str) -> None:
        (self.uploads_dir / user_id).mkdir(parents=True, exist_ok=True)
        closet_path = self._closet_file(user_id)
        if not closet_path.exists():
            self._escribir_json(closet_path, {"user_id": user_id, "prendas": []})

    def crear_cuenta(self, identificador: str, nombre: Optional[str] = None) -> Dict[str, Any]:
        user_id = self.normalizar_user_id(identificador)
        data = self._leer_json(self.usuarios_file)
        usuarios = data.setdefault("usuarios", {})

        if user_id in usuarios:
            return {"ok": False, "error": "Ese usuario o correo ya existe. Usa 'Entrar'."}

        nombre_limpio = (nombre or "").strip()
        if not nombre_limpio:
            return {"ok": False, "error": "Escribe tu nombre para crear la cuenta."}

        usuarios[user_id] = {
            "user_id": user_id,
            "nombre": nombre_limpio,
        }
        self._escribir_json(self.usuarios_file, data)
        self._preparar_espacio_usuario(user_id)
        return {"ok": True, "usuario": usuarios[user_id]}

    def iniciar_sesion(self, identificador: str, nombre: Optional[str] = None) -> Dict[str, Any]:
        user_id = self.normalizar_user_id(identificador)
        data = self._leer_json(self.usuarios_file)
        usuarios = data.setdefault("usuarios", {})

        if user_id not in usuarios:
            return {"ok": False, "error": "No encontramos esa cuenta. Ve a 'Crear cuenta' primero."}

        if nombre and nombre.strip():
            usuarios[user_id]["nombre"] = nombre.strip()
            self._escribir_json(self.usuarios_file, data)

        self._preparar_espacio_usuario(user_id)
        return {"ok": True, "usuario": usuarios[user_id]}

    def obtener_usuario(self, user_id: str) -> Optional[Dict[str, Any]]:
        uid = self.normalizar_user_id(user_id)
        data = self._leer_json(self.usuarios_file)
        return data.get("usuarios", {}).get(uid)

    def _closet_file(self, user_id: str) -> Path:
        uid = self.normalizar_user_id(user_id)
        return self.closets_dir / f"{uid}.json"

    def listar_prendas(self, user_id: str) -> List[Dict[str, Any]]:
        uid = self.normalizar_user_id(user_id)
        ruta = self._closet_file(uid)
        if not ruta.exists():
            return []
        return self._leer_json(ruta).get("prendas", [])

    def guardar_prenda(self, user_id: str, prenda_dict: Dict[str, Any]) -> Dict[str, Any]:
        uid = self.normalizar_user_id(user_id)
        ruta = self._closet_file(uid)
        actual = self._leer_json(ruta) if ruta.exists() else {"user_id": uid, "prendas": []}
        prendas = actual.setdefault("prendas", [])
        prendas.append(prenda_dict)
        self._escribir_json(ruta, actual)
        return prenda_dict

    def eliminar_prenda(self, user_id: str, prenda_id: str) -> bool:
        uid = self.normalizar_user_id(user_id)
        ruta = self._closet_file(uid)
        if not ruta.exists():
            return False
        actual = self._leer_json(ruta)
        prendas = actual.get("prendas", [])
        nuevas = [p for p in prendas if p.get("id") != prenda_id]
        if len(nuevas) == len(prendas):
            return False
        actual["prendas"] = nuevas
        self._escribir_json(ruta, actual)
        return True

    def guardar_imagen(self, user_id: str, nombre_archivo: str, contenido: bytes) -> str:
        uid = self.normalizar_user_id(user_id)
        ext = Path(nombre_archivo or "foto.jpg").suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
            ext = ".jpg"
        nombre_unico = f"{uuid.uuid4().hex[:10]}{ext}"
        carpeta_usuario = self.uploads_dir / uid
        carpeta_usuario.mkdir(parents=True, exist_ok=True)
        destino = carpeta_usuario / nombre_unico
        destino.write_bytes(contenido)
        return f"/uploads/{uid}/{nombre_unico}"
