#!/usr/bin/env python3
import requests
import json

# Test des champs structurés dans la réponse
response = requests.post('http://localhost:8000/recommend', json={
    'plant_name': 'Aloe vera', 
    'symptoms': 'brûlures', 
    'user_profile': 'adulte'
})

data = response.json()
print('Champs retournés:', list(data.keys()))

print('\nChamps structurés:')
structured_fields = [
    'diagnostic', 'symptomes', 'presentation', 'mode_action', 
    'traitement_info', 'precautions_info', 'composants_info', 'resume_traitement'
]

for field in structured_fields:
    value = data.get(field, "")
    status = "PRÉSENT" if value else "ABSENT"
    length = len(str(value)) if value else 0
    print(f'{field}: {status} ({length} chars)')
    if value and length < 200:  # Afficher le contenu si court
        print(f'  Contenu: "{value[:100]}..."')

print('\nExplication complète (début):')
explanation = data.get('explanation', '')
print(f'Longueur: {len(explanation)} chars')
print(f'Début: "{explanation[:300]}..."')
