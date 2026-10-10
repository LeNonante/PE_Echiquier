"""_summary_
Plateau simulé : remplace la board tant qu'elle n'est pas disponible.

Il simule le monde réel : de vraies pièces posées sur des cases, que l'on peut prendre en main
et reposer ailleurs (depuis la page /simulateur). Mais, comme les vrais capteurs, il ne donne
au reste de l'application que l'occupation des cases, jamais le type des pièces.
"""

import threading
import chess

from assets.plateau.base import Plateau


class PlateauSimule(Plateau):

    def __init__(self):
        super().__init__()
        self._verrou = threading.Lock()  # la page web et le suivi Lichess tournent dans des threads différents
        self._affichage = {}
        self._pieces = {}
        self._main = []
        self._hors_plateau = []
        self.reinitialiser()

    # ---------- Interface Plateau ----------
    def lire_occupation(self):
        with self._verrou:
            return frozenset(self._pieces)

    def afficher(self, cases):
        with self._verrou:
            self._affichage = dict(cases)

    # ---------- Actions du « joueur » (appelées par la page /simulateur) ----------
    def reinitialiser(self, fen=chess.STARTING_FEN):
        """Repose toutes les pièces selon une position (position de départ par défaut)."""
        with self._verrou:
            self._pieces = {case: piece.symbol() for case, piece in chess.Board(fen).piece_map().items()}
            self._main = []
            self._hors_plateau = []
        self._notifier_changement()

    def cliquer_case(self, case, index_main=None):
        """
        Simule la main du joueur sur une case :
            - case vide : on y pose la pièce tenue (la dernière prise, ou celle d'indice index_main) ;
            - case occupée par une pièce adverse à celle tenue : prise, la pièce adverse est mise
              hors plateau puis remplacée (deux changements, comme pour de vrai) ;
            - sinon : on prend la pièce en main.
        """
        with self._verrou:
            if self._main and (index_main is None or not 0 <= index_main < len(self._main)):
                index_main = len(self._main) - 1
            tenue = self._main[index_main] if self._main else None
            sur_case = self._pieces.get(case)
            prise = tenue is not None and sur_case is not None and tenue.isupper() != sur_case.isupper()

            if sur_case is not None:
                if prise:
                    self._hors_plateau.append(self._pieces.pop(case))
                else:
                    self._main.append(self._pieces.pop(case))
            elif tenue is not None:
                self._pieces[case] = self._main.pop(index_main)
            else:
                return  # rien en main, rien à poser
        self._notifier_changement()

        if prise:
            with self._verrou:
                self._pieces[case] = self._main.pop(index_main)
            self._notifier_changement()

    def poser_hors_plateau(self, index_main):
        """Met de côté une pièce tenue en main (pièce capturée)."""
        with self._verrou:
            if 0 <= index_main < len(self._main):
                self._hors_plateau.append(self._main.pop(index_main))

    def reprendre_hors_plateau(self, index):
        """Reprend en main une pièce mise de côté (pour une promotion par exemple)."""
        with self._verrou:
            if 0 <= index < len(self._hors_plateau):
                self._main.append(self._hors_plateau.pop(index))

    def appuyer_bouton(self):
        self._notifier_bouton()

    def etat(self):
        """État complet pour la page web (sérialisable en JSON)."""
        with self._verrou:
            return {
                "pieces": {chess.square_name(c): s for c, s in self._pieces.items()},
                "main": list(self._main),
                "hors_plateau": list(self._hors_plateau),
                "affichage": {chess.square_name(c): r for c, r in self._affichage.items()},
            }
