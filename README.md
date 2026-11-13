# WESKA INK

Boutique Django/HTMX en français, avec catalogue public, panier, tunnel de commande, paiement Stripe Checkout, stock partagé boutique/caisse, interface POS et administration.

## Démarrage local

Python 3.12 ou plus récent est recommandé. Django 5.2 est utilisé.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py setup_roles
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Ouvre ensuite `http://127.0.0.1:8000/`. La boutique publique est sur `/`, la caisse sur `/equipe/caisse/`, le tableau de bord sur `/equipe/caisse/tableau-de-bord/`, les stocks sur `/equipe/stock/` et l'administration Django sur `/django-admin/`.

`seed_demo` ajoute six produits et des stocks fictifs, avec des prix et textes d'exemple. Remplace ces données, ajoute les visuels et vérifie les informations produit avant publication commerciale.

## Configuration à renseigner avant la vente

- **Produits et prix** : catalogue Django Admin. Une ligne de stock est créée automatiquement pour chaque nouveau produit.
- **Zones et tarifs de livraison** : Django Admin → Commandes → Zones de livraison. Tant qu'aucune zone active n'existe, seul le retrait est proposé.
- **Stripe** : renseigne `STRIPE_SECRET_KEY` et `STRIPE_WEBHOOK_SECRET` dans `.env`; configure le webhook Stripe vers `/paiements/stripe/webhook/` pour `checkout.session.completed` et `checkout.session.expired`. Le montant est recalculé côté serveur, puis vérifié sur le webhook signé.
- **Paiements POS** : `WESKA_POS_PAYMENT_METHODS=CASH,CARD` dans `.env`; adapte la liste aux moyens effectivement retenus.
- **Retrait, e-mail, mentions légales, CGV, confidentialité et contact** : complète les informations d'exploitation avant l'ouverture publique. Les pages affichent des textes provisoires à remplacer.
- **Images** : téléverse les visuels produit et de collection dans l'administration. Les visuels SVG inclus sont des illustrations de remplacement. Pour un stockage S3 compatible, configure `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME` et éventuellement `AWS_S3_ENDPOINT_URL` / `AWS_S3_CUSTOM_DOMAIN`; les médias restent locaux si aucun bucket n'est indiqué.

Les groupes `Administrateurs`, `Gestionnaires` et `Opérateurs de vente` sont préparés par `setup_roles`. Crée les comptes d'équipe avec Django Admin, coche « équipe », puis assigne le groupe adapté. Un superutilisateur conserve tous les droits.

Les connexions administratives sont protégées par django-axes : cinq tentatives erronées pour une même combinaison nom d'utilisateur/adresse IP déclenchent un verrouillage temporaire d'une heure.

## PostgreSQL et déploiement Docker

En local, l'application utilise SQLite. `DATABASE_URL` active PostgreSQL quand cette variable est définie.

```powershell
Copy-Item .env.example .env
# Renseigner DJANGO_SECRET_KEY, DJANGO_DEBUG=False, DJANGO_ALLOWED_HOSTS, Stripe et e-mail.
$env:POSTGRES_PASSWORD = "un-mot-de-passe-long"
docker compose up --build
```

Le conteneur applique les migrations, prépare les rôles, collecte les fichiers statiques puis démarre Gunicorn. Le média local Docker est persistant via un volume; un backend S3 compatible peut être activé par variables d'environnement. Configure aussi des sauvegardes PostgreSQL hors de cet hôte. N'utilise pas le mot de passe de démonstration du fichier Compose en production.

## Opérations utiles

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py setup_roles
python manage.py expire_reservations
python manage.py collectstatic --noinput
```

Planifie `expire_reservations` régulièrement (par exemple toutes les 5 minutes) avec le planificateur de tâches de l'hébergeur. Cette commande annule les commandes web impayées et restitue leurs quantités réservées. Configure les journaux, les sauvegardes et la supervision Stripe selon l'environnement choisi.

## Périmètre inclus

- Vitrine responsive avec filtres HTMX, collections, fiches produit et pages d'information provisoires.
- Panier de session, coordonnées de commande, retrait/livraison par zones, réservation temporaire de stock.
- Stripe Checkout côté serveur et webhook signé, avec traitement idempotent des événements.
- Point de vente, encaissement physique configuré, décrément de stock atomique et historique partagé.
- Back-office catalogue Django, suivi des stocks et mouvements, commandes, indicateurs essentiels et rôles.

L'espace client, la fidélité, les promotions, les prestations de pose, le remboursement Stripe et les exports ne sont pas encore inclus. Les textes juridiques et règles commerciales du document source doivent être validés et renseignés par WESKA INK avant mise en production.
# weska_-ink
