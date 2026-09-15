from flask import Flask, render_template
from flaskwebgui import FlaskUI
from flask_socketio import SocketIO, emit
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

if __name__ == '__main__':
    #FlaskUI(app=app, server="flask", width=1200, height=800).run()
    app.run(debug=True)