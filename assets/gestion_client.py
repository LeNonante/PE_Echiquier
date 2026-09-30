from assets.lichess_api_functions import connect_to_lichess
from assets.gestion_env import getTokenApiLichess, isThereATokenApiLichess

_client = None

def get_client():
    return _client

def init_client(token):
    """Crée le client global. Lève une exception si le token est invalide."""
    global _client
    _client = connect_to_lichess(token)

def init_client_from_env():
    """Au lancement : tente de se connecter avec le token enregistré, sans planter."""
    global _client
    _client = None
    if isThereATokenApiLichess():
        try:
            _client = connect_to_lichess(getTokenApiLichess())
        except Exception:
            _client = None
    return _client

def reset_client():
    global _client
    _client = None
