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
    """
    
    session = berserk.TokenSession(token)
    client = berserk.Client(session=session)
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