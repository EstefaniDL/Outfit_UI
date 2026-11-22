from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Prenda:
    id: str
    user_id: str
    imagen_url: str
    tipo_articulo: str
    color_principal: str
    colores_secundarios: List[str] = field(default_factory=list)
    tono: str = "medio"
    estampado: str = "liso"
    material: str = "algodon"
    corte: str = "regular"
    largo: str = "regular"
    estilo: List[str] = field(default_factory=lambda: ["casual"])
    estetica: List[str] = field(default_factory=lambda: ["clasico"])
    temporada: List[str] = field(default_factory=lambda: ["todo_el_ano"])
    clima: List[str] = field(default_factory=lambda: ["templado"])
    ocasiones: List[str] = field(default_factory=lambda: ["diario"])
    formalidad: str = "casual"
    etiquetas_confirmadas: bool = False
    origen_etiqueta: str = "pendiente_modelo"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "imagen_url": self.imagen_url,
            "tipo_articulo": self.tipo_articulo,
            "color_principal": self.color_principal,
            "colores_secundarios": self.colores_secundarios,
            "tono": self.tono,
            "estampado": self.estampado,
            "material": self.material,
            "corte": self.corte,
            "largo": self.largo,
            "estilo": self.estilo,
            "estetica": self.estetica,
            "temporada": self.temporada,
            "clima": self.clima,
            "ocasiones": self.ocasiones,
            "formalidad": self.formalidad,
            "etiquetas_confirmadas": self.etiquetas_confirmadas,
            "origen_etiqueta": self.origen_etiqueta,
        }


def _a_lista(valor: Any, por_defecto: List[str]) -> List[str]:
    if isinstance(valor, list) and valor:
        return [str(x).strip() for x in valor if str(x).strip()]
    if isinstance(valor, str) and valor.strip():
        return [parte.strip() for parte in valor.split("|") if parte.strip()]
    return list(por_defecto)


def adaptar_prediccion_externa(
    payload: Dict[str, Any],
    user_id: str,
    imagen_url: str,
    prenda_id: str,
) -> Prenda:
    tipo = (
        payload.get("tipo_articulo")
        or payload.get("tipo")
        or "superior"
    )
    color = (
        payload.get("color_principal")
        or payload.get("color_nombre")
        or "sin_definir"
    )

    return Prenda(
        id=prenda_id,
        user_id=user_id,
        imagen_url=imagen_url,
        tipo_articulo=str(tipo).strip().lower(),
        color_principal=str(color).strip().lower(),
        colores_secundarios=_a_lista(payload.get("colores_secundarios"), []),
        tono=str(payload.get("tono", "medio")).strip().lower(),
        estampado=str(payload.get("estampado", "liso")).strip().lower(),
        material=str(payload.get("material", "algodon")).strip().lower(),
        corte=str(payload.get("corte", "regular")).strip().lower(),
        largo=str(payload.get("largo", "regular")).strip().lower(),
        estilo=_a_lista(payload.get("estilo"), ["casual"]),
        estetica=_a_lista(payload.get("estetica"), ["clasico"]),
        temporada=_a_lista(payload.get("temporada"), ["todo_el_ano"]),
        clima=_a_lista(payload.get("clima"), ["templado"]),
        ocasiones=_a_lista(payload.get("ocasiones"), ["diario"]),
        formalidad=str(payload.get("formalidad", "casual")).strip().lower(),
        etiquetas_confirmadas=bool(payload.get("etiquetas_confirmadas", False)),
        origen_etiqueta=str(payload.get("origen_etiqueta", "pendiente_modelo")),
    )
