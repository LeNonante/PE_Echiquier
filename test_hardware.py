import sys
import dotenv
import berserk
from gpiozero import Button
from signal import pause


COUPS = ["e2e4", "g1f3", "f1c4"]   # coups programmés, joués dans l'ordre
index = 0

def jouer_coup():
    global index
    if index >= len(COUPS):
        print("Plus de coups programmés.")
        return
    coup = COUPS[index]
    try:
        print(f"Coup joué : {coup}")
        index += 1                         # n'avance que si Lichess a accepté
    except Exception as e:
        print(f"Échec ({coup}) : {e}")     # pas ton tour, coup illégal, etc.

bouton = Button(17, pull_up=True, bounce_time=0.05)  # anti-rebond 50 ms
bouton.when_pressed = jouer_coup

print("Prêt. Appuie sur le bouton.")
pause()