import berserk
import threading
import time
import dotenv
dotenv.load_dotenv()

token = dotenv.get_key(".env", "TOKEN_API_LICHESS")

# Insère ton token Lichess ici
LICHESS_TOKEN = token

session = berserk.TokenSession(LICHESS_TOKEN)
client = berserk.Client(session=session)

# Variable globale pour partager l'ID de la partie entre les deux processus
game_id_actuel = None

# --- 1. FONCTION QUI ÉCOUTE LICHESS (Tournera en arrière-plan) ---
def ecouter_lichess():
    global game_id_actuel
    
    print("📡 Écoute du serveur Lichess activée...")
    for event in client.board.stream_incoming_events():
        
        if event['type'] == 'gameStart':
            game_id_actuel = event['game']['id']
            print(f"\n▶️ La partie a commencé ! ID : {game_id_actuel}")
            
            # On se connecte au flux de cette partie
            for game_event in client.board.stream_game_state(game_id_actuel):
                if game_event['type'] == 'gameFull':
                    print("L'échiquier est en place. Tu as les Blancs !")
                    print("👉 À toi de jouer (Tape ton coup, ex: e2e4) :")
                    
                elif game_event['type'] == 'gameState':
                    moves = game_event['moves'].split()
                    if moves:
                        dernier_coup = moves[-1]
                        # Si le nombre de coups est impair, c'est l'IA (les Noirs) qui vient de jouer
                        if len(moves) % 2 != 0:
                            print(f"\n🤖 L'adversaire a joué : {dernier_coup}")
                            print("👉 À toi de jouer : ", end="", flush=True)

# --- 2. LANCEMENT DU PROGRAMME ---

# On lance l'écoute dans un thread (en tâche de fond)
thread_ecoute = threading.Thread(target=ecouter_lichess, daemon=True)
thread_ecoute.start()

# On laisse une petite seconde au thread pour bien démarrer
time.sleep(1)

# On lance un défi à l'IA (Niveau 1, toi tu as les blancs, 10 minutes au chrono)
print("⚔️ Lancement du défi contre l'IA Lichess...")
client.challenges.create_ai(level=1, color="white", clock_limit=600, clock_increment=0)

# --- 3. BOUCLE PRINCIPALE (Ton "Échiquier Physique") ---
# Cette boucle tourne en continu et attend tes actions
while True:
    try:
        # Si une partie est en cours
        if game_id_actuel:
            # Ici, `input()` remplace la lecture des capteurs de ton échiquier
            mon_coup = input() 
            
            # On envoie le coup à Lichess
            try:
                client.board.make_move(game_id_actuel, mon_coup)
            except Exception as e:
                # Si le coup est invalide (ex: e2e5), Lichess renverra une erreur HTTP 400
                print(f"❌ Coup invalide ou erreur réseau. Essaie encore.")
        else:
            time.sleep(0.5) # On patiente tant que la partie n'a pas commencé
            
    except KeyboardInterrupt:
        print("\nArrêt du programme. Si une partie était en cours, tu la perdras au temps sur Lichess.")
        break