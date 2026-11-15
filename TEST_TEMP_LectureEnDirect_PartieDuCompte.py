## Lecture de la partie en cours sur Lichess et affichage des coups joués en temps réel
import berserk
import dotenv

dotenv.load_dotenv()

token = dotenv.get_key(".env", "TOKEN_API_LICHESS")

import berserk

# Insère ton token Lichess ici
LICHESS_TOKEN = token

session = berserk.TokenSession(LICHESS_TOKEN)
client = berserk.Client(session=session)

print("📡 En attente d'une partie... Lancez un match sur Lichess (App ou Web).")

try:
    # 1. Écoute en continu les événements de ton compte
    for event in client.board.stream_incoming_events():
        
        # Dès qu'une partie commence
        if event['type'] == 'gameStart':
            game_id = event['game']['id']
            print(f"\n▶️ Partie détectée ! ID : {game_id}")
            print("----------------------------------------")
            
            # 2. Connexion immédiate au flux de cette partie précise
            for game_event in client.board.stream_game_state(game_id):
                
                # Premier événement reçu : l'état complet initial de la table
                if game_event['type'] == 'gameFull':
                    coups_existants = game_event['state']['moves']
                    if coups_existants:
                        print(f"Historique actuel : {coups_existants}")
                    else:
                        print("La partie commence, aucun coup joué.")
                
                # Événement reçu à chaque fois qu'un joueur joue un coup
                elif game_event['type'] == 'gameState':
                    liste_coups = game_event['moves'].split()
                    
                    if liste_coups:
                        dernier_coup = liste_coups[-1]
                        nb_coups = len(liste_coups)
                        
                        # Détermination simple du joueur (Les blancs jouent les coups impairs)
                        joueur = "Blancs" if nb_coups % 2 != 0 else "Noirs"
                        
                        print(f"Coup n°{nb_coups} [{joueur}] : {dernier_coup}")
                        
                        # C'est ici que tu placeras ton code pour envoyer 'dernier_coup' 
                        # à ton échiquier physique (via Serial/Bluetooth)
                    
                    # Arrêt de l'écoute si la partie se termine
                    if game_event.get('status') in ['mate', 'resign', 'draw', 'outoftime']:
                        print(f"\n🏁 Fin de la partie. Statut : {game_event['status']}")
                        break
                        
            print("----------------------------------------")
            print("📡 Retour en boîte d'attente... Prêt pour la prochaine partie.")

except KeyboardInterrupt:
    print("\nArrêt du programme d'écoute.")