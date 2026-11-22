from itertools import product
from typing import Any, Dict, List, Optional, Tuple

NEUTROS = {
    "blanco",
    "negro",
    "gris",
    "gris_claro",
    "gris_oscuro",
    "beige",
    "crema",
    "marfil",
    "camel",
    "cafe",
    "marron",
    "azul_marino",
    "sin_definir",
}

COMPLEMENTARIOS = {
    ("azul", "naranja"),
    ("naranja", "azul"),
    ("azul", "anaranjado"),
    ("anaranjado", "azul"),
    ("amarillo", "violeta"),
    ("violeta", "amarillo"),
    ("amarillo", "morado"),
    ("morado", "amarillo"),
    ("rojo", "verde"),
    ("verde", "rojo"),
}

COLORES_LLAMATIVOS_FORMAL = {
    "naranja",
    "anaranjado",
    "amarillo",
    "rojo",
    "rosa_neon",
    "fosforescente",
    "verde_neon",
}

PRENDAS_NO_FORMALES = {"short", "bermuda", "deportivo", "leggins", "mallones"}


def _es_neutro(color: str) -> bool:
    c = (color or "").strip().lower()
    return c in NEUTROS or any(k in c for k in ("gris", "beige", "crema", "camel", "marino", "blanco", "negro"))


def _son_complementarios(c1: str, c2: str) -> bool:
    a = (c1 or "").strip().lower()
    b = (c2 or "").strip().lower()
    if (a, b) in COMPLEMENTARIOS:
        return True
    for ka, kb in COMPLEMENTARIOS:
        if ka in a and kb in b:
            return True
    return False


def _lista_lower(val: Any) -> List[str]:
    if isinstance(val, list):
        return [str(x).strip().lower() for x in val if str(x).strip()]
    if isinstance(val, str) and val.strip():
        return [x.strip().lower() for x in val.split("|") if x.strip()]
    return []


def evaluar_outfit(
    piezas: List[Dict[str, Any]],
    ocasion: str,
    clima: str,
) -> Tuple[float, List[str], str]:
    """
    Evalúa un conjunto de prendas bajo las reglas definidas y devuelve:
    (puntaje, razones, descripcion_contextual)
    """
    puntaje = 5.0
    razones: List[str] = []

    ocasion_n = (ocasion or "diario").strip().lower()
    clima_n = (clima or "templado").strip().lower()

    colores = [(p.get("color_principal") or "sin_definir").strip().lower() for p in piezas]
    colores_unicos = list(dict.fromkeys(colores))
    tonos = [(p.get("tono") or "medio").strip().lower() for p in piezas]
    estampados = [(p.get("estampado") or "liso").strip().lower() for p in piezas]
    formalidades = [(p.get("formalidad") or "casual").strip().lower() for p in piezas]
    cortes = [(p.get("corte") or "regular").strip().lower() for p in piezas]
    tipos = [(p.get("tipo_articulo") or "").strip().lower() for p in piezas]

    # R01: Límite de colores lisos (máx. 3 colores distintos cuando son lisas)
    todas_lisas = all(e == "liso" for e in estampados)
    if todas_lisas and len(colores_unicos) > 3:
        puntaje -= 1.8
        razones.append("Supera el límite sugerido de 3 colores distintos en prendas lisas.")
    elif todas_lisas:
        puntaje += 0.8
        razones.append("Respeta el equilibrio de hasta 3 colores en prendas lisas.")

    # R02: Armonía complementaria o presencia de neutros
    if any(_es_neutro(c) for c in colores):
        puntaje += 0.8
        razones.append("Incluye tonos neutros que facilitan el balance cromático.")
    for i in range(len(colores)):
        for j in range(i + 1, len(colores)):
            if _son_complementarios(colores[i], colores[j]):
                puntaje += 1.0
                razones.append(f"Combina colores complementarios ({colores[i]} y {colores[j]}).")

    # R04 & R05: Contraste claro-oscuro y contraste cualitativo (neutro/suave vs. acento/estampado)
    tiene_claro = any(t == "claro" for t in tonos)
    tiene_oscuro = any(t == "oscuro" for t in tonos)
    if tiene_claro and tiene_oscuro:
        puntaje += 0.9
        razones.append("Presenta contraste claro-oscuro que aporta profundidad visual.")

    tiene_estampado = any(e != "liso" for e in estampados)
    tiene_suave_o_neutro = any(t == "suave" or _es_neutro(c) for t, c in zip(tonos, colores))
    if tiene_estampado and tiene_suave_o_neutro:
        puntaje += 0.7
        razones.append("Equilibra estampados con piezas neutras o de tono suave.")

    # R07, R11, R12: Formalidad y ocasión
    coinciden_ocasion = sum(1 for p in piezas if ocasion_n in _lista_lower(p.get("ocasiones")))
    if coinciden_ocasion >= 2:
        puntaje += 1.0
        razones.append(f"Adecuado para la ocasión '{ocasion_n.replace('_', ' ')}'.")

    if ocasion_n in {"trabajo", "evento_formal"}:
        if any(c in COLORES_LLAMATIVOS_FORMAL for c in colores):
            puntaje -= 2.2
            razones.append("Contiene colores muy llamativos/intensos poco recomendables en entorno formal.")
        if any(f == "casual" for f in formalities) and not any(f == "formal" for f in formalities):
            puntaje -= 1.2
            razones.append("Nivel de formalidad más casual que el requerido para la ocasión.")
        if any(t in PRENDAS_NO_FORMALES for t in tipos):
            puntaje -= 2.5
            razones.append("Incluye un tipo de prenda informal fuera de código formal.")

    # R13, R14, R15: Clima y capas
    coinciden_clima = sum(1 for p in piezas if clima_n in _lista_lower(p.get("clima")))
    if coinciden_clima >= 2:
        puntaje += 1.0
        razones.append(f"Compatible con el clima '{clima_n}'.")

    tiene_exterior = "exterior" in tipos
    if clima_n in {"frio", "lluvioso"}:
        if tiene_exterior:
            puntaje += 1.1
            razones.append("Incorpora prenda exterior para abrigo/protección en clima frío o lluvioso.")
        else:
            puntaje -= 1.0
            razones.append("Falta una prenda exterior o capa de abrigo para clima frío/lluvioso.")
    elif clima_n == "calido" and tiene_exterior:
        puntaje -= 1.2
        razones.append("Incluye prenda exterior que puede resultar pesada en clima cálido.")

    # R18: Proporciones (evitar exceso de volumen sin contraste)
    if cortes.count("holgado") >= 2:
        puntaje -= 0.7
        razones.append("Combina múltiples prendas holgadas; conviene equilibrar con un corte regular o ajustado.")
    elif "holgado" in cortes and ("ajustado" in cortes or "regular" in cortes):
        puntaje += 0.6
        razones.append("Equilibra volúmenes combinando corte holgado con ajuste regular o entallado.")

    puntaje_final = round(max(1.0, min(10.0, puntaje)), 1)
    if not razones:
        razones.append("Combinación funcional con estructura completa de prendas.")

    etiqueta_ocasion = ocasion_n.replace("_", " ")
    etiqueta_clima = clima_n.replace("_", " ")
    capa_txt = " con capa exterior de apoyo" if tiene_exterior else ""
    contraste_txt = " y contraste claro-oscuro" if (tiene_claro and tiene_oscuro) else ""
    descripcion = (
        f"Outfit pensado para {etiqueta_ocasion} en clima {etiqueta_clima}{capa_txt}: "
        f"reúne {', '.join(colores_unicos)}{contraste_txt}, con una calificación de {puntaje_final}/10."
    )
    return puntaje_final, razones, descripcion


def recomendar_outfits(
    prendas: List[Dict[str, Any]],
    ocasion: str = "diario",
    clima: str = "templado",
    limite: int = 5,
) -> List[Dict[str, Any]]:
    """
    Genera una selección curada y variada de outfits (nunca el producto cartesiano completo).
    """
    superiores = [p for p in prendas if (p.get("tipo_articulo") or "").lower() == "superior"]
    inferiores = [p for p in prendas if (p.get("tipo_articulo") or "").lower() == "inferior"]
    calzados = [p for p in prendas if (p.get("tipo_articulo") or "").lower() == "calzado"]
    exteriores = [p for p in prendas if (p.get("tipo_articulo") or "").lower() == "exterior"]

    if not superiores or not inferiores:
        return []

    candidatos: List[Dict[str, Any]] = []
    lista_cal = calzados if calzados else [None]
    lista_ext = exteriores if (clima in {"frio", "lluvioso"} and exteriores) else [None]

    for sup, inf, cal, ext in product(superiores, inferiores, lista_cal, lista_ext):
        piezas = [sup, inf] + ([ext] if ext else []) + ([cal] if cal else [])
        puntaje, razones, descripcion = evaluar_outfit(piezas, ocasion=ocasion, clima=clima)
        candidatos.append(
            {
                "calificacion": puntaje,
                "descripcion": descripcion,
                "razones": razones,
                "piezas": piezas,
                "_ids": tuple(p.get("id") for p in piezas),
            }
        )

    candidatos.sort(key=lambda x: x["calificacion"], reverse=True)

    # Selección curada con diversidad para no repetir siempre la misma prenda superior/inferior
    seleccionados: List[Dict[str, Any]] = []
    uso_superior: Dict[str, int] = {}
    uso_inferior: Dict[str, int] = {}

    for cand in candidatos:
        id_sup = cand["piezas"][0].get("id", "")
        id_inf = cand["piezas"][1].get("id", "")
        if uso_superior.get(id_sup, 0) >= 2 and len(candidatos) > limite:
            continue
        if uso_inferior.get(id_inf, 0) >= 2 and len(candidatos) > limite:
            continue
        seleccionados.append({k: v for k, v in cand.items() if k != "_ids"})
        uso_superior[id_sup] = uso_superior.get(id_sup, 0) + 1
        uso_inferior[id_inf] = uso_inferior.get(id_inf, 0) + 1
        if len(seleccionados) >= limite:
            break

    return seleccionados
