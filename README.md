# ⚠️ Dépôt archivé : remplacé par `geneweb-py`

Ce dépôt (parser regex « V2 », MVP) est **gelé** et n'évolue plus. Ses fonctions ont été
transférées et modernisées dans le dépôt [`geneweb-py`](https://github.com/Relais4x100a2/geneweb-py),
moteur central de l'écosystème TOLDOT.

| Ici (V2) | Désormais dans `geneweb-py` |
|---|---|
| `app/parser.py`, `regex.py` : extraction regex des `pevt`, familles, dates (`~ ? < > \| ..`), lieux `complément_-_lieu`, sources | `core/parser/` (parser complet, tests de fidélité sur les `pevt`/`#strng`), `core/date.py`, `core/place.py` |
| Organisations = familles + « organisations » déduites des événements | `core/organization.py` (`Organization`, `OrganizationLink`), `core/event_to_organization.py` (déduction avec hook LLM optionnel), fichier compagnon `*.org.json` |
| `app/data_export/network.py` : graphe individus / organisations / événements (CSV → NetworkX → Plotly) | `src/geneweb_py/analytics/network.py` (NetworkX, JSON vis.js, GraphML, GEXF, Pyvis ; extra `analytics`) |
| `app/flask_app.py`, `sitewebasync/` (Flask/Celery) | API REST FastAPI de `geneweb-py` (`api/`) |

Ce qui n'a pas été repris, volontairement : l'export CSV `csv_ind/csv_org/csv_evt`, le schéma
d'identités `app/data_schema.py` (`authorityRecord`, `othernames`) et le nettoyage `regex.py`
destiné à une base précise. Ils restent consultables ici comme référence.

Aucune donnée généalogique réelle ne doit être ajoutée à ce dépôt.

---

# Parser de fichier geneweb à des fins prosopographiques

### version MVP (Minimum Viable Product) 
La documentation est lacunaire et le code n'est pas très orthodoxe, notre objectif était d'arriver à une version MVP (Produit minimum viable).

Nous allons nous atteler à combler ces défauts dans les prochains mois.

D'ici là, n'hésitez pas à nous faire part de vos remarques ou à cloner le projet. Toute aide est la bienvenue !

***************************************************************************************
### POURQUOI UN PARSER DE FICHIER GENEWEB ?


Fasciné par les récits de mes grands-parents sur les mythes familiaux, je me suis très tôt intéressé à la généalogie. Et depuis quelques années, on peut dire que je m'y suis vraiment passionné. Toutefois, quelque chose me manquait.  En effet, par manque d'archives directes, j'ai très souvent poursuivi mes recherches en m'intéressant systématiquement à l'entourage de mes ancêtres (relations amicales, professionnelles, d'enfance, etc.), ce qui m'a conduit à m'intéresser à la prosopographie (science auxiliaire de l'histoire qui cherche à dégager les traits communs d’un groupe d’acteurs historiques en se fondant sur l’observation systématique de leurs vies et de leurs parcours). Faute d'outils, j'ai détourné les fins généalogiques de mon arbre en base prosopographique. N'étant pas conçu pour cela, je me suis retrouvé assez vite bridé par les outils de requêtes offert par geneweb. J'ai donc réfléchi à une solution pour résoudre ce problème, d'où ce parser (programme parcourant le contenu d'un fichier en l'analysant pour en extraire des éléments). Ce parser est la première brique d'un projet de plus grande échelle autour de la prosopographie.

<img src="notes_ressources/images/livre_proso.jpg" alt="drawing" width="200"/> <img src="notes_ressources/images/network.jpg" alt="drawing" width="200"/>





***************************************************************************************
