import chess

from assets.plateau.simule import PlateauSimule
from assets.plateau.partie import PartiePhysique


def deplacer(plateau, depart, arrivee):
    """Le joueur prend la pièce sur depart et la pose sur arrivee (prise comprise)."""
    plateau.cliquer_case(depart)
    plateau.cliquer_case(arrivee)


class FauxLichess:
    """Remplace client.board.make_move : enregistre les coups envoyés."""

    def __init__(self, refuser=False):
        self.coups = []
        self.refuser = refuser

    def make_move(self, uci):
        if self.refuser:
            raise Exception("Not your turn")
        self.coups.append(uci)


# ---------- Partie locale ----------
def test_partie_locale_enchaine_les_coups():
    plateau = PlateauSimule()
    partie = PartiePhysique(plateau)
    deplacer(plateau, chess.E2, chess.E4)
    plateau.appuyer_bouton()
    deplacer(plateau, chess.E7, chess.E5)
    plateau.appuyer_bouton()
    assert [m.uci() for m in partie.board.move_stack] == ["e2e4", "e7e5"]
    assert partie.synchro


def test_partie_locale_coup_illegal_allume_les_cases_en_erreur():
    plateau = PlateauSimule()
    partie = PartiePhysique(plateau)
    deplacer(plateau, chess.E2, chess.E5)
    plateau.appuyer_bouton()
    assert partie.board.move_stack == []
    assert plateau.etat()["affichage"] == {"e2": "erreur", "e5": "erreur"}
    # Le joueur corrige : l'erreur s'éteint
    deplacer(plateau, chess.E5, chess.E2)
    assert plateau.etat()["affichage"] == {}


def test_mat_du_berger_termine_la_partie():
    plateau = PlateauSimule()
    partie = PartiePhysique(plateau)
    for depart, arrivee in [(chess.E2, chess.E4), (chess.E7, chess.E5), (chess.F1, chess.C4),
                            (chess.B8, chess.C6), (chess.D1, chess.H5), (chess.G8, chess.F6),
                            (chess.H5, chess.F7)]:
        deplacer(plateau, depart, arrivee)
        plateau.appuyer_bouton()
    assert partie.terminee
    assert "Victoire des Blancs" in partie.message


# ---------- Partie Lichess (simulée) ----------
def partie_lichess(couleur=chess.WHITE, refuser=False):
    plateau = PlateauSimule()
    lichess = FauxLichess(refuser)
    partie = PartiePhysique(plateau, envoyer_coup=lichess.make_move, mode="lichess", game_id="test")
    partie.definir_couleur(couleur)
    return plateau, lichess, partie


def test_coup_du_joueur_envoye_a_lichess():
    plateau, lichess, partie = partie_lichess()
    deplacer(plateau, chess.G1, chess.F3)
    plateau.appuyer_bouton()
    assert lichess.coups == ["g1f3"]


def test_pas_de_coup_envoye_hors_de_son_tour():
    plateau, lichess, partie = partie_lichess(couleur=chess.BLACK)
    deplacer(plateau, chess.E2, chess.E4)
    plateau.appuyer_bouton()
    assert lichess.coups == []
    assert partie.message == "Ce n'est pas votre tour."


def test_coup_refuse_par_lichess():
    plateau, lichess, partie = partie_lichess(refuser=True)
    deplacer(plateau, chess.E2, chess.E4)
    plateau.appuyer_bouton()
    assert "refusé" in partie.message
    assert plateau.etat()["affichage"] == {"e2": "erreur", "e4": "erreur"}


def test_coup_adverse_a_reproduire():
    plateau, lichess, partie = partie_lichess()
    deplacer(plateau, chess.E2, chess.E4)
    plateau.appuyer_bouton()
    partie.appliquer_coups("e2e4")  # Lichess confirme notre coup
    assert partie.synchro

    partie.appliquer_coups("e2e4 e7e5")  # l'adversaire joue
    assert not partie.synchro
    assert plateau.etat()["affichage"] == {"e7": "depart", "e5": "arrivee"}

    deplacer(plateau, chess.E7, chess.E5)
    assert partie.synchro
    assert plateau.etat()["affichage"] == {}


def test_prise_adverse_exige_de_retirer_la_piece_prise():
    plateau, lichess, partie = partie_lichess()
    # 1.e4 d5 2.Cc3, déjà sur le plateau
    plateau.reinitialiser("rnbqkbnr/ppp1pppp/8/3p4/4P3/2N5/PPPP1PPP/R1BQKBNR b KQkq - 1 2")
    partie.appliquer_coups("e2e4 d7d5 b1c3")
    assert partie.synchro

    partie.appliquer_coups("e2e4 d7d5 b1c3 d5e4")  # l'adversaire prend notre pion e4
    assert plateau.etat()["affichage"] == {"d5": "depart", "e4": "prise"}

    # Le joueur retire juste le pion d5 : l'occupation est bonne (d5 vide, e4 occupé)
    # mais notre pion est toujours en e4 -> pas synchro
    plateau.cliquer_case(chess.D5)
    plateau.poser_hors_plateau(0)
    assert not partie.synchro

    # Il retire notre pion e4 et y pose le pion noir : c'est bon
    plateau.cliquer_case(chess.E4)
    plateau.poser_hors_plateau(0)
    plateau.reprendre_hors_plateau(0)
    plateau.cliquer_case(chess.E4)
    assert partie.synchro


def test_fin_de_partie_lichess():
    plateau, lichess, partie = partie_lichess()
    partie.appliquer_coups("", statut="resign", gagnant="black")
    assert partie.terminee
    assert partie.message == "Abandon. Victoire des Noirs."
