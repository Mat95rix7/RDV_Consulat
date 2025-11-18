import requests
from bs4 import BeautifulSoup
from datetime import datetime
import http.client
import os
import sys

# Configuration depuis les variables d'environnement
WATCH_URL = "https://consulat-creteil-algerie.fr/5589/rendez-vous-passeport-biometrique/"
CURRENT_RDV_STR = os.getenv("CURRENT_RDV")
SMS_TOKEN = os.getenv("SMS_TOKEN")
SMS_TO = os.getenv("SMS_TO")

def validate_config():
    """Vérifie que toutes les variables d'environnement sont présentes"""
    if not CURRENT_RDV_STR:
        print("❌ Variable CURRENT_RDV manquante")
        sys.exit(1)
    if not SMS_TOKEN:
        print("❌ Variable SMS_TOKEN manquante")
        sys.exit(1)
    if not SMS_TO:
        print("❌ Variable SMS_TO manquante")
        sys.exit(1)
    
    try:
        datetime.strptime(CURRENT_RDV_STR, "%Y-%m-%d")
    except ValueError:
        print(f"❌ Format de date invalide pour CURRENT_RDV: {CURRENT_RDV_STR}")
        print("   Format attendu: YYYY-MM-DD (exemple: 2025-12-31)")
        sys.exit(1)
    
    print("✅ Configuration validée")

def send_sms(message):
    """Envoie un SMS via l'API SMSAPI"""
    try:
        conn = http.client.HTTPSConnection("api.smsapi.com")
        payload = f"access_token={SMS_TOKEN}&to={SMS_TO}&message={message}"
        headers = {'Content-type': "application/x-www-form-urlencoded"}
        conn.request("POST", "/sms.do", payload, headers)
        response = conn.getresponse()
        
        if response.status == 200:
            print(f"✅ SMS envoyé: {message}")
        else:
            print(f"⚠️ Erreur envoi SMS: {response.status}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi du SMS: {e}")

def check_rdv():
    """Vérifie les rendez-vous disponibles"""
    CURRENT_RDV = datetime.strptime(CURRENT_RDV_STR, "%Y-%m-%d")
    
    try:
        print(f"🔍 Vérification des RDV sur {WATCH_URL}")
        html = requests.get(WATCH_URL, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        
        # Tous les jours cliquables
        days = soup.select("a.ui-state-default")
        print(f"   {len(days)} dates disponibles trouvées")
        
        better_dates = []
        for a in days:
            day = int(a["data-date"])
            month = int(a.parent["data-month"]) + 1
            year = int(a.parent["data-year"])
            date = datetime(year, month, day)
            
            if date < CURRENT_RDV:
                better_dates.append(date)
        
        if better_dates:
            better_dates.sort()
            best = better_dates[0]
            msg = f"RDV disponible le {best.strftime('%d/%m/%Y')} (avant le {CURRENT_RDV.strftime('%d/%m/%Y')})"
            print(f"🎉 {msg}")
            send_sms(msg)
        else:
            print(f"ℹ️  Aucun RDV avant le {CURRENT_RDV.strftime('%d/%m/%Y')}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Démarrage du watcher de RDV Consulat")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    validate_config()
    check_rdv()
    
    print("=" * 50)
    print("✅ Exécution terminée")
    print("=" * 50)
