"""_summary_
Interface commune à tous les plateaux (simulé ou physique).

Le reste de l'application ne parle qu'à cette classe : elle ne sait pas si les capteurs sont
réels ou simulés. Brancher la vraie board consistera à écrire une sous-classe de Plateau.

Le plateau sait faire trois choses :
    - lire l'occupation des 64 cases (capteurs) ;
    - afficher des indications sur des cases (LED) ;
    - prévenir quand une case change ou quand le bouton de validation est pressé.
"""

from abc import ABC, abstractmethod

# Rôles possibles d'une case dans afficher() : à chaque rôle sa couleur de LED.
ROLES = ("depart", "arrivee", "prise", "erreur")


class Plateau(ABC):

    def __init__(self):
        self._abonnes_changement = []
        self._abonnes_bouton = []

    # ---------- Abonnements ----------
    def sur_changement(self, fonction):
        """Appelle fonction(occupation) à chaque fois qu'une pièce est levée ou posée."""
        self._abonnes_changement.append(fonction)

    def sur_bouton(self, fonction):
        """Appelle fonction() quand le joueur appuie sur le bouton de validation du coup."""
        self._abonnes_bouton.append(fonction)

    def desabonner(self, fonction):
        for abonnes in (self._abonnes_changement, self._abonnes_bouton):
            if fonction in abonnes:
                abonnes.remove(fonction)

    def _notifier_changement(self):
        occupation = self.lire_occupation()
        for fonction in list(self._abonnes_changement):
            fonction(occupation)

    def _notifier_bouton(self):
        for fonction in list(self._abonnes_bouton):
            fonction()

    # ---------- À implémenter par chaque plateau ----------
    @abstractmethod
    def lire_occupation(self):
        """
        Returns:
            frozenset[int]: Cases (entiers python-chess) sur lesquelles une pièce est posée.
        """

    @abstractmethod
    def afficher(self, cases):
        """
        Remplace les indications affichées sur le plateau.

        Args:
            cases (dict[int, str]): Case -> rôle (voir ROLES). Un dict vide éteint tout.
        """

    def effacer(self):
        self.afficher({})
