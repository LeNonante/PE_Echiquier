from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clé_secrète_test'
socketio = SocketIO(app, cors_allowed_origins="*")

# Stocke tous les messages pour affichage
messages_log = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    msg = f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Client connecté"
    print(msg)
    messages_log.append(msg)
    emit('log', {'text': msg})

@socketio.on('disconnect')
def handle_disconnect():
    msg = f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Client déconnecté"
    print(msg)
    messages_log.append(msg)
    emit('log', {'text': msg})

@socketio.on('message')
def handle_message(data):
    msg = f"[{datetime.now().strftime('%H:%M:%S')}] 📨 Reçu: {data}"
    print(msg)
    messages_log.append(msg)
    # Broadcast à tous les clients connectés
    emit('log', {'text': msg}, broadcast=True)

@socketio.on('move')
def handle_move(data):
    move = data.get('move', 'unknown')
    msg = f"[{datetime.now().strftime('%H:%M:%S')}] 📍 Coup reçu: {move}"
    print(msg)
    messages_log.append(msg)
    # Envoie une réponse au client
    emit('response', {'status': 'ok', 'received': move})
    # Et broadcast à tous
    emit('log', {'text': msg}, broadcast=True)

# Route pour voir l'historique en texte brut
@app.route('/logs')
def get_logs():
    return '<br>'.join(messages_log)

if __name__ == '__main__':
    print("🚀 Serveur démarré sur http://0.0.0.0:5000")
    print("Ouvre http://localhost:5000 dans ton navigateur")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)