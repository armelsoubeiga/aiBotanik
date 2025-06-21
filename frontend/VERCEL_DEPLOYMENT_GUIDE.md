# Guide de Déploiement Vercel - aiBotanik Frontend

## ✅ Corrections Appliquées

### 1. Configuration des Alias de Modules
- **tsconfig.json** : Alias `@/*`, `@/components/*`, `@/lib/*`, etc. configurés avec `baseUrl: "."`
- **jsconfig.json** : Configuration identique pour VSCode et Webpack
- **next.config.mjs** : Alias Webpack explicites pour résolution sur Vercel

### 2. Compatibilité React/Dependencies
- React downgraded à 18.2.0 pour compatibilité avec react-day-picker
- Types React mis à jour (@types/react ^18.2.0)
- Section `overrides` dans package.json pour forcer les versions

### 3. Configuration Node.js
- **package.json** : Section `engines` spécifie Node >=18.0.0
- **.nvmrc** : Force Node 18.18.0
- **.node-version** : Force Node 18.18.0

### 4. Configuration Vercel
- **vercel.json** : Configuration minimale avec variable d'environnement
- Scripts nettoyés dans package.json

### 5. Code Fixes
- **lib/config.ts** : Formatage corrigé, détection d'environnement améliorée
- **lib/utils.ts** : Vérifié existant
- **components/ui/*** : Vérifiés existants

## 📋 Checklist pour Déploiement Vercel

### Avant le Déploiement
1. ✅ Push toutes les modifications vers le repo Git
2. ⚠️ **IMPORTANT** : Vider le cache Vercel avant build

### Vider le Cache Vercel
1. Aller sur le dashboard Vercel
2. Sélectionner votre projet
3. Aller dans Settings > Functions
4. Cliquer sur "Clear Cache" ou "Redeploy"
5. OU utiliser l'API Vercel : `curl -X POST "https://api.vercel.com/v1/projects/{PROJECT_ID}/invalidate-cache" -H "Authorization: Bearer {TOKEN}"`

### Variables d'Environnement Vercel
Ajouter dans Vercel Dashboard > Settings > Environment Variables :
```
NEXT_PUBLIC_API_URL=https://aibotanik.onrender.com
```

### Commandes de Test Local
```bash
cd frontend
npm install
npm run build  # ✅ Doit passer sans erreurs
npm start      # Test en mode production
```

## 🚀 Déploiement

1. **Connecter le Repository** à Vercel
2. **Configuration Build** :
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`
   - Development Command: `npm run dev`

3. **Node.js Version** : Vercel détectera automatiquement 18.18.0 grâce aux fichiers `.nvmrc` et `.node-version`

## 🔍 Vérifications Post-Déploiement

### Tests à Effectuer
1. ✅ Build réussi sans erreurs d'alias
2. ✅ Imports `@/lib/config`, `@/lib/utils` fonctionnent
3. ✅ Imports `@/components/ui/*` fonctionnent
4. ✅ Détection automatique de l'URL backend (prod vs dev)
5. ✅ Interface utilisateur s'affiche correctement

### Debugging
Si erreurs d'imports persistent :
1. Vérifier les logs de build Vercel
2. S'assurer que le cache a été vidé
3. Vérifier que Node.js 18 est utilisé
4. Vérifier les variables d'environnement

## 📁 Fichiers Modifiés

```
frontend/
├── lib/config.ts                  # ✅ Formatage corrigé
├── tsconfig.json                  # ✅ Alias configurés
├── jsconfig.json                  # ✅ Créé/corrigé
├── next.config.mjs               # ✅ Alias Webpack
├── package.json                  # ✅ React 18, engines, overrides
├── .nvmrc                        # ✅ Node 18.18.0
├── .node-version                 # ✅ Node 18.18.0
└── vercel.json                   # ✅ Config basique
```

## 🎯 Résultat Attendu

- ✅ Build local OK (testé et validé)
- ✅ Tous les alias d'imports résolus
- ✅ Compatibilité React/react-day-picker
- ✅ Configuration Node.js forcée
- ✅ Variables d'environnement gérées
- ✅ Prêt pour déploiement Vercel

---

**Dernière mise à jour** : $(Get-Date)
**Status** : ✅ PRÊT POUR DÉPLOIEMENT
