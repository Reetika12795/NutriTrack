# NutriTrack - Notes de Presentation (en francais)

> Ce que vous devez dire a chaque diapositive. Lisez ce document avant la soutenance. Gardez un ton naturel -- ce sont des points de repere, pas un script a lire mot pour mot.

---

## DIAPOSITIVE 1 : Titre

**Dire (10 secondes) :**
"Bonjour, je m'appelle Reetika Gautam. Je vous presente aujourd'hui NutriTrack, une plateforme d'ingenierie de donnees nutritionnelles, dans le cadre de ma certification RNCP niveau 7 -- Expert en infrastructures de donnees massives."

> Astuce : Souriez, faites une pause, regardez le jury. La premiere impression compte.

---

## DIAPOSITIVE 2 : Agenda de la soutenance - 90 minutes

**Dire (30 secondes) :**
"Voici le plan pour les 90 prochaines minutes. Je vais consacrer les 60 premieres minutes aux evaluations E1 a E5 -- de l'analyse du besoin jusqu'a l'entrepot de donnees. J'inclurai des demonstrations en direct tout au long. Ensuite, 10 minutes pour E6, les questions sur la maintenance de l'entrepot. Puis 10 minutes pour E7, le data lake. Et nous terminerons par 10 minutes de questions du jury."

"Le rapport vous a ete remis, le code est sur GitHub, et je ferai des demos en direct a chaque etape."

---

## DIAPOSITIVE 3 : Rencontre avec la cliente - Mme Sophie Yang

**Dire (60 secondes) :**
"Permettez-moi de vous presenter la cliente qui est a l'origine de tout ce projet : Sophie Yang, une dieteticienne a Paris qui recoit plus de 40 patients par semaine."

"Sophie rencontre cinq problemes au quotidien :" *(montrer chaque point)*

1. "Elle cherche manuellement les produits sur Open Food Facts -- cela prend des heures."
2. "Elle calcule les macronutriments dans des tableurs -- c'est sujet aux erreurs et tres lent."
3. "Elle ne peut pas suivre les progres de ses patients dans le temps."
4. "Ses donnees sont dispersees entre cinq outils et sources differents."
5. "Elle manipule des donnees de sante sensibles sans aucune conformite RGPD."

"Ses mots exacts : *Je passe des heures a chercher des produits. J'ai besoin d'une plateforme ou mes patients enregistrent leurs repas et ou je vois les analyses.*"

"C'est la competence C1 -- analyser l'expression du besoin d'un projet data. Les problemes de Sophie orientent chaque choix technique de ce projet."

> Astuce : Cette diapositive pose le recit ENTIER. Chaque fonctionnalite que vous demontrerez plus tard se rattache a un probleme de Sophie.

---

## DIAPOSITIVE 4 : Grilles d'entretien (C1)

**Dire (30 secondes) :**
"Donc, a partir des problemes de Sophie, la premiere chose que j'ai faite a ete de formaliser l'analyse du besoin. J'ai cree deux grilles d'entretien : une pour les producteurs de donnees -- les personnes qui creent et gerent les donnees -- et une pour les consommateurs de donnees -- Sophie et son equipe qui utiliseront la plateforme."

"La grille producteur interroge sur les activites metier, les types de donnees, les volumes, les controles qualite et les contraintes d'acces. La grille consommateur interroge sur les objectifs d'analyse, la granularite, le format de livraison, les contraintes RGPD et les besoins d'accessibilite."

"Ces grilles sont le fondement de toutes les decisions techniques qui suivent."

---

## DIAPOSITIVE 5 : Objectifs SMART (C1)

**Dire (30 secondes) :**
"A partir des entretiens, j'ai defini des objectifs SMART."

"Specifique : centraliser les donnees de plus de 5 sources. Mesurable : plus de 777 000 produits avec des requetes en moins de 5 secondes. Atteignable : tout en open source, base sur Docker. Relevant : repond directement au probleme de donnees nutritionnelles fragmentees de Sophie. Temporel : un calendrier de 12 semaines."

"L'avant-projet comprend des recommandations techniques, un plan d'action RGPD, une planification de l'accessibilite et une priorisation RICE pour l'ordonnancement des fonctionnalites."

---

## DIAPOSITIVE 6 : NutriTrack - Construit pour Sophie

**Dire (45 secondes) :**
"Maintenant que vous comprenez le besoin et les objectifs, voici ce que nous avons construit, en lien direct avec les besoins de Sophie."

*(Montrer chaque correspondance)*
- "Elle cherche les produits manuellement ? Nous avons construit 5 extracteurs automatises et une recherche de produits unifiee."
- "Elle ne peut pas suivre les repas de ses patients ? Nous avons construit un journal de repas avec des tableaux de bord quotidiens et des tendances hebdomadaires."
- "Elle s'inquiete de la conformite ? Nous avons implemente le RGPD complet : suivi du consentement, registre des donnees, nettoyage automatique et pseudonymisation."

"Au total : plus de 777 000 produits, 14 services Docker, 7 DAGs Airflow, 4 roles utilisateur, et toute la plateforme se deploie en une seule commande."

---

## DIAPOSITIVE 7 : Open Food Facts - Source de donnees principale

**Dire (45 secondes) :**
"Notre source de donnees principale est Open Food Facts, une association francaise a but non lucratif fondee en 2012. C'est comme Wikipedia pour les produits alimentaires -- communautaire, avec plus de 3 millions de produits et 30 000 contributeurs."

"Ce qui la rend precieuse pour nous : elle fournit le Nutri-Score de A a E pour la qualite nutritionnelle, les groupes NOVA de 1 a 4 pour le niveau de transformation, l'Eco-Score pour l'impact environnemental, les listes d'ingredients completes, les declarations d'allergenes et 31 champs nutritionnels par produit."

"C'est open source sous licence ODbL, utilise par des applications connues comme Yuka et Foodvisor. Nous l'avons choisie car elle correspond parfaitement au besoin de Sophie en donnees nutritionnelles fiables et transparentes."

---

## DIAPOSITIVE 8 : Formats de donnees OFF et extraction

**Dire (40 secondes) :**
"Nous accedon a Open Food Facts par deux methodes."

"Premierement : l'API REST. Nous interrogeons 5 categories alimentaires quotidiennement, avec une limitation de debit a 0,6 seconde entre les appels. Cela nous donne environ 1 000 produits nouveaux ou mis a jour par jour en format JSON."

"Deuxiemement : l'export massif en Parquet depuis HuggingFace. Le dump complet de plus de 3 millions de produits, filtre pour la France, ce qui nous donne environ 798 000 produits francais avec une completude superieure a 0,3. Cela s'execute chaque semaine."

"A droite, vous voyez un exemple reel -- le Nutella, code-barres 3017620422003. 31 champs : energie, lipides, sucres, Nutri-Score D, NOVA groupe 4. Mais attention : les donnees sont desordonnees -- nommage inconsistant, valeurs manquantes. C'est pourquoi le nettoyage est critique."

---

## DIAPOSITIVE 9 : Nettoyage des donnees - Avant / Apres (C10)

**Dire (50 secondes) :**
"C'est la competence C10 -- aggregation et nettoyage des donnees. Laissez-moi vous presenter nos 7 regles de nettoyage, toutes executees par PySpark."

*(Montrer chaque regle)*
1. "Renommage des colonnes : l'API utilise `energy-kcal_100g`, nous standardisons en `energy_kcal`."
2. "Nettoyage des codes-barres : suppression des caracteres non numeriques, conservation uniquement des codes de 8 a 14 chiffres."
3. "Normalisation du Nutri-Score : le 'd' minuscule devient 'D' majuscule."
4. "Plafonnement des valeurs : si energy_kcal vaut 2000 pour 100g, c'est physiologiquement impossible -- on met NULL."
5. "Les noms de produits nuls sont supprimes -- pas de nom, pas de produit."
6. "Deduplication : si le meme code-barres apparait deux fois, on garde l'enregistrement avec le score de completude le plus eleve."
7. "Generation du rapport de nettoyage avec les metriques de qualite."

"Resultat : 798 177 enregistrements bruts deviennent 777 126 enregistrements propres. Un taux de suppression de 2,6 %. PySpark traite le tout en moins de 3 minutes. Puis 6 controles de qualite formels sont executes et enregistres dans la table `staging.data_quality_checks`."

---

## DIAPOSITIVE 10 : Flux de donnees de bout en bout

**Dire (40 secondes) :**
"Voici le flux de donnees complet, de bout en bout."

"A 2h du matin : 5 scripts d'extraction recuperent les donnees depuis nos sources en fichiers bruts. A 4h : PySpark execute le pipeline de nettoyage -- il agrege, valide et nettoie tout. A 4h30 : les donnees nettoyees sont importees dans la base PostgreSQL applicative. A 5h : l'ETL de l'entrepot et l'ingestion du data lake s'executent en parallele."

"Ensuite, tous les publics sont servis via Streamlit -- utilisateurs, dieteticiens, analystes et administrateurs voient chacun des tableaux de bord specifiques a leur role. L'equipe ops surveille via Grafana."

"Tout est entierement automatise avec Apache Airflow."

---

## DIAPOSITIVE 11 : Une commande, 15 services

**Dire (30 secondes) :**
"Toute la plateforme demarre avec une seule commande : `docker compose up -d`."

"14 services organises en 4 groupes : Infrastructure -- PostgreSQL, Redis, MinIO. Orchestration -- Airflow avec webserver, scheduler et worker. Couche applicative -- FastAPI et Streamlit avec 4 tableaux de bord par role. Monitoring -- Prometheus, Grafana, exporteur StatsD et MailHog pour les alertes."

"Pourquoi Docker Compose ? La reproductibilite. N'importe quelle machine avec Docker peut executer la plateforme complete. C'est essentiel pour la demo et pour la transmission du projet a l'equipe IT de Sophie."

> DEMO : Vous pouvez montrer `docker compose ps` dans un terminal.

---

## DIAPOSITIVE 12 : Stack technique - Quoi et Pourquoi

**Dire (45 secondes) :**
"Chaque outil a ete choisi pour une raison."

"Extraction et nettoyage : l'API OFF, BeautifulSoup pour le scraping, DuckDB pour les requetes SQL sur les fichiers Parquet. PySpark 3.5 pour le pipeline de nettoyage -- capable de traitement distribue, il traite 798 000 lignes en moins de 3 minutes. Trois types de sources comme exige par C8."

"Orchestration : Airflow 2.8 plutot que Prefect, car Airflow est plus mature avec une meilleure interface et le support Celery pour la montee en charge."

"Stockage : PostgreSQL pour les transactions ACID et la suppression RGPD par ligne. MinIO comme data lake compatible S3, gratuit et auto-heberge. Redis pour le cache et comme broker Celery."

"Exposition : FastAPI pour l'API REST asynchrone avec authentification JWT. Streamlit comme frontend unique avec 4 tableaux de bord par role."

"Monitoring : Prometheus et Grafana avec 6 tableaux de bord. MailHog pour les alertes par email. Cela couvre C16."

---

## DIAPOSITIVE 13 : Decisions techniques cles (C3)

**Dire (40 secondes) :**
"La competence C3 exige de documenter les decisions d'architecture. Voici quatre decisions cles."

"PostgreSQL plutot que MongoDB : nous avons besoin de transactions ACID pour l'integrite des donnees et de la suppression par ligne pour la conformite RGPD. MongoDB ne supporte pas facilement la suppression transactionnelle RGPD."

"Airflow plutot que Prefect : un ecosysteme plus mature, eprouve a grande echelle, une meilleure interface pour le monitoring."

"MinIO plutot que AWS S3 : auto-heberge signifie zero cout cloud et zero dependance fournisseur. L'API compatible S3 permet de migrer vers AWS plus tard si besoin."

"Streamlit multi-role plutot que Superset : un service de moins a maintenir, le RBAC base sur JWT est integre dans l'application."

---

## DIAPOSITIVE 14 : PostgreSQL - Trois zones

**Dire (30 secondes) :**
"Nous utilisons une seule instance PostgreSQL mais avec trois zones logiques."

"Le schema `app` est l'application en production -- produits, utilisateurs, repas. FastAPI et Streamlit lisent et ecrivent ici."

"Le schema `dw` est l'entrepot -- schema en etoile avec 7 dimensions et 2 tables de faits. Le tableau de bord analyste de Streamlit lit d'ici via FastAPI."

"Et MinIO est le data lake -- des buckets bronze, silver et gold dans une architecture medallion. Uniquement des fichiers Parquet. La couche gold inclut 4 jeux de donnees agreges anonymises : nutrition_patterns, popular_products, brand_rankings et category_stats. Utilises par les data scientists."

"L'ETL alimente l'entrepot depuis l'application, et en parallele le lac de donnees."

---

## DIAPOSITIVE 15 : Pourquoi un entrepot ET un lac ?

**Dire (40 secondes) :**
"Une question frequente : pourquoi ne pas avoir un seul ?"

"L'entrepot contient les donnees produits ET les donnees utilisateurs. Il offre les transactions ACID, la suppression RGPD par ligne, le filtrage du consentement par requete et des requetes de tableau de bord en moins de 100ms. Il sert les analystes BI."

"Le lac contient les donnees produits UNIQUEMENT. Jamais de donnees utilisateurs. Pourquoi ? Les fichiers Parquet sont immuables -- on ne peut pas supprimer les lignes d'un seul utilisateur dans un fichier Parquet. Donc pour la conformite RGPD, les donnees personnelles doivent rester dans PostgreSQL ou nous pouvons effectuer des suppressions individuelles."

"C'est une decision d'architecture deliberee dictee par le RGPD, pas simplement par des preferences technologiques."

---

## DIAPOSITIVE 16 : Topographie des donnees (C2)

**Dire (30 secondes) :**
"C2 exige de cartographier toutes les donnees en quatre dimensions."

"Semantique : 9 objets metier documentes dans un glossaire avec les metadonnees."
"Modeles de donnees : donnees structurees dans PostgreSQL, JSON semi-structure depuis les API, fichiers Parquet non structures."
"Flux : 8 flux source-cible documentes dans une matrice de flux avec les diagrammes ETL."
"Acces : matrice d'acces par role avec 3 niveaux et les contraintes RGPD."

---

## DIAPOSITIVE 17 : Architecture systeme (C3)

**Dire (20 secondes) :**
"Voici l'architecture complete -- 14 services avec leurs ports. Trois sources de donnees alimentent Airflow, qui charge PostgreSQL et MinIO. PostgreSQL sert FastAPI. FastAPI sert Streamlit, qui est le frontend unique pour les 4 roles. Prometheus collecte les metriques de tous les services et alimente Grafana."

"Chaque fleche represente une connexion reseau reelle entre les conteneurs Docker."

---

## DIAPOSITIVE 18 : Matrice de flux (C2, C3)

**Dire (20 secondes) :**
"La matrice de flux documente les 8 flux de donnees. Source, format, cible, nom du script et frequence. De l'API OFF quotidiennement, au Parquet hebdomadairement, au scraping mensuellement. Chaque flux a un script Python dedie, tous versiones sur Git."

---

## DIAPOSITIVE 19 : Veille technologique (C4)

**Dire (30 secondes) :**
"C4 exige une veille technologique reguliere. Je suis trois sujets chaque semaine, en y consacrant environ 1 heure par semaine."

"Streamlit multi-role RBAC : nous avons construit un systeme de tableaux de bord a 4 roles avec un controle d'acces base sur JWT. Applique dans le projet."
"Mise a jour RGPD : l'EDPB a publie des lignes directrices en janvier 2026 indiquant que les donnees de bien-etre sont sensibles. Nous sommes conformes."
"Airflow 2.8 : backend de stockage objet et hooks de listener. Note pour implementation future."

"Tout est documente dans `docs/veille_technologique.md` avec la fiabilite des sources verifiee."

---

## DIAPOSITIVE 20 : Conformite RGPD (C3, C11)

**Dire (40 secondes) :**
"Le RGPD n'est pas une reflexion apres coup -- c'est integre dans l'architecture."

"Quatre piliers :"
"Registre des donnees : une table `rgpd_data_registry` documentant la base legale de chaque champ et les periodes de retention."
"Consentement : case a cocher obligatoire a l'inscription. La date de consentement est tracee. Pas de consentement, pas de compte."
"Nettoyage automatique : une fonction planifiee `rgpd_cleanup_expired_data` qui supprime les repas de plus de 2 ans et les utilisateurs dont la retention est expiree."
"Securite : mots de passe hashes avec bcrypt, utilisateurs identifies par UUID et non par email, et pseudonymisation SHA256 dans l'entrepot."

"Point critique : les donnees personnelles restent dans PostgreSQL ou nous pouvons faire de la suppression par ligne. Les donnees publiques des produits vont a la fois dans l'entrepot et dans le lac."

---

## DIAPOSITIVE 21 : Feuille de route en 6 phases (C5)

**Dire (30 secondes) :**
"Le projet a ete planifie en 6 phases sur 12 semaines. Mise en place en semaines 1-2, extraction en 3-4, transformation en 5-6, entrepot en 7-8, lac en 9-10, et deploiement avec monitoring en semaines 11-12."

"Nous avons utilise des story points Fibonacci pour l'estimation, des rituels Agile -- planification, standup, revue, retrospective -- et 5 roles definis : ingenieur data, ingenieur plateforme, ingenieur CI/CD, auditeur et relecteur."

---

## DIAPOSITIVE 22 : Indicateurs de suivi (C6)

**Dire (20 secondes) :**
"C6 exige des indicateurs de suivi. Nous en suivons quatre : le taux de succes des DAGs depuis Airflow, les entrees du journal d'activite -- 22 entrees sur 14 jours, le pourcentage de completude par jeu de donnees et les tendances de duree des ETL dans le temps. Visible dans l'interface Airflow et le tableau de bord SLA de Grafana."

---

## DIAPOSITIVE 23 : Communication multi-audience (C7)

**Dire (20 secondes) :**
"C7 exige d'adapter la communication au public. Les developpeurs ont Swagger, ReDoc, Grafana et MkDocs. Les analystes ont le tableau de bord Product Analytics et le catalogue de donnees dans Streamlit. Les dieteticiens ont les analyses utilisateurs. Les utilisateurs finaux ont le suivi des repas et la recherche de produits."

"Le bon outil pour le bon public."

---

## DIAPOSITIVE 24 : 5 sources d'extraction (C8)

**Dire (30 secondes) :**
"C8 exige l'extraction depuis 5 types de sources. Nous avons :"
"API REST : Open Food Facts, plus de 1 000 produits par jour."
"Fichier de donnees : export Parquet massif, 798 000 produits."
"Web Scraping : les recommandations nutritionnelles de l'ANSES et de l'EFSA avec BeautifulSoup."
"Base de donnees : extraction directe PostgreSQL."
"Systeme Big Data : DuckDB executant du SQL directement sur les fichiers Parquet -- plus de 3 millions de lignes sans serveur de base de donnees. PySpark prend le relais pour le nettoyage apres l'extraction par DuckDB."

"Les 5 alimentent `aggregate_clean.py` qui fusionne et standardise tout avec PySpark."

---

## DIAPOSITIVE 25 : Detail de l'API REST (C8)

**Dire (20 secondes) :**
"Voici la structure de `extract_off_api.py`. Il configure 5 categories alimentaires, envoie des requetes GET paginates, respecte la limitation de debit a 0,6 seconde, inclut un en-tete User-Agent, encapsule chaque page dans un try/except pour la gestion des erreurs et sauvegarde le JSON dans `/data/raw/api/`. Les 5 scripts d'extraction suivent cette meme structure."

---

## DIAPOSITIVE 26 : Scraping et DuckDB (C8)

**Dire (20 secondes) :**
"Deux autres types de sources. Le web scraping cible l'ANSES et l'EFSA pour les recommandations nutritionnelles officielles avec BeautifulSoup et des valeurs AJR de secours. Execution mensuelle."

"DuckDB gere l'extraction -- du SQL directement sur les fichiers Parquet, 3 millions de lignes, pas de base de donnees necessaire, le stockage en colonnes permet des scans analytiques rapides. PySpark gere le nettoyage -- une transformation distribuee sur 798 000 lignes. DuckDB sort les donnees, PySpark les nettoie."

---

## DIAPOSITIVE 27 : Pipeline de nettoyage (C10)

**Dire (20 secondes) :**
"Les 7 etapes de nettoyage, toutes executees dans PySpark : standardisation des noms de colonnes, validation des codes-barres, suppression des noms de produits nuls, plafonnement des valeurs nutritionnelles aux maximums physiologiques, normalisation du Nutri-Score en majuscules, deduplication par code-barres en conservant l'enregistrement le plus complet, et generation du rapport de nettoyage."

"Apres le nettoyage, 6 controles de qualite formels sont executes : seuil de nombre de lignes, unicite des codes-barres, taux de nulls par colonne, validation des plages sur les champs nutritionnels, validation des valeurs Nutri-Score. Tous les resultats sont enregistres dans la table `staging.data_quality_checks`."

---

## DIAPOSITIVE 28 : 7 requetes SQL (C9)

**Dire (20 secondes) :**
"C9 exige des requetes SQL d'extraction optimisees. Nous en avons 7, chacune utilisant une technique differente : recherche plein texte avec index GIN, fonctions de fenetre avec ROW_NUMBER, CTE pour eviter les scans repetes, fonctions analytiques, LAG pour les tendances temporelles, GROUP BY avec HAVING, et vues materialisees avec jointures complexes. Toutes documentees avec la sortie EXPLAIN ANALYZE."

---

## DIAPOSITIVE 29 : Base de donnees conforme RGPD (C11)

**Dire (30 secondes) :**
"C11 : creation de la base de donnees conforme RGPD. Nous avons suivi la methodologie MERISE : MCD vers MLD vers MPD."

"8 tables avec integrite referentielle complete. La table `rgpd_data_registry` en rouge documente chaque champ de donnees personnelles. Les colonnes de consentement sur la table utilisateurs. Une fonction de nettoyage pour les donnees expirees. Hachage bcrypt des mots de passe et identification par UUID."

---

## DIAPOSITIVE 30 : API REST FastAPI (C12)

**Dire (45 secondes) :**
"C12 : l'API REST. Huit endpoints couvrant l'authentification, la recherche de produits, la recherche par code-barres, les alternatives plus saines, l'enregistrement des repas et les bilans nutritionnels."

"Le flux d'authentification :" *(montrer le cote droit)*
"Etape 1 : l'utilisateur se connecte avec son nom d'utilisateur et son mot de passe."
"Etape 2 : l'API cree un token JWT -- une chaine signee numeriquement contenant l'ID utilisateur, le role et une expiration de 60 minutes."
"Etape 3 : a chaque requete suivante, l'API decode le token, verifie le role et applique le controle d'acces."
"Etape 4 : les reponses sont validees avec des schemas Pydantic."

"Trois roles : l'utilisateur voit ses propres donnees, le dieteticien voit les analyses de tous les utilisateurs, l'administrateur voit tout y compris le catalogue de donnees."

> DEMO : "Permettez-moi de vous montrer l'interface Swagger a localhost:8000/docs"

---

## DIAPOSITIVE 31 : Streamlit - Deux parties (C7, C20)

**Dire (30 secondes) :**
"Le frontend Streamlit a deux parties. L'application utilisateur sur le port 8501 : recherche de produits, journal des repas, tableau de bord macro quotidien, tendances hebdomadaires, comparaison de produits et alternatives plus saines. Elle consomme l'API REST FastAPI."

"La page catalogue de donnees : recherche de jeux de donnees, navigation dans les couches bronze/silver/gold, visualisation des schemas et de la lignee, controle des metriques de qualite et consultation des informations de gouvernance et RGPD. Elle se connecte directement a MinIO."

> DEMO : "Permettez-moi de vous montrer l'application Streamlit. Je vais me connecter d'abord en tant qu'utilisateur, puis en tant que dieteticien, puis en tant qu'admin pour montrer le controle d'acces par role."

---

## DIAPOSITIVE 32 : Schema en etoile (C13)

**Dire (30 secondes) :**
"C13 : modelisation de l'entrepot. Nous utilisons un schema en etoile avec 7 tables de dimensions et 2 tables de faits, selon l'approche ascendante de Kimball."

"Deux tables de faits : `fact_daily_nutrition` suit les donnees de repas des utilisateurs, et `fact_product_market` suit la disponibilite et la qualite des produits. Elles partagent `dim_product` et `dim_time`."

"Plus 6 vues datamart qui pre-calculent les requetes analytiques courantes pour que les analystes n'aient pas a ecrire des jointures complexes."

---

## DIAPOSITIVE 33 : 6 vues Datamart (C13, C14)

**Dire (20 secondes) :**
"Six vues pre-construites : suivi nutritionnel quotidien pour les dieteticiens, disponibilite des produits par categorie pour les analystes marche, classement qualite des marques, distribution du Nutri-Score pour la sante publique, tendances nutritionnelles pour les data scientists, et metriques de sante de l'entrepot pour les administrateurs."

"Les datamarts epargnent aux analystes l'ecriture de jointures sur le schema en etoile -- ils interrogent simplement une vue."

---

## DIAPOSITIVE 34 : Pipeline ETL - 7 DAGs (C15)

**Dire (30 secondes) :**
"C15 : le pipeline ETL, orchestre par 7 DAGs Airflow."

"Trois DAGs d'extraction s'executent a 2h du matin. Le DAG de nettoyage s'execute a 4h. Puis a 5h, le chargement de l'entrepot et l'ingestion du lac s'executent en parallele."

"Un septieme DAG gere les sauvegardes et la maintenance a 6h."

"La coordination inter-DAGs utilise `ExternalTaskSensor` -- les DAGs de l'entrepot et du lac attendent que le nettoyage soit termine avant de demarrer."

> DEMO : "Permettez-moi de vous montrer l'interface Airflow a localhost:8080"

---

## DIAPOSITIVE 35 : SCD - Dimensions a evolution lente (C17)

**Dire (30 secondes) :**
"C17 : les variations de dimensions selon les trois types de Kimball."

"Type 1 -- Ecrasement : utilise pour `dim_brand`. Si un nom de marque etait mal orthographie, on le corrige simplement. Pas d'historique necessaire pour les fautes de frappe."

"Type 2 -- Historisation : utilise pour `dim_product`. Quand la recette d'un produit change, on ferme l'ancien enregistrement avec une date de fin et on en insere un nouveau. L'historique complet est conserve."

"Type 3 -- Valeur precedente : utilise pour `dim_country`. On garde une colonne pour la valeur precedente -- un seul niveau d'historique."

"La detection des changements dans l'ETL utilise `IS DISTINCT FROM` pour determiner quel type de mise a jour appliquer."

---

## DIAPOSITIVE 36 : Systeme d'alertes (C16)

**Dire (20 secondes) :**
"Quand un DAG echoue : le callback Airflow dans `alerting.py` se declenche. Il fait trois choses simultanement : enregistre dans la table `activity_log`, envoie un email via MailHog, et pousse une metrique vers StatsD. StatsD alimente Prometheus, qui alimente Grafana. L'equipe ops voit les alertes sur le tableau de bord Grafana et dans sa boite mail."

---

## DIAPOSITIVE 37 : Tableau de bord SLA (C16)

**Dire (20 secondes) :**
"Quatre indicateurs SLA : taux de succes ETL superieur a 95 %, fraicheur des donnees inferieure a 24 heures, completion des sauvegardes a 100 %, et temps de reponse des requetes inferieur a 5 secondes."

"Les incidents sont priorises selon une matrice ITIL : P1 critique moins d'1 heure, P2 eleve moins de 4 heures, P3 moyen moins de 24 heures, P4 faible au prochain sprint. L'escalade va du redemarrage automatique a l'ingenieur puis a la revue d'architecture."

> DEMO : "Permettez-moi de vous montrer Grafana a localhost:3000 et MailHog a localhost:8025"

---

## DIAPOSITIVE 38 : Sauvegarde et maintenance (C16)

**Dire (20 secondes) :**
"Le script de sauvegarde `backup_database.py` supporte les modes complet et partiel. Les sauvegardes sont envoyees vers le bucket MinIO /backups avec un nettoyage automatique des anciennes sauvegardes. Il s'execute comme un DAG Airflow planifie."

"Nous avons aussi documente les procedures pour : ajouter une nouvelle source de donnees en 6 etapes, creer un nouvel acces en 3 etapes, augmenter le stockage, ajouter des vues datamart et augmenter la capacite de calcul. Tout est dans le chapitre 12 du rapport final."

---

## DIAPOSITIVE 39 : Architecture Medallion (C18)

**Dire (30 secondes) :**
"C18 : l'architecture du data lake. Nous utilisons le pattern medallion avec trois couches."

"Bronze : les donnees brutes telles quelles. JSON, Parquet, CSV. Retention de 90 jours."
"Silver : nettoyees et validees. Uniquement Parquet. Dedupliquees."
"Gold : agregats prets pour l'analytique. 4 jeux de donnees anonymises : nutrition_patterns avec les moyennes macro par Nutri-Score, popular_products avec les produits les plus consultes, brand_rankings avec les scores qualite des marques, et category_stats avec les statistiques nutritionnelles par categorie. Snapshots quotidiens."

"Les donnees passent de bronze a silver par le nettoyage, et de silver a gold par l'agregation."

"Cela repond aux trois V : Volume -- plus de 3 millions de produits dans la source, 798 000 importes et nettoyes avec PySpark. Variete -- JSON, Parquet, CSV. Velocite -- planifications quotidiennes et hebdomadaires."

---

## DIAPOSITIVE 40 : Volume, Variete, Velocite (C18)

**Dire (15 secondes) :**
"Pour etre explicite sur les trois V : le Volume est de plus de 3 millions de produits avec le format colonnaire Parquet pour des scans rapides. La Variete est de 4 formats -- JSON, Parquet, HTML, SQL. La Velocite est des extractions API quotidiennes, Parquet hebdomadaire, scraping mensuel, tout planifie en DAGs."

---

## DIAPOSITIVE 41 : Comparaison des catalogues (C18)

**Dire (30 secondes) :**
"Nous avons compare trois outils de catalogage. Apache Atlas : puissant mais lourd, necessite Java, surdimensionne pour notre echelle. DataHub : surcharge moderee, necessite sa propre infrastructure. Notre catalogue JSON personnalise : surcharge minimale, integration native MinIO, dimensionne pour ce projet."

"Nous avons choisi l'approche personnalisee car elle offre des capacites de recherche et de navigation via la page Streamlit sans ajouter d'infrastructure significative. Si le projet grandit, la migration vers DataHub serait l'etape naturelle."

---

## DIAPOSITIVE 42 : Navigateur du catalogue (C20)

**Dire (20 secondes) :**
"Le navigateur du catalogue est une page Streamlit. Vous pouvez rechercher des jeux de donnees par nom, format ou source. Naviguer par couche -- onglets bronze, silver, gold. Voir le schema avec les noms et types de colonnes. Voir la lignee des donnees -- d'ou vient chaque jeu de donnees. Verifier les metriques de qualite. Et consulter les informations de gouvernance et de conformite RGPD, y compris les groupes d'acces et les politiques de retention."

> DEMO : "Permettez-moi de montrer le catalogue. Je dois me connecter en tant qu'admin car le catalogue est restreint par role."

---

## DIAPOSITIVE 43 : Gouvernance des acces (C21)

**Dire (30 secondes) :**
"C21 : gouvernance des donnees avec controle d'acces par groupe."

"Trois groupes, appliques de maniere coherente sur les quatre systemes :"
"Role admin : acces complet a PostgreSQL, tous les buckets MinIO, tous les endpoints API et toutes les pages Streamlit."
"Role analyste : lecture des produits dans PostgreSQL, bucket gold dans MinIO, API analytics et tableaux de bord Product Analytics et Data Catalog dans Streamlit."
"Role dieteticien : lecture des produits et repas dans PostgreSQL, API dieteticien et tableau de bord utilisateur Streamlit."
"Role utilisateur : uniquement ses propres repas dans PostgreSQL, endpoints API de base et 6 pages Streamlit."

"Le principe est le moindre privilege : chaque role n'obtient que ce dont il a besoin. Et l'acces est par groupe, pas individuel, comme le recommande le RGPD."

---

## DIAPOSITIVE 44 : Stack de monitoring (C16, C20)

**Dire (15 secondes) :**
"Quatre exporteurs alimentent Prometheus : StatsD pour les metriques Airflow, cAdvisor pour les statistiques des conteneurs Docker, Node Exporter pour les metriques de l'hote et PostgreSQL Exporter pour les metriques de la base. Prometheus interroge les quatre et alimente les 6 tableaux de bord Grafana."

---

## DIAPOSITIVE 45 : 6 tableaux de bord Grafana

**Dire (15 secondes) :**
"Six tableaux de bord : vue d'ensemble Airflow pour les executions de DAGs, Airflow DAGs pour la performance par DAG, PostgreSQL pour la sante de la base, Docker System pour les ressources des conteneurs, MinIO pour le stockage objet, et SLA Compliance pour les quatre indicateurs de service."

---

## DIAPOSITIVE 46 : 21/21 Competences couvertes

**Dire (20 secondes) :**
"Les 21 competences des 4 blocs sont couvertes par ce seul projet integre. Bloc 1 -- piloter un projet data : C1 a C7. Bloc 2 -- collecte des donnees : C8 a C12. Bloc 3 -- entrepot : C13 a C17. Bloc 4 -- lac : C18 a C21."

"Un seul projet, 15 services Docker, conformite RGPD complete, les 7 evaluations."

---

## DIAPOSITIVE 47 : Retour d'experience

**Dire (30 secondes) :**
"Ce qui a bien fonctionne : Docker pour le deploiement en une commande. L'execution de l'entrepot et du lac en parallele. Airflow pour l'orchestration. Avoir fait du RGPD un moteur d'architecture des le premier jour, pas un ajout apres coup. Et traiter la documentation comme un livrable de premiere classe."

"Prochaines etapes : le streaming temps reel avec Kafka, Kubernetes pour l'orchestration en production, un pipeline ML pour les recommandations personnalisees, la migration vers DataHub pour le catalogue, et davantage de tests automatises."

---

## DIAPOSITIVE 48 : Plan de la demo en direct

**Dire (15 secondes) :**
"Voici la sequence de demonstration. Je vais suivre ces etapes dans l'ordre pendant la presentation."

> C'est votre checklist. Referez-vous-y au fur et a mesure des demos.

---

## DIAPOSITIVE 49 : Merci

**Dire :**
"Merci de votre attention. Le code est sur GitHub a Reetika12795/NutriTrack. Je suis prete pour vos questions."

---

# Conseils generaux

1. **Reliez toujours les fonctionnalites a Sophie.** "Nous avons construit cela parce que Sophie a besoin de..."
2. **Mentionnez le numero de competence** quand vous montrez quelque chose de pertinent : "C'est C8" ou "Cela couvre C16."
3. **Pendant les demos, commentez ce que vous faites.** "Je me connecte maintenant en tant que dieteticien pour montrer le controle d'acces par role."
4. **Si quelque chose echoue pendant la demo**, restez calme et dites : "Permettez-moi de vous montrer une alternative." Passez au point de demo suivant.
5. **Surveillez le temps.** Vous avez 60 minutes pour E1-E5 -- soit environ 90 secondes par diapositive.
6. **Pour le Q&A E6 (10 min) :** Le jury posera des questions sur la maintenance de l'entrepot. Soyez prete a expliquer : le flux d'alerte, les metriques SLA, les procedures de sauvegarde et comment ajouter une nouvelle source de donnees.
7. **Pour E7 (10 min) :** Concentrez-vous sur l'architecture medallion, la comparaison des outils de catalogue et la gouvernance des acces.
8. **Parlez lentement et clairement.** Il vaut mieux couvrir moins de diapositives bien que de toutes les survoler.
