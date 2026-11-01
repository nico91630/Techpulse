# TechPulse 5.0 — notifications en arrière-plan

Le service worker `sw.js` gère désormais les événements `push` et `notificationclick`. Cela **ne suffit pas** pour envoyer des notifications lorsque le site est fermé.

## Dépendances nécessaires

1. Un serveur d'abonnement Web Push (ex. Cloudflare Worker + KV/D1, Supabase Edge Function + base, ou un service Web Push). GitHub Pages seul ne peut pas conserver les abonnements de façon sécurisée.
2. Une paire de clés VAPID générée côté serveur ; garder la clé privée exclusivement dans les secrets du service.
3. Un endpoint HTTPS d'abonnement et désabonnement, une politique de conservation et une suppression des abonnements expirés. Ne pas committer les abonnements dans le dépôt public.
4. Un contrôle explicite d'opt-in dans l'interface : demander la permission après action de l'utilisateur, appeler `registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:publicVapidKey})`, transmettre l'abonnement au serveur.
5. Un job de veille périodique qui détecte les nouveaux articles pertinents par abonnement, applique un anti-doublon et envoie les notifications via Web Push.
6. Tester Android Chrome/PWA et iOS Safari (sur iOS, les notifications Web Push requièrent l'application web ajoutée à l'écran d'accueil et une version compatible).

## Situation actuelle

- Notifications quand TechPulse est ouvert : option locale existante.
- Réception de notifications push dans le service worker : code prêt.
- Souscription, stockage des abonnements et expédition : **non configurés**. Aucune notification en arrière-plan ne sera envoyée avant l'ajout de ces services.

## Sécurité et qualité

Ne jamais publier de clé VAPID privée, de jeton d'accès ou de liste d'abonnés dans GitHub Pages. Limiter la fréquence des notifications et proposer un désabonnement accessible.
