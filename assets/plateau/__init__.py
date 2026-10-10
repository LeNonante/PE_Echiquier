"""_summary_
Accès au plateau unique de l'échiquier. Le type de plateau est choisi dans le fichier .env :
    PLATEAU=simule    (par défaut, tant que la board n'est pas disponible)
    PLATEAU=physique  (sur le Raspberry Pi, une fois les capteurs câblés)
"""

from assets.gestion_env import getTypePlateau

_plateau = None


def get_plateau():
    global _plateau
    if _plateau is None:
        if getTypePlateau() == "physique":
            from assets.plateau.physique import PlateauPhysique  # import local : gpiozero
            _plateau = PlateauPhysique()
        else:
            from assets.plateau.simule import PlateauSimule
            _plateau = PlateauSimule()
    return _plateau


def est_simule():
    from assets.plateau.simule import PlateauSimule
    return isinstance(get_plateau(), PlateauSimule)
