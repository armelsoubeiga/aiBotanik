"""
Ce patch ajoute une gestion améliorée des recommandations pour garantir la cohérence des données
entre les consultations en direct et celles chargées depuis l'historique.

Pour appliquer ce patch:
1. Copiez le contenu de ce fichier
2. Ouvrez routes.py
3. Localisez la section de création du message dans la fonction add_message (vers la ligne 305)
4. Remplacez cette section par le code de ce patch
"""

# Amélioration de la gestion des recommandations dans la fonction add_message
# Remplacer le bloc existant dans routes.py par:

    # Créer le message avec gestion avancée de la recommandation
    message_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    # Vérifier si la requête contient une recommandation (peut être dans le body)
    recommendation_data = None
    
    # Vérifier si la recommandation est dans le corps de la requête
    request_body = await request.json()
    if 'recommendation' in request_body:
        try:
            # La recommandation peut être une chaîne JSON ou un objet
            raw_recommendation = request_body['recommendation']
            
            # Si c'est une chaîne, essayer de la parser
            if isinstance(raw_recommendation, str):
                import json
                try:
                    recommendation_data = json.loads(raw_recommendation)
                    logging.info(f"Recommandation désérialisée depuis une chaîne JSON: {recommendation_data.get('plant', 'unknown')}")
                except json.JSONDecodeError:
                    logging.warning(f"Recommandation reçue sous forme de chaîne, mais pas au format JSON valide")
                    recommendation_data = {"plant": "Format invalide", "explanation": "Données de recommandation mal formatées"}
            # Si c'est déjà un objet (dict), l'utiliser directement
            elif isinstance(raw_recommendation, dict):
                recommendation_data = raw_recommendation
                logging.info(f"Recommandation reçue sous forme d'objet: {recommendation_data.get('plant', 'unknown')}")
            else:
                logging.warning(f"Format de recommandation non géré: {type(raw_recommendation)}")
                recommendation_data = None
        except Exception as e:
            logging.error(f"Erreur lors du traitement de la recommandation: {e}")
            recommendation_data = None
    
    # Créer le message final
    message = {
        "id": message_id,
        "consultation_id": consultation_id,
        "content": message_data.content,
        "sender": message_data.sender,
        "timestamp": now,
        "recommendation": recommendation_data  # Utiliser la recommandation traitée
    }
    
    # Insérer le message dans la base
    try:
        supabase_admin.table("messages").insert(message).execute()
        logging.info(f"Message inséré avec succès: {message_id}")
    except Exception as e:
        logging.error(f"Erreur lors de l'insertion du message: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du message: {str(e)}")
