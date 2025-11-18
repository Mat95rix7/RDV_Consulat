import os
import sys
import http.client
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
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
        print(f"❌ Format de date invalide: {CURRENT_RDV_STR}")
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
            print(f"⚠️ Erreur SMS: {response.status}")
    except Exception as e:
        print(f"❌ Erreur SMS: {e}")

def check_rdv():
    """Vérifie les RDV avec Selenium"""
    CURRENT_RDV = datetime.strptime(CURRENT_RDV_STR, "%Y-%m-%d")
    
    # Configuration Chrome headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        print(f"🔍 Ouverture du navigateur...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(WATCH_URL)
        
        print(f"⏳ Attente du chargement du calendrier...")
        # Attendre que le calendrier soit chargé (max 20 secondes)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td[data-handler='selectDay']"))
        )
        
        print(f"✅ Calendrier chargé")
        
        # Récupérer toutes les dates cliquables
        date_cells = driver.find_elements(By.CSS_SELECTOR, "td[data-handler='selectDay'][data-month][data-year]")
        
        print(f"   {len(date_cells)} dates trouvées")
        
        better_dates = []
        all_dates = []
        
        for cell in date_cells:
            try:
                month = int(cell.get_attribute("data-month")) + 1
                year = int(cell.get_attribute("data-year"))
                
                link = cell.find_element(By.CSS_SELECTOR, "a[data-date]")
                day = int(link.get_attribute("data-date"))
                
                date = datetime(year, month, day)
                all_dates.append(date)
                
                if date < CURRENT_RDV:
                    better_dates.append(date)
                    print(f"   ✨ {date.strftime('%d/%m/%Y')}")
            except Exception as e:
                continue
        
        # Afficher les dates disponibles
        if all_dates:
            all_dates.sort()
            print(f"\n📅 Dates disponibles (10 premières):")
            for d in all_dates[:10]:
                prefix = "→" if d < CURRENT_RDV else " "
                print(f"   {prefix} {d.strftime('%d/%m/%Y')}")
        
        # Envoyer SMS si meilleure date
        if better_dates:
            better_dates.sort()
            best = better_dates[0]
            msg = f"RDV Consulat: {best.strftime('%d/%m/%Y')} disponible!"
            print(f"\n🎉 {msg}")
            send_sms(msg)
        else:
            print(f"\nℹ️  Aucun RDV avant le {CURRENT_RDV.strftime('%d/%m/%Y')}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Watcher RDV Consulat (Selenium)")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    validate_config()
    check_rdv()
    
    print("=" * 60)
    print("✅ Terminé")
    print("=" * 60)
