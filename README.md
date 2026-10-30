# TechPulse personnel

Site statique GitHub Pages + collecte RSS Python par GitHub Actions, toutes les 3 heures (horaire indicatif). Les flux RSS peuvent changer, bloquer ou devenir indisponibles. Les articles renvoient vers leurs éditeurs ; pas de réécriture IA.

## Installation
Téléverser les fichiers à la racine du dépôt, y compris `.github/workflows/actualites.yml` et `collect.py`. Dans Settings > Pages : Deploy from a branch > main > /(root). Dans Actions > Actualites automatiques > Run workflow : lancer une première collecte. Dans Settings > Actions > General > Workflow permissions, autoriser Read and write permissions si nécessaire. Vérifier le fichier `articles.json` après l'exécution. Si aucun flux ne répond, voir les logs de l'action.
