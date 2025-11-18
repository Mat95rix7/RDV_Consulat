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
            print(f"⚠️ Erreur envoi SMS: {response.status} - {response.read().decode()}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi du SMS: {e}")

def check_rdv():
    """Vérifie les rendez-vous disponibles"""
    CURRENT_RDV = datetime.strptime(CURRENT_RDV_STR, "%Y-%m-%d")
    
    try:
        print(f"🔍 Vérification des RDV sur {WATCH_URL}")
        response = requests.get(WATCH_URL, timeout=10)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        
        # Trouver toutes les cellules de dates cliquables
        # Structure: <td data-month="X" data-year="Y"><a data-date="Z">
        date_cells = soup.select("td[data-handler='selectDay'][data-month][data-year]")
        
        print(f"   {len(date_cells)} dates cliquables trouvées")
        
        better_dates = []
        all_dates = []
        
        for cell in date_cells:
            # Récupérer les données depuis le <td>
            month = int(cell.get("data-month", -1)) + 1  # Le mois est en base 0
            year = int(cell.get("data-year", -1))
            
            # Récupérer le jour depuis le <a> enfant
            link = cell.find("a", {"data-date": True})
            if not link:
                continue
            
            day = int(link.get("data-date", -1))
            
            # Vérifier que toutes les données sont valides
            if day == -1 or month == -1 or year == -1:
                continue
            
            try:
                date = datetime(year, month, day)
                all_dates.append(date)
                
                # Comparer avec le RDV actuel
                if date < CURRENT_RDV:
                    better_dates.append(date)
                    print(f"   ✨ Date disponible: {date.strftime('%d/%m/%Y')}")
            except ValueError as e:
                print(f"   ⚠️ Date invalide ignorée: {day}/{month}/{year} - {e}")
                continue
        
        # Afficher toutes les dates trouvées pour debug
        if all_dates:
            all_dates.sort()
            print(f"\n📅 Toutes les dates disponibles:")
            for d in all_dates[:10]:  # Limiter à 10 pour la lisibilité
                prefix = "→" if d < CURRENT_RDV else " "
                print(f"   {prefix} {d.strftime('%d/%m/%Y')}")
            if len(all_dates) > 10:
                print(f"   ... et {len(all_dates) - 10} autres dates")
        
        # Envoyer SMS si de meilleures dates sont trouvées
        if better_dates:
            better_dates.sort()
            best = better_dates[0]
            msg = f"🎉 RDV disponible le {best.strftime('%d/%m/%Y')} (votre RDV actuel: {CURRENT_RDV.strftime('%d/%m/%Y')})"
            print(f"\n{msg}")
            send_sms(f"RDV Consulat: {best.strftime('%d/%m/%Y')} disponible!")
        else:
            print(f"\nℹ️  Aucun RDV disponible avant votre date actuelle ({CURRENT_RDV.strftime('%d/%m/%Y')})")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Démarrage du watcher de RDV Consulat d'Algérie à Créteil")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    validate_config()
    check_rdv()
    
    print("=" * 60)
    print("✅ Exécution terminée")
    print("=" * 60)
