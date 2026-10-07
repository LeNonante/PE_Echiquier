import chess.pgn


def lire_coups_pgn(chemin_fichier):
	"""Lit un fichier PGN et produit les coups un par un en notation SAN.

	Utiliser `yield` crée un générateur : les coups sont calculés à la demande,
	ce qui évite de stocker toute la partie en mémoire et permet de commencer
	leur traitement avant d'avoir lu tous les coups.
	"""
	with open(chemin_fichier, "r", encoding="utf-8") as fichier:
		while partie := chess.pgn.read_game(fichier):
			plateau = partie.board()
			for coup in partie.mainline_moves():
				yield plateau.san(coup)
				plateau.push(coup)
