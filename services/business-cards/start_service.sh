#!/bin/bash

echo "🚀 Avviando Business Cards Service..."

# Carica variabili ambiente
source /var/www/intelligenceai_docker_ready/.env

# Avvia il servizio
cd /var/www/intelligenceai_docker_ready/services/business-cards
python3 business_cards_service.py
