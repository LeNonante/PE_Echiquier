from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)


import subprocess

@app.route('/wifi_setup')
def wifi_setup():
    result = subprocess.run(["nmcli", "-t", "-f", "SSID", "device", "wifi", "list"],
                             capture_output=True, text=True)
    ssids = sorted(set(s for s in result.stdout.split('\n') if s.strip()))
    return render_template('wifi_setup.html', ssids=ssids)

@app.route('/connect_wifi', methods=['POST'])
def connect_wifi():
    ssid = request.form['ssid']
    password = request.form['password']
    subprocess.run(["nmcli", "connection", "add", "type", "wifi",
                     "ifname", "wlan0", "con-name", ssid, "ssid", ssid])
    subprocess.run(["nmcli", "connection", "modify", ssid,
                     "wifi-sec.key-mgmt", "wpa-psk",
                     "wifi-sec.psk", password,
                     "connection.autoconnect-priority", "10"])
    subprocess.run(["reboot"])
    return "Connexion en cours, le Pi va redémarrer..."


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
    app.run(host='0.0.0.0', port=80, debug=True)