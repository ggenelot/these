---
title: Des modèles pour la mitigation aux modèles pour l'adaptation
parts:
  abstract: |
    Les modèles de prospective, notamment ceux qui informent les rapports du GIEC, sont issus de la prospective énergétique. Ils sont orientés vers l'évaluation de politiques de mix énergétiques, et répondent à des questions de transition énergétique. Cependant, ils peinent à prendre en compte des données qui ne sont pas quantifiées, et sont souvent très abstraits spatialement. Ces deux caractéristiques rendent difficile l'évaluation de politiques d'adapation, et posent la question de leur transformation pour répondre à des questions contemporaines. Nous développons ici l'idée que de nouveaux modèles de prospective sont requis pour permettre de répondre à des questions d'adaptation et de justice climatique.
  problematic: |
    En quoi l'évolution de la gouvernance climatique appelle-t-elle à une évolution des techniques de modélisation prospective ?
  literature_note: |
    On s'appuie sur :
  partial_conclusion: |
    Pour bien aménager le territoire pour l'adaptation, les modèles de prospective doivent évoluer pour prendre en compte la spatialité et l'aspect qualitatif de phénomènes climatiques.
exports:
- format: pdf
  template: ./templates/these-chapitre
  output: exports/prospective.pdf
---

Grandes idées: [changement bien visible pour tester] => devrait aller sur test2 dernier changement avant de tester le plugin sur mon repo en prod / test avec le choix du dossier / test sans la branche
- la prospective vise à éclairer la politique publique
- une forme de politique publique qui a particulièrement besoin de prospective est la plannification, qui a besoin d'une vision systémique et à long-terme
- la plupart des modèles de prospective actuels viennent de plannification énergétique issus des chocs pétroliers
- ce sont donc des modèles de prospective essentiellement énergétiques
- ils sont capables de prendre en compte de nombreuses variables quantitatives
- de ce fait, ils orientent vers des solutions quantifiées, par exemple des taxes ou des marchés carbones
- de ce fait, ils orientent surtout sur des solutions sur le carbone (qui est quantifiable et quantifié) et sur des solutions globales
- de ce fait, ce sont des modèles très utiles pour la mitigation / la transition énergétique
- en revanche, ils ne permettent pas de correctement représenter des données qui ne sont pas quantifiées;
- en revanche, ils ont du mal à prendre en compte des données spatiales
- or, un des gros défis du changement climatique est l'adaptation (on fait l'hypothèse que la mitigation seule n'est pas suffisante)
- or, l'adaptation est forcément locale
- or, l'adaptation nécessite de faire des choix de vie, de société, des choix politiques
- pour qu'un modèle permette d'accompagner l'adpatation, il doit donc prendre en compte en entrée des composantes politiques et des données spatiales
- ce qui nous amène à la question : à quelle questions un modèle pour l'adaptation doit-il être en mesure de répondre ?
- ce qui nous amène à la question : quelles sont les limitations actuelles des modèles pour répondre à ces questions
- ce qui nous amène à la question : à quoi ressemblerait un modèle qui permettrait de répondre à ces questions ?

Trame du raisonnement :
- La gouvernance climatique change de phase (I.1). Orientée initialement vers la mitigation, elle doit aujourd'hui répondre à des questions d'adaptation (I.2). Pour rester pertinents, les modèles de prospective doivent permettre de répondre à ces nouvelles questions(I.3). Or, celles-ci posent des contraintes techniques difficiles : prise en compte de données qualitatives et spatiales (II). De nouvelles techniques et approches permettraient cependant de répondre à ces contraintes (III).

mots-clés permettant de distinguer la biblio : spatial, socio-ecosystème, coût social du carbone, monétarisation

Proposition de plan :

## Coévolution de la recherche scientifique et de la gouvernance climatique

  - => il y a une double évolution de la gouvernance et de la recherche, qui s'alimentent mutuellement
    - la gouvernance climatique (comme définie par Aykut) a évolué depuis 40 ans : logique monétaire / quantitative / globale / marché (taxes carbones, etc), à une logique local / qualitatif / adaptation
    - La production scientifique a évolué aussi : elle est passée d'une logique de compréhension / mitigation (donc un évitement du phénomène) à une logique de (p)réparation / adaptation (donc une acceptation du problème)
    - cette coévolution illustre et questionne les liens entre science et politique
      - une influence sur la recherche par le système international (GIEC, etc) (Cointe, aykut)
      - les effets du cadrage de la recherche sur la politique climatique (Fressoz, notion de cadrage)

## Les contraintes structurelles des modèles numériques d'optimisation

  - => les limites historiques des simulations numériques type DICE, World3, etc.
    - le monétaire et la commensurabilité : la nécessité d'avoir une unité de compte dans un modèle d'optimisation
      - une simulation numérique / un modèle d'optimisation nécessite une unité de compte commune pour pouvoir comparer des choses différentes
      - cette généralisation réduit la précision de la compréhension, notamment sur des phénomènes qui ne sont pas directement monétaires
      - reproduction nécessaire des inégalités déjà existante : donc un outil pas adaptaté pour des questions de justice climatique
    - un manque de finesse spatiale
      - les modèles intégrés (pas les modèles de climat) sont historiquement peu spatially-aware (notamment ceux dans la tradition de DICE)
      - ça limite la prise en compte de réalités locales / de spécificités territoriales (pré-introduction au chapitre aménagement)
      - pourtant, la spatialité est prise en compte dans certaines approches (données spatiales quantitatives, liens avec les GCM, géoprospective)
      - et en même temps, la question de l'abstraction : à quoi bon avoir des modèles trop précis (mythe de l'empereur et du cartographe)
    - la question de la justice et des normes
      - une recherche de la neutralité, inscrite dans la pensée scientifique classique
      - pourtant, l'impossibilité d'être neutre quand on fait de la modélisation
      - effets de cette non-neutralité et marge de manoeuvre

## Outils possibles et nécessaire pour la formation de la connaissance scientifique de demain

///////////////////////////  Remarques
- J'aime bien l'idée de changement d'objet, de questionnement scientifique et de cadre politique (en fait plutot objet, échelle et régime de preuve) :
  - objet :
    - climat comme objet purement physique, un peu partout, gazeux (littéralement) => adaptation, espace, territoire : objets beaucoup plus concrets, matériels (morphologie urbaine), politiques
    - instruments financiers à aménagement de l'espace
  - échelle : échelle globale (et abstraite):
    - échelle de la perception : globale et abstraite à échelle locale et perceptible
      - une idée intéressante là : la perception du changement climatique : avant il n'y avait pas de perception, c'était quelque chose d'imperceptible, alors que maintenant c'est quelque chose de très sensible (chaleur, catastrophes, odeur des sargasses)
    - échelle du cadrage du problème
      - un prblème global à des solutions localisées
      - un problème collectif à un problème spécifiques à certaines personnes, injuste
  - régime de preuve:
    - preuve numériques, quantitative

/
