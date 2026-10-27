# Journal des vérifications du rendu commun

## Sources et préservation

- Lecture intégrale de la mission, des 9 pages du sujet, des 32 cellules du
  starter, du GUIDE et des sources indiquées ; audit du code et des sorties
  des quatre contributions. L'inventaire CSV distingue les fichiers propres.
- Inventaire distant initial : quatre branches individuelles, SHA repris dans
  l'audit. Création locale de `final` depuis Elias, sans modifier les autres
  références. La mission initialement non suivie est conservée telle quelle.
- Les notebooks individuels sont copiés depuis leurs blobs Git ; les historiques
  scientifiques d'Elias sont copiés dans `rendu_final/historique`. Aucun fichier
  de `artifacts/competition` ou `artifacts/full_project` n'est réécrit.
- Les SHA-256 des données sont dans `provenance_donnees.json`. Comparaison
  numérique exacte des 61 années train, des 25 années test, de leurs CO₂ et du
  préfixe journalier avec les CSV complets. Calendrier réel complet : 31 412 jours.

## Exécution des expériences

- Trois validations et deux cibles, avec 10 000 tirages par année. Bayes, GEV,
  quantiles, références, C0, D1/D2/D3/D4, H0 et H1 réellement évalués.
- 78 checkpoints neuronaux compatibles réutilisés après vérification des
  empreintes des entrées de train et de validation ; 12 réseaux complémentaires
  entraînés sur les données complètes, sans remplacer les historiques.
- La sélection est écrite avant ouverture de la vérité par le nouveau runner.
  Aucun ajustement ne reçoit cette vérité. Le test ayant déjà été consulté
  auparavant, les nouveaux résultats restent déclarés exploratoires.
- Le kit original est réellement appelé et retourne un couple admissible.
  Le CRPS local retrouve exactement sa formule. Les contrôles portent sur les
  tirages bruts. Les échecs de méthodes concurrentes sont conservés.
- Les 75 années et les trois scénarios sont simulés pour les deux variables,
  avec paramètres communs par trajectoire et innovations annuelles renouvelées.
  Les tableaux contiennent aussi les sensibilités, coûts, couvertures et largeurs.

## Vérification du notebook

- Environnement virtuel Python neuf créé sans `--system-site-packages`, avec
  PyTorch CPU et les dépendances explicites. Le noyau utilise cet interpréteur
  via un kernelspec temporaire ; aucun kernel utilisateur n'est modifié.
- Seul le notebook est copié dans un dossier temporaire vide ; toutes ses
  sorties sont effacées avant `NotebookClient.execute`, erreurs interdites.
  Les ressources sont extraites du notebook et vérifiées, sans accès au dépôt.
- Les 23 cellules de code s'exécutent. Elles recalculent les vagues, un petit
  entraînement, les tirages du modèle retenu, le kit et les projections.
  Les scores sont identiques aux scores de référence dans cet environnement.
- Les 7 figures du notebook sont inspectées : axes et unités, seuils, légendes,
  couleurs, distributions et bandes. Les tableaux sont rapprochés des calculs
  et des équations. La matrice vérifie 16 exigences et l'existence de toutes
  les cellules pointées.
- 43 tests et 4 sous-tests passent, dont les contrôles scientifiques nouveaux :
  CRPS par paires, pénalisation des fausses alertes, extrémités exactes du mélange,
  posterior bayésien tronqué comparé à sa marginale Student et interpolation
  monotone des quantiles.

## Obstacles effectivement rencontrés

- Les anciens notebooks dépendent de dossiers ignorés par Git. Ils ne suffisent
  pas à une reproduction isolée : un paquet compact vérifié est désormais
  embarqué dans le notebook.
- Les jeux de données et chemins personnels sont remplacés dans le rendu par
  des chemins relatifs et une extraction temporaire. Les anciens manifestes
  gardent leurs chemins comme trace historique, sans être requis pour exécuter.
- Certaines sorties texte Windows utilisaient CP1252 et affichaient mal les
  accents ; les scripts et journaux nouveaux sont enregistrés en UTF-8.
- L'accès HTML direct à la prépublication Park a échoué dans l'outil web ; la
  notice arXiv primaire a été retrouvée par recherche, et les formules ont été
  confrontées au code local et à l'audit historique. Aucun résultat sur Brest
  n'est attribué à cet article.

Les preuves JSON d'exécution, versions, durées et empreintes sont conservées
dans `reports/final/`. La vérification finale du clone distant complète ce
journal après le push sans force.

## Vérification du paquet Git

Un clone local isolé a été comparé octet par octet aux 251 ressources du
manifeste. Une conversion automatique CRLF de `requirements-final.txt` a été
repérée puis corrigée par `.gitattributes`. Les données et états archivés
conservent leurs octets originaux ; les sources Python et les dépendances
utilisent LF. Les espaces des SVG et archives générés ne sont pas traités
comme des erreurs de code. Le contrôle `git diff --check` du code passe.

## Réentraînement intégral et dernière anomalie conservée

Le notebook en mode réentraînement termine ses 23 cellules en 2 472 s environ
(41,2 min), avec 90 réseaux réappris depuis zéro. Leurs poids sont tous
identiques aux états remis. Les tables de validation, test, projections,
sensibilités et probabilités comparées ne présentent aucune différence numérique.
La sélection et les scores du kit sont exactement retrouvés.

Le contrôle étendu aux 75 années après réajustement complet trouve un tirage
GEV SSP5-8.5 à 50,901 °C, parmi 750 000 tirages de cette méthode/scénario.
Il est conservé et présenté. La GEV historique avait passé les contrôles ;
cette réussite ne garantissait pas le modèle réajusté. Les six ensembles
D3/D1 retenus sont conformes aux bornes sur les tirages vérifiés.

Le tableau `reentrainement_90_reseaux.csv` trace les entraînements et
`controle_toutes_projections_reentrainees.csv` conserve les extrêmes mesurés.

Le paquet final contient 252 ressources embarquées : la base expérimentale
initiale et le diagnostic des projections complètes. La dernière exécution
propre du notebook maître, incluant cet échec, termine en 19 s environ sur
CPU. Les 16 exigences de la matrice sont contrôlées.
