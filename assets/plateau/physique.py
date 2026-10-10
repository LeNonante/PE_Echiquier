"""_summary_
Plateau physique : squelette à compléter quand la board sera disponible.

Il suffit de remplir lire_occupation() et afficher(), puis de mettre PLATEAU=physique dans le
fichier .env : le reste de l'application (détection des coups, Lichess) ne change pas.
"""

from assets.plateau.base import Plateau


class PlateauPhysique(Plateau):

    def __init__(self, broche_bouton=17):
        super().__init__()
        from gpiozero import Button  # import local : gpiozero n'existe que sur le Raspberry Pi

        # Même câblage que test_hardware.py
        self._bouton = Button(broche_bouton, pull_up=True, bounce_time=0.05)
        self._bouton.when_pressed = self._notifier_bouton

        # TODO : initialiser les capteurs (64 capteurs à effet Hall / ILS, via multiplexeurs
        # ou expandeurs I2C type MCP23017) et lancer une boucle de lecture qui appelle
        # self._notifier_changement() quand l'occupation change (avec un anti-rebond).

        # TODO : initialiser les LED (ruban WS2812 par exemple, une LED par case).

    def lire_occupation(self):
        raise NotImplementedError("Lecture des capteurs pas encore câblée.")

    def afficher(self, cases):
        raise NotImplementedError("Affichage LED pas encore câblé.")
