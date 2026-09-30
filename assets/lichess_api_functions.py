"""_summary_
Fichier qui contient les fonctions pour interagir avec l'API Lichess et écouter les événements d'une partie.
"""

import berserk

def connect_to_lichess(token):
    """
    Connecte à l'API Lichess en utilisant le token fourni.

    Args:
        token (str): Token d'authentification pour l'API Lichess.

    Returns:
        berserk.Client: Instance du client Lichess connecté.

    Raises:
        berserk.exceptions.ResponseError: Si le token est invalide (401).
    """

    session = berserk.TokenSession(token)
    client = berserk.Client(session=session)
    try:
        client.account.get()  # Lève une erreur si le token n'est pas valide
    except berserk.exceptions.ResponseError as e:
        raise e
    return client

def get_account_info(client):
    """
    Récupère les informations du compte connecté.

    Args:
        client: Instance du client Lichess.

    Returns:
        dict: Informations du compte.
    """
    username = client.account.get()['username']
    
    dict_info = {
        "username": username}
    return dict_info

def get_all_ongoing_games(client):
    """
    Récupère toutes les parties en cours pour le compte connecté.

    Args:
        client: Instance du client Lichess.

    Returns:
        list: Liste des parties en cours.
    """
    return list(client.games.get_ongoing())

def creer_partie_ia(client, level, color, clock_limit=None, clock_increment=None):
    """
    Crée une partie contre l'IA Lichess avec les paramètres spécifiés.
    
    Args:
        client: Instance du client Lichess.
        level (int): Niveau de l'IA (1-8).
        color (str): Couleur choisie par le joueur ('black', 'white', 'random').
        clock_limit (int, optional): Limite de temps en secondes. None pour illimité.
        clock_increment (int, optional): Incrément en secondes. None pour aucun.

    Returns:
        dict: Détails de la partie créée.
    """
    partie = client.challenges.create_ai(level=level, color=color, clock_limit=clock_limit, clock_increment=clock_increment)
    return partie

def creer_partie_contre_joueur(client, opponent_username, rated, color, clock_limit=None, clock_increment=None):
    """
    Crée une partie contre un autre joueur sur Lichess avec les paramètres spécifiés.
    
    Args:
        client: Instance du client Lichess.
        opponent_username (str): Nom d'utilisateur de l'adversaire.
        rated (bool): True pour une partie classée, False pour une partie amicale.
        color (str): Couleur choisie par le joueur ('black', 'white', 'random').
        clock_limit (int, optional): Limite de temps en secondes. None pour illimité.
        clock_increment (int, optional): Incrément en secondes. None pour aucun.

    Returns:
        dict: Détails du défi créé.
    """
    challenge = client.challenges.create(opponent_username, rated=rated, color=color, clock_limit=clock_limit, clock_increment=clock_increment)
    return challenge

def _info_joueur(joueur):
    """
    Normalise les infos d'un camp (blancs ou noirs) envoyées par Lichess dans un évènement
    'gameFull' : un adversaire IA n'a pas de nom, seulement un niveau ('aiLevel').
    """
    if 'aiLevel' in joueur:
        return {"name": f"Stockfish niveau {joueur['aiLevel']}", "is_ai": True, "rating": None}
    return {"name": joueur.get('name') or joueur.get('id') or '?', "is_ai": False, "rating": joueur.get('rating')}

def stream_partie_events(client, game_id):
    """
    Écoute le flux d'état d'une partie Lichess (client.board.stream_game_state) et le
    transforme en évènements simples, sérialisables en JSON, pour alimenter une page de suivi
    en direct (via Server-Sent Events par exemple) : un premier évènement 'full' avec toutes les
    infos de la partie, puis un évènement 'state' à chaque coup joué ou changement de statut.

    Args:
        client: Instance du client Lichess.
        game_id (str): ID de la partie à suivre.

    Yields:
        dict: Évènement normalisé décrivant l'état courant de la partie.
    """
    for event in client.board.stream_game_state(game_id):
        etype = event.get('type')
        if etype == 'gameFull':
            state = event.get('state', {})
            clock = event.get('clock')
            yield {
                "type": "full",
                "white": _info_joueur(event.get('white', {})),
                "black": _info_joueur(event.get('black', {})),
                "speed": event.get('speed'),
                "clock_initial_ms": clock.get('initial') if clock else None,
                "clock_increment_ms": clock.get('increment') if clock else None,
                "moves": state.get('moves', ''),
                "wtime_ms": state.get('wtime'),
                "btime_ms": state.get('btime'),
                "status": state.get('status'),
                "winner": state.get('winner'),
            }
        elif etype == 'gameState':
            wtime = event.get('wtime')
            btime = event.get('btime')
            yield {
                "type": "state",
                "moves": event.get('moves', ''),
                "wtime_ms": int(wtime.total_seconds() * 1000) if wtime is not None else None,
                "btime_ms": int(btime.total_seconds() * 1000) if btime is not None else None,
                "status": event.get('status'),
                "winner": event.get('winner'),
            }

def _info_joueur_export(joueur):
    """Même rôle que _info_joueur, mais pour le format renvoyé par client.games.export()
    (utilisé en repli quand le flux temps réel n'est plus disponible)."""
    if 'aiLevel' in joueur:
        return {"name": f"Stockfish niveau {joueur['aiLevel']}", "is_ai": True, "rating": None}
    user = joueur.get('user', {})
    return {"name": user.get('name') or user.get('id') or '?', "is_ai": False, "rating": joueur.get('rating')}