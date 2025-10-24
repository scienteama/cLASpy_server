try: 
    import cLASpy_ML
    from cLASpy_ML import cLASpy_Classes 
except ModuleNotFoundError: 
    cLASpy_ML = None
    cLASpy_Classes = None

class ClaspyMLService:
    """
    Service pour interagir avec le plugin cLASpy_ML.
    """
    
    def __init__(self):
        if cLASpy_ML != None:
            self.plugin = cLASpy_ML
            self.classes = cLASpy_Classes
        else:
            self.plugin = None
            self.classes = None

    def get_core_version(self) -> str:
        if self.classes != None:
            
            return f"core_version : {self.classes.cLASpy_Core_version}"
        else:
            return "Plugin cLASpy_ML non chargé."
