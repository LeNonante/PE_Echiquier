import os
from dotenv import load_dotenv, set_key, dotenv_values


#------------------------- TOKEN API LICHESS -------------------------
def isThereATokenApiLichess() :
    vals = dotenv_values()
    return bool(vals.get("TOKEN_API_LICHESS", ""))

def setTokenApiLichess(token) :
    #Enregistrement du token API Lichess
    load_dotenv() #Ouverture du .env
    set_key(".env", "TOKEN_API_LICHESS", token) #on enregistre

def getTokenApiLichess() :
    vals = dotenv_values()
    return vals.get("TOKEN_API_LICHESS", "")


#------------------------- TYPE DE PLATEAU -------------------------
def getTypePlateau() :
    #"simule" (par défaut) ou "physique"
    vals = dotenv_values()
    return vals.get("PLATEAU", "simule")