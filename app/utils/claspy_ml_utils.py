
import inspect
import re

def parse_sklearn_doc(algo_class):
        """
        Extrait les infos documentaires des paramètres d'un modèle sklearn :
        - baseinfo
        - valeurs possibles
        - valeur par défaut
        """
        doc = inspect.getdoc(algo_class.__class__)
        if not doc:
            return {}

        params = {}

        # Regex pour extraire les lignes "param : type, default=value"
        pattern = re.compile(
            r"^(\w+)\s*:\s*([^\n]+?)(?:,?\s*default\s*=\s*([^\n]+))?$",
            re.MULTILINE
        )

        for match in pattern.finditer(doc):
            name, typeinfo, default = match.groups()
            typeinfo = typeinfo.strip()
            default = default.strip() if default else None

            # Extraction des valeurs possibles entre accolades
            choices_match = re.search(r"\{([^}]+)\}", typeinfo)
            if choices_match:
                choices = [x.strip().strip('"').strip("'") for x in choices_match.group(1).split(",")]
            else:
                choices = None

            params[name] = {
                "baseinfo": typeinfo,
                "values": choices,
                "default": default
            }

        return params

def enrich_algorithm_params(algo_class):
    """
    Fusionne get_params() avec les infos extraites de parse_sklearn_doc(),
    uniquement pour les clés existantes dans get_params().
    """
    runtime_params = algo_class.get_params()
    doc_info = parse_sklearn_doc(algo_class)
    enriched = {}
    for key, value in runtime_params.items():
        enriched[key] = {"value": value}
        if key in doc_info:
            info = doc_info[key]
            if info.get("baseinfo"):
                enriched[key]["typeinfo"] = info["baseinfo"]
            if info.get("values"):
                enriched[key]["choices"] = info["values"]
            if info.get("default"):
                enriched[key]["default"] = info["default"]
    return enriched