from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/create_ia')
def create_ia():
    return render_template('create_ia.html')

@app.route('/create_online')
def create_online():
    return render_template('create_online.html')

@app.route('/rejoindre')
def rejoindre():
    games = [
        {'id': 4821, 'color': 'white', 'turn': 'you', 'last_move': 'e4'},
        {'id': 4822, 'color': 'black', 'turn': 'waiting', 'last_move': 'Nf3'},
        {'id': 4823, 'color': 'white', 'turn': 'you', 'last_move': 'd4'},
        {'id': 4824, 'color': 'black', 'turn': 'you', 'last_move': 'c5'},
    ]
    return render_template('rejoindre.html', games=games)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)