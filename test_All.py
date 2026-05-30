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

def ecouter_lichess():
    """Écoute les événements du compte pour détecter le démarrage d'une nouvelle partie."""
    global game_id_actuel, couleur_actuelle

    print("Écoute du serveur Lichess activée...")
    for event in client.board.stream_incoming_events():

        if event['type'] == 'gameStart':
            game_id_actuel = event['game']['id']
            couleur_actuelle = "Blancs" if event['game']['color'] == 'white' else "Noirs"
            print(f"\nLa partie a commencé ! ID : {game_id_actuel}")

            for game_event in client.board.stream_game_state(game_id_actuel):
                if game_event['type'] == 'gameFull':
                    print("L'échiquier est en place. Tu joues les {} !".format(couleur_actuelle))

                elif game_event['type'] == 'gameState':
                    moves = game_event['moves'].split()
                    if moves:
                        dernier_coup = moves[-1]
                        if (len(moves) % 2 == 0 and couleur_actuelle == "Blancs") or \
                           (len(moves) % 2 != 0 and couleur_actuelle == "Noirs"):
                            print(f"\nL'adversaire a joué : {dernier_coup}")
                            print("À toi de jouer : (ex: e2e4, abort, resign) ", end="", flush=True)

                    if game_event.get('status') in ['mate', 'resign', 'draw', 'outoftime']:
                        print(f"\nFin de la partie. Statut : {game_event['status']}")
                        game_id_actuel = None
                        break


def ecouter_partie_rejointe(game_id):
    """Écoute directement une partie existante sans passer par stream_incoming_events."""
    global game_id_actuel, couleur_actuelle
    game_id_actuel = game_id
    couleur = None

    for game_event in client.board.stream_game_state(game_id):
        if game_event['type'] == 'gameFull':
            me = client.account.get()['id']
            white_id = game_event['white'].get('id', '')
            couleur = "Blancs" if white_id == me else "Noirs"
            couleur_actuelle = couleur
            coups_existants = game_event['state']['moves']
            if coups_existants:
                print(f"Historique actuel : {coups_existants}")
            print("L'échiquier est en place. Tu joues les {} !".format(couleur))

        elif game_event['type'] == 'gameState':
            if couleur is None:
                continue
            moves = game_event['moves'].split()
            if moves:
                dernier_coup = moves[-1]
                if (len(moves) % 2 == 0 and couleur == "Blancs") or \
                   (len(moves) % 2 != 0 and couleur == "Noirs"):
                    print(f"\nL'adversaire a joué : {dernier_coup}")
                    print("À toi de jouer : (ex: e2e4, abort, resign) ", end="", flush=True)

            if game_event.get('status') in ['mate', 'resign', 'draw', 'outoftime']:
                print(f"\nFin de la partie. Statut : {game_event['status']}")
                game_id_actuel = None
                break


# --- MENU (affiché en premier, avant tout thread) ---

choix = int(input("1. Jouer contre l'IA\n2. Jouer contre un joueur\n3. Rejoindre une partie déjà commencée\n> "))

if choix == 3:
    game_id = input("Entrez l'ID de la partie à rejoindre : ")
    print(f"Connexion à la partie {game_id}...")
    thread_ecoute = threading.Thread(target=ecouter_partie_rejointe, args=(game_id,), daemon=True)
    thread_ecoute.start()
    time.sleep(1)

elif choix == 1:
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

    # Démarrer l'écoute PUIS créer le défi
    thread_ecoute = threading.Thread(target=ecouter_lichess, daemon=True)
    thread_ecoute.start()
    time.sleep(0.5)
    client.challenges.create_ai(level=1, color=color, clock_limit=clock_limit, clock_increment=clock_increment)

elif choix == 2:
    print("Mode joueur contre joueur - à implémenter")
    thread_ecoute = threading.Thread(target=ecouter_lichess, daemon=True)
    thread_ecoute.start()
    time.sleep(1)


# --- BOUCLE PRINCIPALE (lit les coups depuis le clavier / futur échiquier physique) ---

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
