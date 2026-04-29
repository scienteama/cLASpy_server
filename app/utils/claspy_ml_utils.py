import inspect
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple
from typing import Any

from app.schemas.train_schema import PointCloudInfo


def get_description_from_doc(algo_class) -> str:
    """
    Récupère la description générale d'un algorithme sklearn.
    """
    doc = inspect.getdoc(algo_class.__class__)
    if not doc:
        return ""

    # Couper tout ce qui vient après "Read more" ou "Parameters"
    split_pattern = re.compile(r"(Read more|Parameters)", re.IGNORECASE)
    match = split_pattern.search(doc)
    if match:
        doc = doc[: match.start()]

    # Nettoyer les lignes vides
    lines = doc.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    return "\n".join(lines)


def parse_type_and_default(full_text: str) -> Tuple[str, Optional[str], Optional[List[str]]]:
    """
    Extrait types et valeurs par défaut d'un paramètre d'algorithme sklearn.
    """
    # Chercher default
    default_match = re.search(r"default\s*=\s*([^\s,]+)", full_text)
    default = default_match.group(1) if default_match else None

    choices_match = re.search(r"\{([^}]+)\}", full_text)
    if choices_match:
        choices = [x.strip().strip("'\"") for x in choices_match.group(1).split(",")]
    else:
        choices = None

    typeinfo = full_text
    if default_match:
        typeinfo = typeinfo[: default_match.start()]
    typeinfo = typeinfo.strip().rstrip(",")

    return typeinfo, default, choices


def get_params_from_doc(algo_class) -> Dict[str, dict]:
    """
    Récupère les paramètres d'un algorithme sklearn.
    """
    doc = inspect.getdoc(algo_class.__class__)
    if not doc:
        return {}

    # Extraire la section Parameters
    params_section = re.split(r"Parameters\n[-]+\n", doc)
    if len(params_section) < 2:
        return {}
    params_doc = params_section[1]

    params = {}
    current_param = None
    param_lines: List[str] = []

    for line in params_doc.splitlines():
        # Ligne param : type [, default=...]
        m = re.match(r"^(\w+)\s*:\s*(.*)$", line)
        if m:
            if current_param:
                # traiter le param précédent
                full_text = " ".join(param_lines).strip()
                baseinfo, default, choices = parse_type_and_default(full_text)
                params[current_param] = {
                    "baseinfo": baseinfo,
                    "values": choices,
                    "default": default,
                }
            current_param = m.group(1)
            param_lines = [m.group(2)]
        elif current_param:
            # uniquement lignes d'extension qui commencent par espace
            param_lines.append(line.strip())

    # dernier param
    if current_param:
        full_text = " ".join(param_lines).strip()
        baseinfo, default, choices = parse_type_and_default(full_text)
        params[current_param] = {"baseinfo": baseinfo, "values": choices, "default": default}

    return params


def parse_sklearn_doc(algo_class) -> Dict[str, Any]:
    """
    Fusionne description et paramètres documentés.
    """
    description = get_description_from_doc(algo_class)
    parameters = get_params_from_doc(algo_class)
    return {"description": description, "parameters": parameters}


def enrich_algorithm_params(algo_class) -> Tuple[Dict[str, dict], str]:
    """
    Fusionne get_params() avec les infos extraites de parse_sklearn_doc().
    Retourne un tuple (params, description)
    """
    runtime_params = algo_class.get_params()
    doc_info = parse_sklearn_doc(algo_class)
    enriched = {}
    doc_params = doc_info.get("parameters", {})

    for key, value in runtime_params.items():
        enriched[key] = {"value": value}

        if key in doc_params:
            info = doc_params[key]
            if info.get("baseinfo"):
                enriched[key]["typeinfo"] = info["baseinfo"]
            if info.get("values"):
                enriched[key]["choices"] = info["values"]
            if info.get("default"):
                enriched[key]["default"] = info["default"]

    # Retourne description séparément
    description = doc_info.get("description", "")

    return enriched, description


def parse_cloud_points_info(text: str, file_name: str) -> PointCloudInfo:
    """
    Parse le retour de "ClaspyTrainer.point_cloud_info()" pour générer un PointCloudInfo
    """
    ext = Path(file_name).suffix.lower()
    if ext not in (".las", ".csv"):
        raise ValueError(f"Extension de fichier non supportée : {ext}")

    points_match = re.search(
        r"Number of points:\s*([\d]+(?:[.,\s][\d]{3})*)",
        text,
        re.IGNORECASE,
    )
    if not points_match:
        raise ValueError("Impossible d'extraire le nombre de points")

    version_match = re.search(r"LAS Version:\s*([\d.]+)", text, re.IGNORECASE)
    format_match = re.search(r"LAS point format:\s*(\d+)", text, re.IGNORECASE)

    return PointCloudInfo(
        file_name=file_name,
        file_type=ext,
        points_number=int(re.sub(r"[^\d]", "", points_match.group(1))),
        las_version=float(version_match.group(1)) if version_match else None,
        las_point_format=int(format_match.group(1)) if format_match else None,
    )
