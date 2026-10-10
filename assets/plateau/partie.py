"""_summary_
Fait le lien entre un plateau (simulé ou physique) et une partie d'échecs.

    Lichess --(coups adverses)--> PartiePhysique --(LED : quoi déplacer)--> Plateau
    Lichess <--(coup validé)----- PartiePhysique <--(capteurs + bouton)---- Plateau

Une seule partie est active à la fois : il n'y a qu'un plateau.
"""

import threading
import chess

from assets.plateau.detection import (
    CoupIllisible, occupation_de, cases_en_ecart, deduire_coup, cases_a_manipuler,
)

STATUTS_EN_COURS = ("created", "started")

LIBELLES_FIN = {
    "mate": "Échec et mat.",
    "resign": "Abandon.",
    "stalemate": "Pat.",
    "timeout": "Temps écoulé.",
    "outoftime": "Temps écoulé.",
    "draw": "Partie nulle.",
    "aborted": "Partie annulée.",
    "noStart": "Partie non commencée.",
}


class PartiePhysique:
    """
    Args:
        plateau (Plateau): Plateau sur lequel se joue la partie.
        envoyer_coup (callable | None): fonction(uci) appelée quand le joueur valide un coup ;
            doit lever une exception si le coup est refusé. None : partie locale, le coup est
            simplement appliqué.
        mode (str): "lichess" ou "locale" (affiché sur la page du simulateur).
        game_id (str | None): ID Lichess de la partie.
    """

    def __init__(self, plateau, envoyer_coup=None, mode="locale", game_id=None):
        self.plateau = plateau
        self.mode = mode
        self.game_id = game_id
        self._envoyer_coup = envoyer_coup
        # RLock : en partie locale, le bouton applique le coup directement (appel réentrant)
        self._verrou = threading.RLock()

        # Couleur jouée sur le plateau. None : les deux camps (partie locale).
        self.couleur = None
        # En partie Lichess, on attend de connaître sa couleur avant d'accepter un coup.
        self.pret = envoyer_coup is None
        self.board = chess.Board()
        self.terminee = False
        self.message = "Partie locale : jouez les deux camps." if self.pret else "Connexion à Lichess…"

        # Synchro = le plateau physique correspond à self.board (au coup du joueur près).
        self.synchro = False
        self._coup_a_reproduire = None  # (position avant, coup) d'un coup adverse
        self._cases_levees = set()
        self._erreur_affichee = False
        self._occupation_precedente = plateau.lire_occupation()

        plateau.sur_changement(self._sur_changement)
        plateau.sur_bouton(self._sur_bouton)
        with self._verrou:
            self._verifier_synchro(self._occupation_precedente)

    # ---------- Entrées venant de Lichess (ou de la partie locale) ----------
    def definir_couleur(self, couleur):
        with self._verrou:
            self.couleur = couleur
            self.pret = True
            self._verifier_synchro(self.plateau.lire_occupation())

    def appliquer_coups(self, coups_uci, statut="started", gagnant=None):
        """
        Met à jour la partie avec la liste complète des coups joués (format Lichess).

        Args:
            coups_uci (str): Coups séparés par des espaces, ex. "e2e4 e7e5".
            statut (str): Statut Lichess de la partie.
            gagnant (str | None): "white", "black" ou None.
        """
        with self._verrou:
            if self.terminee:
                return
            nouveau = chess.Board()
            for uci in coups_uci.split():
                nouveau.push_uci(uci)
            if nouveau.move_stack != self.board.move_stack:
                self._nouvelle_position(nouveau)

            if statut not in STATUTS_EN_COURS:
                self.terminer(self._libelle_fin(LIBELLES_FIN.get(statut, "Partie terminée."), gagnant))
            elif self.mode == "locale" and nouveau.outcome() is not None:
                issue = nouveau.outcome()
                gagnant = None if issue.winner is None else ("white" if issue.winner else "black")
                libelle = "Échec et mat." if issue.termination == chess.Termination.CHECKMATE else "Partie nulle."
                self.terminer(self._libelle_fin(libelle, gagnant))

    def terminer(self, message="Partie terminée."):
        with self._verrou:
            self.terminee = True
            self.message = message
            self.plateau.effacer()
            self.plateau.desabonner(self._sur_changement)
            self.plateau.desabonner(self._sur_bouton)

    # ---------- Entrées venant du plateau ----------
    def _sur_changement(self, occupation):
        with self._verrou:
            if self.terminee:
                return
            self._cases_levees |= self._occupation_precedente - occupation
            self._occupation_precedente = occupation

            if not self.synchro:
                self._verifier_synchro(occupation)
                return
            if occupation == occupation_de(self.board):
                self._cases_levees = set()  # le joueur a tout reposé comme avant
            if self._erreur_affichee:
                self._erreur_affichee = False
                self.plateau.effacer()
                self.message = self._message_tour()

    def _sur_bouton(self):
        with self._verrou:
            if self.terminee:
                return
            if not self.pret:
                self.message = "Connexion à Lichess en cours, patientez."
                return
            occupation = self.plateau.lire_occupation()
            if not self.synchro:
                self._verifier_synchro(occupation)
                self.message = "Le plateau ne correspond pas à la partie : corrigez les cases signalées."
                return
            if not self._est_mon_tour():
                self.message = "Ce n'est pas votre tour."
                return
            try:
                coup = deduire_coup(self.board, occupation, self._cases_levees)
            except CoupIllisible as e:
                self._signaler_erreur(str(e), e.cases)
                return
            uci = coup.uci()
            if self._envoyer_coup is None:
                self.appliquer_coups(" ".join(m.uci() for m in self.board.move_stack + [coup]))
                return
            self.message = f"Coup {uci} envoyé à Lichess…"

        # Appel réseau hors du verrou : le flux Lichess doit pouvoir mettre la partie à jour en parallèle
        try:
            self._envoyer_coup(uci)
        except Exception as e:
            with self._verrou:
                self._signaler_erreur(f"Coup {uci} refusé par Lichess : {e}", {coup.from_square, coup.to_square})

    # ---------- Logique interne (appelée verrou pris) ----------
    def _nouvelle_position(self, nouveau):
        avant = nouveau.copy()
        dernier = avant.pop() if avant.move_stack else None
        self.board = nouveau
        occupation = self.plateau.lire_occupation()
        self._occupation_precedente = occupation
        self._cases_levees = set()
        self._erreur_affichee = False
        # Coup de l'adversaire : le joueur doit le reproduire sur le plateau
        joue_par_adversaire = dernier is not None and not self._est_mon_tour(avant)
        self._coup_a_reproduire = (avant, dernier) if joue_par_adversaire else None
        self.synchro = False
        self._verifier_synchro(occupation)

    def _verifier_synchro(self, occupation):
        """Passe en synchro si le plateau correspond à la partie, sinon affiche quoi corriger."""
        prise_a_retirer = set()
        indications = {case: "erreur" for case in cases_en_ecart(self.board, occupation)}
        if self._coup_a_reproduire is not None:
            avant, coup = self._coup_a_reproduire
            indications.update(cases_a_manipuler(avant, coup))
            if avant.is_capture(coup) and not avant.is_en_passant(coup):
                # Les capteurs ne voient pas la différence entre la pièce prise et celle qui
                # prend : on exige que la case ait été vidée au moins une fois.
                prise_a_retirer = {coup.to_square} - self._cases_levees

        if occupation == occupation_de(self.board) and not prise_a_retirer:
            self.synchro = True
            self._coup_a_reproduire = None
            self._cases_levees = set()
            self.plateau.effacer()
            self.message = self._message_tour()
        else:
            self.synchro = False
            self.plateau.afficher(indications)
            if self._coup_a_reproduire is not None:
                self.message = f"Reproduisez le coup adverse : {self._coup_a_reproduire[1].uci()}."
            elif self.pret:
                self.message = "Replacez les pièces sur les cases signalées."

    def _signaler_erreur(self, message, cases):
        self.message = message
        self.plateau.afficher({case: "erreur" for case in cases})
        self._erreur_affichee = True

    def _est_mon_tour(self, board=None):
        board = board or self.board
        return self.couleur is None or board.turn == self.couleur

    def _message_tour(self):
        if not self.pret:
            return "Connexion à Lichess…"
        if self.couleur is None:
            return f"Trait aux {'Blancs' if self.board.turn else 'Noirs'} : jouez puis appuyez sur le bouton."
        if self._est_mon_tour():
            return "À vous de jouer : déplacez votre pièce puis appuyez sur le bouton."
        return "En attente du coup adverse."

    @staticmethod
    def _libelle_fin(libelle, gagnant):
        if gagnant == "white":
            return f"{libelle} Victoire des Blancs."
        if gagnant == "black":
            return f"{libelle} Victoire des Noirs."
        return libelle

    # ---------- Pour la page web ----------
    def etat(self):
        with self._verrou:
            board = chess.Board()
            coups_san = []
            for coup in self.board.move_stack:
                coups_san.append(board.san(coup))
                board.push(coup)
            couleur = {None: None, chess.WHITE: "white", chess.BLACK: "black"}[self.couleur]
            return {
                "mode": self.mode,
                "game_id": self.game_id,
                "couleur": couleur,
                "message": self.message,
                "trait": "white" if self.board.turn else "black",
                "coups": coups_san,
                "fen": self.board.fen(),
                "synchro": self.synchro,
                "terminee": self.terminee,
            }


# ---------- Partie active (une seule à la fois) ----------
_partie_active = None
_verrou_global = threading.Lock()


def get_partie_active():
    return _partie_active


def _remplacer_partie(partie):
    global _partie_active
    if _partie_active is not None and not _partie_active.terminee:
        _partie_active.terminer("Partie quittée.")
    _partie_active = partie


def demarrer_partie_locale(plateau):
    """Partie sans Lichess : le joueur joue les deux camps sur le plateau."""
    with _verrou_global:
        partie = PartiePhysique(plateau, envoyer_coup=None, mode="locale")
        _remplacer_partie(partie)
        return partie


def demarrer_partie_lichess(client, plateau, game_id):
    """Relie le plateau à une partie Lichess (ne fait rien si c'est déjà la partie active)."""
    with _verrou_global:
        if _partie_active is not None and _partie_active.game_id == game_id and not _partie_active.terminee:
            return _partie_active
        mon_id = client.account.get()['id']
        partie = PartiePhysique(
            plateau,
            envoyer_coup=lambda uci: client.board.make_move(game_id, uci),
            mode="lichess",
            game_id=game_id,
        )
        _remplacer_partie(partie)
        threading.Thread(target=_suivre_lichess, args=(partie, client, game_id, mon_id), daemon=True).start()
        return partie


def _suivre_lichess(partie, client, game_id, mon_id):
    """Thread : écoute le flux Lichess de la partie et le transmet à la PartiePhysique."""
    try:
        for event in client.board.stream_game_state(game_id):
            if partie.terminee:
                break
            etype = event.get('type')
            if etype == 'gameFull':
                blancs = event.get('white', {})
                partie.definir_couleur(chess.WHITE if blancs.get('id') == mon_id else chess.BLACK)
                state = event.get('state', {})
            elif etype == 'gameState':
                state = event
            else:
                continue  # chatLine, opponentGone...
            partie.appliquer_coups(state.get('moves', ''), state.get('status', 'started'), state.get('winner'))
            if partie.terminee:
                break
    except Exception as e:
        if not partie.terminee:
            partie.terminer(f"Connexion à Lichess perdue : {e}")
