# ByteStream — L'actu tech sans filtre

> Blog tech automatique style Korben.info, 100% gratuit, mis à jour 4x/jour par IA.

## Stack

| Composant | Service | Coût |
|-----------|---------|------|
| Hébergement | GitHub Pages | Gratuit |
| Automatisation | GitHub Actions | Gratuit (repo public) |
| Génération IA | Gemini 2.0 Flash API | Gratuit (1500 req/jour) |
| Sources | RSS publics (Ars Technica, The Verge, HN...) | Gratuit |

**Total : 0 €/mois**

## Installation en 5 minutes

### 1. Fork ce repo
Clique sur "Fork" en haut à droite.

### 2. Obtenir une clé Gemini API (gratuite)
1. Va sur [aistudio.google.com](https://aistudio.google.com)
2. Clique sur **Get API Key**
3. Crée une clé (plan gratuit largement suffisant)

### 3. Ajouter la clé dans GitHub
Dans ton repo forké :
1. **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Nom : `GEMINI_API_KEY`
4. Valeur : ta clé Gemini

### 4. Activer GitHub Pages
1. **Settings** → **Pages**
2. Source : **Deploy from a branch**
3. Branch : `main` / root `/`
4. Ton site est en ligne sur `https://TON-USERNAME.github.io/NOM-DU-REPO`

### 5. Premier lancement
Va dans **Actions** → **Génération automatique articles** → **Run workflow**

C'est tout. Le site se met à jour automatiquement 4x/jour.

## Personnalisation

### Changer le nom du site
Dans `generate.py`, modifie la constante `OUTPUT_HTML` et le titre dans la fonction `generate_html()`.

### Ajouter des sources RSS
Ajoute des URLs dans la liste `RSS_FEEDS` dans `generate.py`.

### Modifier le style éditorial
Édite le `SYSTEM_PROMPT` dans `generate.py` pour ajuster le ton.

### Fréquence de mise à jour
Modifie le `cron` dans `.github/workflows/update.yml`.
Exemple pour toutes les 3 heures : `'0 */3 * * *'`

### Domaine custom
Dans GitHub Pages, tu peux ajouter un domaine personnalisé gratuitement.

## Architecture

```
generate.py         ← script principal
articles.json       ← cache des articles générés (persisté dans le repo)
index.html          ← site généré (mis à jour à chaque run)
.github/workflows/
  update.yml        ← automatisation GitHub Actions
```

## Limites du free tier Gemini

- 15 requêtes/minute
- 1 500 requêtes/jour
- Avec 5 articles par run × 4 runs/jour = 20 articles/jour → largement dans les clous

## Licence

MIT — fais-en ce que tu veux.
