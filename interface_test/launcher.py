"""
Lanceur PyWebView + Flask

Cette approche démarre Flask dans un thread en arrière-plan,
puis ouvre PyWebView qui pointe vers le serveur local.
"""

import threading
import time
import webview
from app import app

# Configuration
HOST = '127.0.0.1'
PORT = 5000


def run_flask():
    """Lance Flask en mode silencieux (pas de logs dans la console)."""
    # Désactiver les logs pour ne pas polluer la fenêtre desktop
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


def main():
    # Démarrer Flask dans un thread daemon (s'arrête avec l'app)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Attendre que Flask soit prêt
    time.sleep(1)
    
    # Créer la fenêtre PyWebView
    window = webview.create_window(
        title='Chessmate',
        url=f'http://{HOST}:{PORT}',
        width=1200,
        height=800,
        min_size=(900, 600),
        resizable=True,
        # Décommenter pour cacher la barre du menu navigateur :
        # frameless=False,
    )
    
    # Lancer l'interface
    webview.start(debug=False, gui='edgechromium')



if __name__ == '__main__':
    main()