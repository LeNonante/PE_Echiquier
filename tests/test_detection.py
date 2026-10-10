import chess
import pytest

from assets.plateau.detection import (
    CoupIllisible, occupation_de, deduire_coup, cases_a_manipuler,
)


def occupation_apres(board, *deplacements):
    """Occupation physique après des déplacements (depart, arrivee) ; arrivee=None : pièce retirée."""
    occupation = set(occupation_de(board))
    for depart, arrivee in deplacements:
        occupation.discard(depart)
        if arrivee is not None:
            occupation.add(arrivee)
    return occupation


def test_coup_simple():
    board = chess.Board()
    occupation = occupation_apres(board, (chess.E2, chess.E4))
    assert deduire_coup(board, occupation) == chess.Move.from_uci("e2e4")


def test_aucun_changement():
    board = chess.Board()
    with pytest.raises(CoupIllisible, match="Aucun coup"):
        deduire_coup(board, occupation_de(board))


def test_coup_illegal():
    board = chess.Board()
    occupation = occupation_apres(board, (chess.E2, chess.E5))  # pion qui avance de 3 cases
    with pytest.raises(CoupIllisible, match="illégal") as erreur:
        deduire_coup(board, occupation)
    assert erreur.value.cases == {chess.E2, chess.E5}


def test_prise_exige_que_la_piece_prise_ait_ete_levee():
    board = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
    occupation = occupation_apres(board, (chess.E4, chess.D5))  # exd5
    with pytest.raises(CoupIllisible):
        deduire_coup(board, occupation, cases_levees={chess.E4})
    coup = deduire_coup(board, occupation, cases_levees={chess.E4, chess.D5})
    assert coup == chess.Move.from_uci("e4d5")


def test_prise_ambigue_quand_deux_cibles_levees():
    # Cavalier en e4 pouvant prendre en d6 ou f6 : même occupation finale
    board = chess.Board("4k3/8/3p1p2/8/4N3/8/8/4K3 w - - 0 1")
    occupation = occupation_apres(board, (chess.E4, chess.D6))
    assert deduire_coup(board, occupation, {chess.E4, chess.D6}) == chess.Move.from_uci("e4d6")
    assert deduire_coup(board, occupation, {chess.E4, chess.F6}) == chess.Move.from_uci("e4f6")
    with pytest.raises(CoupIllisible, match="ambigu"):
        deduire_coup(board, occupation, {chess.E4, chess.D6, chess.F6})


def test_petit_roque():
    board = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    occupation = occupation_apres(board, (chess.E1, chess.G1), (chess.H1, chess.F1))
    assert deduire_coup(board, occupation) == chess.Move.from_uci("e1g1")


def test_grand_roque_noir():
    board = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
    occupation = occupation_apres(board, (chess.E8, chess.C8), (chess.A8, chess.D8))
    assert deduire_coup(board, occupation) == chess.Move.from_uci("e8c8")


def test_tour_seule_pendant_un_roque_nest_pas_un_roque():
    board = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    occupation = occupation_apres(board, (chess.H1, chess.F1))
    assert deduire_coup(board, occupation) == chess.Move.from_uci("h1f1")


def test_prise_en_passant():
    board = chess.Board("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 2")
    occupation = occupation_apres(board, (chess.E5, chess.D6), (chess.D5, None))
    assert deduire_coup(board, occupation) == chess.Move.from_uci("e5d6")


def test_promotion_en_dame_par_defaut():
    board = chess.Board("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
    occupation = occupation_apres(board, (chess.A7, chess.A8))
    assert deduire_coup(board, occupation) == chess.Move.from_uci("a7a8q")
    assert deduire_coup(board, occupation, promotion=chess.KNIGHT) == chess.Move.from_uci("a7a8n")


def test_cases_a_manipuler_roque():
    board = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    cases = cases_a_manipuler(board, chess.Move.from_uci("e1g1"))
    assert cases == {chess.E1: "depart", chess.G1: "arrivee", chess.H1: "depart", chess.F1: "arrivee"}


def test_cases_a_manipuler_prise():
    board = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
    cases = cases_a_manipuler(board, chess.Move.from_uci("e4d5"))
    assert cases == {chess.E4: "depart", chess.D5: "prise"}
