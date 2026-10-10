"""_summary_
Fonctions qui font le lien entre ce que voient les capteurs du plateau (des cases occupées
ou vides, sans savoir quelle pièce s'y trouve) et les règles des échecs (python-chess).

Toutes les cases sont manipulées sous forme d'entiers python-chess (chess.E4 == 28, etc.).
"""

import chess


class CoupIllisible(Exception):
    """
    Levée quand l'état du plateau physique ne correspond à aucun coup légal (ou à plusieurs).

    Attributes:
        cases (set[int]): Cases à signaler au joueur (LED d'erreur par exemple).
    """

    def __init__(self, message, cases=()):
        super().__init__(message)
        self.cases = set(cases)


def occupation_de(board):
    """
    Calcule ce que les capteurs devraient voir pour une position donnée.

    Args:
        board (chess.Board): Position de référence.

    Returns:
        frozenset[int]: Cases occupées par une pièce (peu importe sa couleur).
    """
    return frozenset(board.piece_map())


def cases_en_ecart(board, occupation):
    """
    Compare le plateau physique à la position attendue.

    Args:
        board (chess.Board): Position attendue.
        occupation (Iterable[int]): Cases occupées sur le plateau physique.

    Returns:
        set[int]: Cases occupées alors qu'elles devraient être vides, et inversement.
    """
    return set(occupation_de(board) ^ frozenset(occupation))


def deduire_coup(board, occupation, cases_levees=(), promotion=chess.QUEEN):
    """
    Retrouve le coup joué à partir de la nouvelle occupation du plateau.

    Le principe : on essaie chaque coup légal de la position de départ et on garde ceux qui
    produisent exactement l'occupation lue par les capteurs.

    L'occupation ne suffit pas pour les prises : un cavalier en e4 qui prend en d6 ou en f6
    laisse le même plateau (e4 vide, d6 et f6 toujours occupées). On utilise donc aussi les
    cases levées pendant le coup : pour une prise, la case de la pièce prise doit avoir été
    vidée à un moment (le joueur a retiré la pièce adverse).

    Args:
        board (chess.Board): Position avant le coup.
        occupation (Iterable[int]): Cases occupées après le coup.
        cases_levees (Iterable[int]): Cases qui ont été vides au moins une fois pendant le coup.
        promotion (int): Pièce choisie en cas de promotion (les capteurs ne la voient pas).

    Returns:
        chess.Move: Le coup joué.

    Raises:
        CoupIllisible: Aucun coup, coup illégal ou coup ambigu.
    """
    occupation = frozenset(occupation)
    cases_levees = set(cases_levees)
    ecart = cases_en_ecart(board, occupation)
    if not ecart:
        raise CoupIllisible("Aucun coup détecté : le plateau n'a pas changé.")

    candidats = []
    for coup in board.legal_moves:
        if coup.promotion is not None and coup.promotion != promotion:
            continue  # les 4 promotions donnent la même occupation : on n'en garde qu'une
        apres = board.copy(stack=False)
        apres.push(coup)
        if occupation_de(apres) != occupation:
            continue
        prise_classique = board.is_capture(coup) and not board.is_en_passant(coup)
        if prise_classique and coup.to_square not in cases_levees:
            continue  # la pièce adverse n'a jamais été retirée de sa case
        candidats.append(coup)

    if len(candidats) == 1:
        return candidats[0]
    if not candidats:
        raise CoupIllisible("Coup illégal ou pièces mal placées.", ecart)
    raise CoupIllisible("Coup ambigu : plusieurs prises possibles.", ecart | {c.to_square for c in candidats})


def cases_a_manipuler(board, coup):
    """
    Indique au joueur comment reproduire sur le plateau un coup joué par l'adversaire.

    Args:
        board (chess.Board): Position avant le coup.
        coup (chess.Move): Coup à reproduire.

    Returns:
        dict[int, str]: Case -> rôle ("depart", "arrivee" ou "prise").
    """
    cases = {coup.from_square: "depart", coup.to_square: "arrivee"}
    if board.is_en_passant(coup):
        pion_pris = chess.square(chess.square_file(coup.to_square), chess.square_rank(coup.from_square))
        cases[pion_pris] = "prise"
    elif board.is_capture(coup):
        cases[coup.to_square] = "prise"  # retirer la pièce prise, puis poser la sienne
    elif board.is_castling(coup):
        rang = chess.square_rank(coup.from_square)
        if board.is_kingside_castling(coup):
            cases[chess.square(7, rang)] = "depart"
            cases[chess.square(5, rang)] = "arrivee"
        else:
            cases[chess.square(0, rang)] = "depart"
            cases[chess.square(3, rang)] = "arrivee"
    return cases
