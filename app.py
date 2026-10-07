from flask import Flask, render_template, request, redirect, url_for, Response
from assets.lichess_api_functions import *
from assets.gestion_env import *
from assets.gestion_client import *
from datetime import datetime
import json

app = Flask(__name__)


import subprocess


@app.route('/wifi_setup')
def wifi_setup():
    return render_template('wifi_setup.html')

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
    context = {"username": "Déconnecté", "is_connected": False}
    client = get_client()
    if client is not None:
        try:
            account_info = get_account_info(client)
            context["username"] = account_info["username"]
            context["is_connected"] = True
        except Exception:
            pass
    return render_template('index.html', **context)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    context = {}
    if request.method == "POST":
        token = request.form.get("token")
        try:
            init_client(token)  # valide le token et crée le client global
        except Exception:
            context["error"] = "Token invalide. Veuillez réessayer."
            context["token"] = getTokenApiLichess() if isThereATokenApiLichess() else ""
            context["is_connected"] = bool(context["token"])
            return render_template('settings.html', **context)

        setTokenApiLichess(token)
        context["success"] = "Token API Lichess enregistré avec succès."
    context["token"] = getTokenApiLichess() if isThereATokenApiLichess() else ""
    context["is_connected"] = bool(context["token"])
    return render_template('settings.html', **context)

@app.route('/logout', methods=['POST'])
def logout():
    setTokenApiLichess("")
    reset_client()
    return redirect(url_for('index'))

@app.route('/create_ia', methods=['GET', 'POST'])
def create_ia():
    if get_client() is None:
        return redirect(url_for('settings'))
    elif request.method == 'POST':
        level = int(request.form.get('level'))
        color = request.form.get('color')
        clock_limit = request.form.get('clock_limit')
        clock_increment = request.form.get('clock_increment')
        no_clock_limit = request.form.get('no_clock_limit')
        no_clock_increment = request.form.get('no_clock_increment')
        if no_clock_limit is not None:
            # Lichess exige limite et incrément ensemble : pas de limite => pas d'horloge
            clock_limit = None
            clock_increment = None
        else:
            clock_limit = int(clock_limit)
            clock_increment = 0 if no_clock_increment is not None else int(clock_increment)
            if clock_limit not in (15, 30, 45) and (clock_limit <= 0 or clock_limit % 60 != 0):
                return render_template('create_ia.html', error="Limite de temps invalide : Veuillez choisir 15, 30, 45s ou un multiple de 60s.")

        partie = creer_partie_ia(get_client(), level, color, clock_limit, clock_increment)
        game_id = partie['id']
        return redirect(url_for('suivi_partie', game_id=game_id))
    else :
        return render_template('create_ia.html')

@app.route('/create_online', methods=['GET', 'POST'])
def create_online():
    if get_client() is None:
        return redirect(url_for('settings'))
    elif request.method == 'POST':
        adversaire = request.form.get('adversaire', '').strip()
        color = request.form.get('color')
        clock_limit = request.form.get('clock_limit')
        clock_increment = request.form.get('clock_increment')
        no_clock_limit = request.form.get('no_clock_limit')
        no_clock_increment = request.form.get('no_clock_increment')
        if not adversaire:
            return render_template('create_online.html', error="Veuillez indiquer le pseudo Lichess de l'adversaire.")
        if no_clock_limit is not None:
            # Lichess exige limite et incrément ensemble : pas de limite => pas d'horloge
            clock_limit = None
            clock_increment = None
        else:
            clock_limit = int(clock_limit)
            clock_increment = 0 if no_clock_increment is not None else int(clock_increment)
            if clock_limit not in (15, 30, 45) and (clock_limit <= 0 or clock_limit % 60 != 0):
                return render_template('create_online.html', error="Limite de temps invalide : Veuillez choisir 15, 30, 45s ou un multiple de 60s.")
        try:
            challenge = creer_partie_contre_joueur(get_client(), adversaire, rated=False, color=color, clock_limit=clock_limit, clock_increment=clock_increment)
        except Exception:
            return render_template('create_online.html', error=f"Impossible de défier « {adversaire} ». Vérifiez que ce pseudo existe et qu'il accepte les défis.")
        print(challenge['id'])
        return render_template('create_online.html')
    else :
        return render_template('create_online.html')

@app.route('/rejoindre', methods=['GET', 'POST'])
def rejoindre():
    if get_client() is None:
        return redirect(url_for('settings'))
    else:
        games = get_all_ongoing_games(get_client())
        return render_template('rejoindre.html', games=games)

@app.route('/demonstrations')
def demonstrations():
    with open("assets/fichiers_pgn/infos.json", "r", encoding="utf-8") as f:
        demos = json.load(f)
    return render_template('demonstrations.html', demos=demos)

@app.route('/partie/<game_id>')
def suivi_partie(game_id):
    if get_client() is None:
        return redirect(url_for('settings'))
    return render_template('game_live.html', game_id=game_id)

@app.route('/partie/<game_id>/stream')
def suivi_partie_stream(game_id):
    client = get_client()
    if client is None:
        return redirect(url_for('settings'))

    def event_stream():
        try:
            for event in stream_partie_events(client, game_id):
                yield f"data: {json.dumps(event)}\n\n"
            return
        except Exception as e:
            print(f"[suivi_partie] flux temps réel interrompu pour la partie {game_id} : {e}")

    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )

init_client_from_env()  # connexion au lancement si un token est déjà enregistré

if __name__ == '__main__':
    # threaded=True : indispensable pour que le flux SSE de suivi de partie (connexion
    # longue durée) ne bloque pas les autres requêtes sur le serveur de développement.
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)