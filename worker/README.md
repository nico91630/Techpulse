# Collecte manuelle en un clic (Cloudflare Worker)

Le bouton **Actualiser** de TechPulse peut lancer le workflow GitHub sans ouvrir GitHub, une fois ce Worker déployé. Le code du Worker est dans `worker/collect.js`.

## Configuration à faire une seule fois

1. Créer un Cloudflare Worker (offre gratuite possible) et y déployer `worker/collect.js`.
2. Créer un namespace Workers KV, le lier au Worker avec le nom **COOLDOWN**.
3. Ajouter le secret Worker **GITHUB_TOKEN** : jeton GitHub à droits minimaux, autorisé à déclencher les workflows de `nico91630/Techpulse`. Ne jamais placer ce secret dans le code public ni dans GitHub Pages.
4. Copier l'URL du Worker (par ex. `https://<worker>.workers.dev`) dans `worker/config.json`, champ `endpoint`, avec le chemin `/collect`.
5. Déployer le Worker et tester sur TechPulse. Le bouton déclenche le workflow ; les nouveaux articles apparaissent après la collecte et le déploiement Pages, pas immédiatement.

## Protection et limites

- Requêtes POST uniquement, origine autorisée et limite globale de 15 minutes via KV. **CORS et l'en-tête Origin ne sont pas une authentification** : une personne malveillante peut les imiter. KV est éventuellement cohérent et n'offre pas de verrou strict.
- Pour un endpoint public robuste, ajouter Cloudflare Turnstile avec vérification serveur ou Cloudflare Access / Durable Object, et un plafond de déclenchements par jour.
- Le quota GitHub Actions et les limites Cloudflare restent applicables.
- Sans URL Worker configurée, le bouton recharge seulement le JSON publié et affiche clairement qu'une collecte immédiate n'est pas encore activée.
