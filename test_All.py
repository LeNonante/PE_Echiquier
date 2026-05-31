import berserk
import threading
import time
import dotenv
dotenv.load_dotenv()

LICHESS_TOKEN = dotenv.get_key(".env", "TOKEN_API_LICHESS")

session = berserk.TokenSession(LICHESS_TOKEN)
client = berserk.Client(session=session)

game_id_actuel = None
couleur_actuelle = None


# --- FONCTIONS D'ÉCOUTE ---

def attendre_game_start() -> tuple[str, str]:
    """Écoute les événements du compte jusqu'au démarrage d'une partie, puis retourne (game_id, couleur)."""
    print("En attente du démarrage de la partie...")
    for event in client.board.stream_incoming_events():
        if event['type'] == 'gameStart':
            game_id = event['game']['id']
            couleur = "Blancs" if event['game']['color'] == 'white' else "Noirs"
            print(f"\nPartie démarrée ! ID : {game_id}")
            return game_id, couleur


def ecouter_partie(game_id: str, couleur: str | None = None):
    """Écoute l'état d'une partie. Si couleur est None, la détermine depuis gameFull."""
    global game_id_actuel, couleur_actuelle
    game_id_actuel = game_id

    for event in client.board.stream_game_state(game_id):
        if event['type'] == 'gameFull':
            if couleur is None:
                me = client.account.get()['id']
                couleur = "Blancs" if event['white'].get('id', '') == me else "Noirs"
            couleur_actuelle = couleur

            coups_existants = event['state']['moves']
            if coups_existants:
                print(f"Historique actuel : {coups_existants}")
            print(f"L'échiquier est en place. Tu joues les {couleur} !")

        elif event['type'] == 'gameState':
            if couleur_actuelle is None:
                continue
            moves = event['moves'].split()
            if moves:
                dernier_coup = moves[-1]
                if (len(moves) % 2 == 0 and couleur_actuelle == "Blancs") or \
                   (len(moves) % 2 != 0 and couleur_actuelle == "Noirs"):
                    print(f"\nL'adversaire a joué : {dernier_coup}")
                    print("À toi de jouer : (ex: e2e4, abort, resign) ", end="", flush=True)

            if event.get('status') in ['mate', 'resign', 'draw', 'outoftime']:
                print(f"\nFin de la partie. Statut : {event['status']}")
                game_id_actuel = None
                break


def lancer_ecoute(game_id: str, couleur: str | None = None):
    """Lance ecouter_partie dans un thread daemon."""
    thread = threading.Thread(target=ecouter_partie, args=(game_id, couleur), daemon=True)
    thread.start()
    time.sleep(0.5)


# --- MENU ---

choix = int(input("1. Jouer contre l'IA\n2. Défier un joueur Lichess\n3. Rejoindre une partie déjà commencée\n> "))

if choix == 1:
    print("Lancement du défi contre l'IA Lichess...")
    color = str(input("Choisis ta couleur (black/white/random) : "))
    while color not in ["black", "white", "random"]:
        print("Choix invalide. Essaie encore.")
        color = str(input("Choisis ta couleur (black/white/random) : "))

    clock_limit = int(input("Limite de temps en secondes (ex: 600 pour 10 min, 0 pour illimité) : "))
    if clock_limit == 0:
        clock_limit = None

    clock_increment = int(input("Incrément en secondes (0 pour aucun) : "))
    if clock_increment == 0:
        clock_increment = None

    client.challenges.create_ai(level=1, color=color, clock_limit=clock_limit, clock_increment=clock_increment)
    game_id, couleur = attendre_game_start()
    lancer_ecoute(game_id, couleur)

elif choix == 2:
    name = input("Entrez le nom d'utilisateur de votre adversaire : ")
    print(f"Envoi du défi à {name}...")
    try:
        rated=str(input("Partie classée ? (y/n) : ")).lower() == "y"
        
        color = str(input("Choisis ta couleur (black/white/random) : "))
        while color not in ["black", "white", "random"]:
            print("Choix invalide. Essaie encore.")
            color = str(input("Choisis ta couleur (black/white/random) : "))

        clock_limit = int(input("Limite de temps en secondes (ex: 600 pour 10 min, 0 pour illimité) : "))
        if clock_limit == 0:
            clock_limit = None

        clock_increment = int(input("Incrément en secondes (0 pour aucun) : "))
        if clock_increment == 0:
            clock_increment = None
            
        client.challenges.create(name, rated=rated, color=color, clock_limit=clock_limit, clock_increment=clock_increment)
        
    except Exception as e:
        print(f"Erreur lors de l'envoi du défi : {e}")
        exit(1)
    print("Défi envoyé. En attente de l'acceptation...")
    game_id, couleur = attendre_game_start()
    lancer_ecoute(game_id, couleur)

elif choix == 3:
    game_id = input("Entrez l'ID de la partie à rejoindre : ")
    print(f"Connexion à la partie {game_id}...")
    lancer_ecoute(game_id)  # couleur déterminée depuis gameFull


# --- BOUCLE PRINCIPALE ---

while True:
    try:
        if game_id_actuel:
            mon_coup = input()

            if mon_coup.lower() == "resign":
                client.board.resign_game(game_id_actuel)
                print("Tu as abandonné la partie.")
                game_id_actuel = None
                continue
            elif mon_coup.lower() == "abort":
                client.board.abort_game(game_id_actuel)
                print("Tu as annulé la partie.")
                game_id_actuel = None
                continue

            try:
                client.board.make_move(game_id_actuel, mon_coup)
            except Exception:
                print("Coup invalide ou erreur réseau. Essaie encore.")
        else:
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nArrêt du programme. Si une partie était en cours, tu la perdras au temps sur Lichess.")
        break
