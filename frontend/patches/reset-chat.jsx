// Code à ajouter à chat-interface.tsx juste avant le return() 

// Effet pour surveiller les changements d'authentification et réinitialiser si déconnexion
useEffect(() => {
  // Si l'utilisateur vient de se déconnecter (le props est passé de true à false)
  if (propIsAuthenticated === false && prevPropAuthState.current === true && messages.length > 0) {
    console.log("Déconnexion détectée dans ChatInterface - Réinitialisation du chat");
    
    // Réinitialiser les messages
    setMessages([]);
    
    // Réinitialiser l'input
    setInputValue("");
    
    // Réinitialiser le mode de discussion
    setChatMode("discussion");
    
    // Réinitialiser la consultation actuelle
    setCurrentConsultation(null);
    
    // Réinitialiser l'état de consultation historique
    setIsHistoricalConsultation(false);
    
    // Réinitialiser l'état du choix utilisateur
    setUserChooseContinueWithoutLogin(false);
    setPendingSaveConversation(false);
    setPendingMessage("");
    
    // Notifier le composant parent
    if (onConversationChange) {
      onConversationChange({
        messages: [],
        mode: "discussion",
        consultation: null
      });
    }
  }
  
  // Mettre à jour l'état précédent pour le prochain render
  prevPropAuthState.current = propIsAuthenticated;
}, [propIsAuthenticated, messages, onConversationChange]);
