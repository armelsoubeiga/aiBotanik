# Script PowerShell pour démarrer le backend aiBotanik

Write-Host "Démarrage du serveur backend aiBotanik..." -ForegroundColor Green

# Naviguer vers le répertoire du backend
Set-Location -Path "../../backend"

# Démarrer le serveur
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Maintenir la fenêtre ouverte si le serveur s'arrête
Write-Host "Appuyez sur une touche pour fermer..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
