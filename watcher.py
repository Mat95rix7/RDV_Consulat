name: Consulat RDV Watcher

on:
  schedule:
    # Exécute toutes les heures
    - cron: '0 * * * *'
  workflow_dispatch: # Permet l'exécution manuelle

jobs:
  check-rdv:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout du code
        uses: actions/checkout@v4

      - name: Configuration de Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Installation des dépendances
        run: |
          pip install requests beautifulsoup4

      - name: Debug - Vérifier les secrets (TEMPORAIRE)
        run: |
          echo "CURRENT_RDV existe: ${{ secrets.CURRENT_RDV != '' }}"
          echo "SMS_TOKEN existe: ${{ secrets.SMS_TOKEN != '' }}"
          echo "SMS_TO existe: ${{ secrets.SMS_TO != '' }}"

      - name: Vérification des RDV
        env:
          CURRENT_RDV: ${{ secrets.CURRENT_RDV }}
          SMS_TOKEN: ${{ secrets.SMS_TOKEN }}
          SMS_TO: ${{ secrets.SMS_TO }}
        run: |
          echo "Variables d'environnement chargées"
          python watcher.py
