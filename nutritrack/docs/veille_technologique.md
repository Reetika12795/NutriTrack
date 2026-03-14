# Bulletin de Veille Technologique - NutriTrack

**Projet**: NutriTrack - Plateforme de suivi nutritionnel
**Periode**: Semaine du 10 mars 2026
**Redacteur**: Equipe Data Engineering
**Frequence**: Hebdomadaire (1h minimum / semaine)

---

## 1. Theme de veille : Apache Superset 6.0 - BI et visualisation analytique

### 1.1 Contexte du choix

Apache Superset a ete retenu comme outil BI pour le projet NutriTrack (evaluation E5, competence C14) afin de fournir aux equipes metier (nutritionnistes, analystes) un acces autonome aux donnees de l'entrepot. Ce bulletin couvre les evolutions majeures de la version 6.0 deployee dans le projet.

### 1.2 Nouveautes Superset 6.0.1

| Fonctionnalite | Impact NutriTrack | Statut |
|---|---|---|
| **Types de visualisation renommes** (e.g. `dist_bar` -> `echarts_bar`, `pie` -> `echarts_pie`) | Migration obligatoire des dashboards existants | Integre |
| **Filtres natifs cross-dashboard** (`DASHBOARD_CROSS_FILTERS`) | Permet le filtrage interactif entre graphiques Nutri-Score et tendances nutritionnelles | Active |
| **Template processing** (`ENABLE_TEMPLATE_PROCESSING`) | Requetes SQL dynamiques avec variables Jinja dans les datasets | Active |
| **Cache Redis integre** | Temps de reponse des dashboards ameliore (TTL 300s configure) | Deploye |

### 1.3 Decision technique prise

Les anciens noms de types de visualisation (`dist_bar`, `pie`, `line`) ne sont plus reconnus dans Superset 6.x. Le script `superset/bootstrap_dashboards.py` a ete mis a jour pour utiliser exclusivement les types ECharts (`echarts_bar`, `echarts_pie`, `echarts_timeseries_line`). Cette migration a ete validee sur les 4 dashboards NutriTrack.

### 1.4 Sources consultees

| Source | Fiabilite | URL/Reference |
|---|---|---|
| Apache Superset Release Notes | Officielle (ASF) | github.com/apache/superset/releases |
| Superset Documentation | Officielle | superset.apache.org/docs |
| Superset GitHub Issues | Communautaire (verifiee) | Tickets #28xxx series sur la migration ECharts |

---

## 2. Veille reglementaire : RGPD et donnees nutritionnelles

### 2.1 Point de vigilance

Le Comite Europeen de la Protection des Donnees (CEPD) a publie des lignes directrices actualisees sur le traitement des donnees de sante et de bien-etre dans les applications mobiles (Guidelines 01/2026). Les donnees de suivi alimentaire (repas, apports caloriques) sont qualifiees de **donnees sensibles** lorsqu'elles permettent de deduire l'etat de sante d'un individu.

### 2.2 Impact sur NutriTrack

| Mesure existante | Conformite |
|---|---|
| Pseudonymisation SHA256 des identifiants utilisateur dans l'entrepot | Conforme |
| Registre RGPD (`rgpd_data_registry`) avec bases legales et durees de conservation | Conforme |
| Suppression automatique des donnees de repas > 2 ans (`rgpd_cleanup_expired_data()`) | Conforme |
| Consentement explicite a l'inscription (champ `consent_date` obligatoire) | Conforme |

### 2.3 Action recommandee

Aucune action corrective immediate requise. Maintenir la veille sur les publications du CEPD et de la CNIL pour anticiper d'eventuelles evolutions des exigences de consentement.

---

## 3. Veille outil : Apache Airflow 2.8 - Orchestration ETL

### 3.1 Evolutions pertinentes

- **Object Storage backend** : Airflow 2.8 introduit un support natif pour les backends de stockage objet (S3, GCS, Azure Blob). NutriTrack utilise deja MinIO comme data lake ; cette fonctionnalite pourrait simplifier les connexions dans les DAGs futurs.
- **Listener hooks ameliores** : Les hooks `on_task_instance_failed` et `on_task_instance_success` permettent des callbacks personnalises, utile pour enrichir le systeme d'alertes (C16).

### 3.2 Sources consultees

| Source | Fiabilite |
|---|---|
| Apache Airflow Changelog (apache/airflow) | Officielle (ASF) |
| Astronomer Blog | Industrie (verifiee) |

---

## 4. Synthese et actions

| Priorite | Action | Echeance | Responsable |
|---|---|---|---|
| Haute | Valider la compatibilite des dashboards Superset apres mise a jour 6.0.1 | Fait | Data Engineer |
| Moyenne | Surveiller les publications CEPD/CNIL sur les donnees de bien-etre | Continue | DPO / Data Engineer |
| Basse | Evaluer l'Object Storage backend Airflow 2.8 pour simplifier les DAGs MinIO | Sprint suivant | Data Engineer |

---

*Ce bulletin est produit dans le cadre de la veille technologique et reglementaire (competence C4) du projet NutriTrack. Frequence : hebdomadaire, duree minimale : 1 heure par semaine. Les sources sont evaluees selon les criteres de fiabilite suivants : officielle (editeur/organisme), communautaire verifiee (peer-reviewed, >1000 contributeurs), industrie (verifiee par experience).*
