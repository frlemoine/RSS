# Flux RSS JADE

Cette application génère un flux RSS des nouvelles décisions publiées dans le fonds JADE, avec une page HTML statique par décision récente.

## Ce que fait le projet

- récupère la liste des archives quotidiennes JADE publiées par la DILA ;
- télécharge les nouvelles archives non encore traitées ;
- extrait les décisions XML ;
- génère `docs/rss.xml`, `docs/index.html` et une page HTML par décision ;
- conserve l'état dans `data/state.json` pour éviter les doublons ;
- peut être hébergé gratuitement sur GitHub Pages.

## Pourquoi cette architecture

En développement, on peut lancer un serveur web local sur le poste.

En production, le site est purement statique, donc il peut être hébergé gratuitement sur un tiers comme GitHub Pages sans serveur applicatif permanent.

## Prérequis

- Python 3.10 ou plus récent

Le projet n'a pas de dépendance externe.

## Lancer en local

1. Générer le site et le flux RSS :

```powershell
python app.py build --base-url http://localhost:8000
```

2. Démarrer le serveur local :

```powershell
python app.py serve --base-url http://localhost:8000
```

Le site sera disponible sur `http://127.0.0.1:8000` et le flux sur `http://127.0.0.1:8000/rss.xml`.

## Déploiement gratuit sur GitHub Pages

Le workflow fourni dans `.github/workflows/update-feed.yml` :

- exécute le build tous les jours ;
- met à jour `docs/` et `data/state.json` ;
- commit automatiquement les nouveautés dans le dépôt.

### Mise en place

1. Pousser le dépôt sur GitHub.
2. Activer GitHub Pages dans les paramètres du dépôt.
3. Choisir `Deploy from a branch`.
4. Sélectionner la branche par défaut et le dossier `/docs`.
5. Laisser le workflow planifié faire les mises à jour quotidiennes.

Le workflow calcule automatiquement l'URL publique du site GitHub Pages pour alimenter les liens du flux RSS.

## Notes utiles

- Lors du premier lancement, l'application importe les `5` dernières archives JADE pour éviter un bootstrap trop lourd.
- Ensuite, chaque exécution importe uniquement les nouvelles archives non encore traitées.
- Le flux conserve les `150` décisions les plus récentes.
- Les pages HTML de décision affichent le texte intégral extrait du XML officiel.

## Commandes utiles

Reconstruire le site sans lancer le serveur :

```powershell
python app.py build --base-url http://localhost:8000
```

Servir les fichiers déjà générés sans refaire le build :

```powershell
python app.py serve --no-refresh
```

Lancer les tests :

```powershell
python -m unittest discover -s tests
```
