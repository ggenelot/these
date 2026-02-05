# Introduction

Ma thèse cherche à modéliser les dommages liés au changement climatique, notamment ceux des cyclones aux Petites Antilles en associant des méthodes d'analyse spatiale et de prospective. Cette méthode devrait permettre de prendre en compte l'adaptation au changement climatique et la distribution spatiale des dommages. On construit un modèle régional en utilisant des données physiques et sociales spatialisées, puis on évalue les dommages causés par des cyclones synthétiques pour comparer différents scénarios d'aménagement. 

```{mermaid}
:caption: Cadre d'analyse du projet (contexte, problÃ©matique et mÃ©thodologie)
:name: fig-intro-cadre

graph TD
    contexte --> risque
    contexte --> prospective
    contexte --> IAM
    
    A1 --> A4
    A2 --> A4
    A3 --> A4
    prospective --> question
    risque --> question
    IAM --> question
    
    subgraph contexte[Contexte]
    	C1[Cyclone]
        C2[Martinique]
        C3[Changement climatique] --> C5[Triptyque mitigation / adaptation / impacts]
        C4[Dommages] --> C5
        
    
    end
    
    subgraph risque["Géographie du risque"]
        A1[Méthodes quali]
        A2[Analyse spatiale]
        A3[Cadre conceptuel]
        A4{Futur  ?}
    end
    
    subgraph prospective["Rapports et assurances"]
    	P1[Politique publique] --> P3{Outre-mer ?}
        P2[Maille fine] --> P4{Monétaire}
    end
    
    subgraph IAM[Modélisation prospective]
    	I1[Coût social du carbone] --> I4{Global}
        I2[Fonctions de dommage] --> I5{Monétaire}
        I2 --> I6{Adaptation ?}
    end
    
    subgraph question[Problématique]
    
    	Q0[Comment les politiques d'adaptation d'aujourd'hui permettent de limiter les impacts demain  ?] --> ope
        Q0 --> epistemo
    
    	subgraph ope[Questions opérationnelles]
    	Q1[Quelles sont les politiques d'adaptation possibles ?]
        Q2[Quelle est la distribution spatiale des impacts ?]
        Q3[Peut-on modifier la distribution spatiale des impacts ?]
        end
        
        subgraph epistemo[Questions épistémiques]
        	Q4[Association de données quali ?]
            Q5[Dépasser la monétarisation ?]
            Q6[Evenement soudain et localisé ? ]
        
        end
    end
    
    question --> methodo
    
    subgraph methodo[Méthodologie]
    	M1[Données]
        M2[Modélisation]
        M3[Simulation]
        M4[Evaluation]
        M5(Itération)
        M6{Entretiens} --> M2
       
        M7{Revue de littérature} --> M2
        M8{Sources} --> M1
        
        	M1 --> M2 --> M3 --> M4--> M1
		
    
    end

    
    methodo  --> finalité
    
    
    subgraph finalité[Finalité]
    
    	Ac0[Accompagner la décision publique] --> Ac1
        Ac0 --> Ac2
        Ac0 --> Ac
    	Ac1(Collectivité territoriale) --> F1[Aménagement du territoire]
        Ac2(Etat) --> F2[Gestion du risque]
        Ac(Diplomatie climatique) --> F3[Transition juste]
    
    end
    
    
    
    
style IAM fill:#a28ae5, color:#fff;
style prospective fill:#a28ae5, color:#fff;
style risque fill:#a28ae5, color:#fff;

style question fill:#FF8658, color:#fff;
style ope fill:#CC5948, color:#fff;
style epistemo fill:#CC5948, color:#fff;


style methodo fill: #B4CF66, color:#fff;

style finalité fill: #FFEC5C, color:#fff;





```

## Présentation générale du projet

La modélisation prospective imagine les futurs possibles pour éclairer les choix actuels qui permettent de les construire. Le changement climatique a et aura de nombreux effets adverses, appelés dommages ou impacts. Leur fréquence et leur intensité dépendent de mesures et de politiques actuelles. Un des rôles de la modélisation est ainsi d'informer les décideurs pour prendre des mesures adéquates.

On peut distinguer trois types de mesures permettant de limiter les dommages. 

- D'abord, l'atténuation, qui cherche à limiter le changement climatique.
- Ensuite, l'adaptation, qui cherche à réduire les effets de phénomènes adverses quand ils arrivent.
- Enfin, la compensation, qui vise à prendre en compte les impacts qui n'ont pas été limités par l'atténuation ou l'adaptation.

L'objectif de cette thèse est de proposer des outils pour mieux comprendre les effets de politiques d'adaptation sur les dommages, dans le cadre de cyclones tropicaux dans les Caraïbes.

## Littératures existantes

Ce projet de recherche s'inscrit à l'intersection de différents types de littérature : la littérature grise autour du risque, la géographie du risque et la modélisation prospective. 


### Littérature institutionnelle

D'abord, une littérature grise importante existe autour des impacts du changement climatique. 

D'une part, des rapports publics mettent en avant le besoin de développer une approche spécifique aux territoires ultramarins. Un rapport de l'observatoire national sur les effets du réchauffement climatique pointe la nécessité d'évaluer le coût des impacts du changement climatique et les limites de la modélisation climatique dans les politiques d'adaptation {cite:p}`onercOutremerFaceAu2012`. Par ailleurs, deux autres rapports, sur l'adaptation et sur les littoraux, pointent la nécessité de prendre en compte les dommages et ne prennent pas en compte de manière spécifique les territoires ultramarins {cite:p}`onercLadaptationFranceAu2012,onercLittoralDansContexte2015`.  
D'autre part, les assurances estiment régulièrement les coûts du changement climatique. On peut notamment citer une étude de la Caisse Centrale de Réassurance qui a simulé l'impact d'un cyclone de type Irma sur la Guadeloupe, pour estimer les pertes économiques {cite:p}`nsandaCatastrophesNaturellesFrance2024`. 



###  Géographie du risque

La géographie du risque conceptualise les risques naturels dans une approche intégrée éléments sociaux - éléments naturels. 
D'abord, elle porte un travail important de conceptualisation du risque et de ses composantes. On peut notamment citer des définitions du risque {cite:p}`kermischVersDefinitionMultidimensionnelle2012,dercoleEnjeuxAuCoeur2003`, des travaux sur des concepts annexes tels que la résilience {cite:p}`manyenaConceptResilienceRevisited2006,magalireghezza-zittWhatResilienceNot2012,barrocaVulnerabiliteResilienceMutation2013`, la vulnérabilité {cite:p}`robertdercoleVulnerabilitesSocietesEspaces1994`, la catastrophe {cite:p}`clavandierRetourCatastropheScene2015`. 
Ensuite, la géographie quantitative développe des outils permettant de prendre en compte des phénomènes quantitatifs dans leur spatialité, notamment à l'aide de Systèmes d'Information Géographique {cite:p}`feuilletManuelGeographieQuantitative2019,aschan-leygonieSystemesDinformationGeographique2023`.
Enfin, des monographies décrivent les dynamiques et les effets des risques, notamment dans le cadre des cyclones tropicaux aux petites Antilles. Un projet de RETEX scientifique du cyclone Irma (2017), mené conjointement par 10 chercheurs permet de mieux comprendre les impacts et les capacités de relèvement de différentes petites îles (Saint-Martin, Saint-Barthélémy), {cite:p}`defossezCapacitesRelevementDun2021,duvatSystemeRisqueSaintMartin2008`. 

Ce corpus est essentiel pour décrire précisément les interactions entre les éléments physiques des cyclones tropicaux et la dimension sociétale et humaine de leurs impacts. Les concepts et les monographies sont une mine d'or pour comprendre ces phénomènes, et notamment leur dimension spatiale. Cependant, ces travaux sont inscrits dans le temps, à un instant $t$. Il serait intéressant de pouvoir mobiliser leurs apports dans une approche de long terme. \\

### Prospective et modélisation

La modélisation des interactions entre le changement climatique et les sociétés permet de comprendre leurs évolutions au temps long. En particulier, les modèles intégrés éclairent les politiques publiques en évaluant les effets attendus de mesures. 

La question du coût de l'inaction face au changement climatique est un thème récurrent de l'économie de l'environnement. Une approche courante est de calculer le coût social du carbone, c'est-à-dire le coût en intégrant les externalités négatives , pour évaluer l'intérêt de politiques de mitigation dans une perspective d'analyse coût-bénéfice {cite:p}`nordhausSlowNotSlow1991,nordhausRevisitingSocialCost2017,sternEconomicsClimateChange2007,anthoffUncertaintySocialCost2013`.  Ils ont deux limitations majeures. D'une part, ils évaluent les dommages de manière très agrégée et globale, ce qui limite leur représentation de politiques ciblée, notamment d'adaptation. D'autre part, l'évaluation des dommages est sur une base monétaire, ce qui exclut ou limite la prise en compte d'effets extra-monétaires. 

Plus récemment, des modèles plus précis ciblent un phénomène physique particulier. Dans le modèle IMAGE, les dommages des inondations sont pris en compte par l'utilisation de données spatialisées {cite:p}`vanvuurenIMAGEStrategyDocument,winsemiusFrameworkGlobalRiver2013`. Cette approche permet une plus grande granularité, même si les dommages sont toujours monétarisés. @mendelsohnImpactClimateChange2012 s'intéresse aux effets du changement climatique sur les dommages issus des cyclones tropicaux. Deux limitations sont mentionnées dans l'article : le manque de décomposition par cause (vent, précipitation, marée cyclonique) et l'absence de modélisation de politiques d'adaptation. 

## Questions de recherche

La question centrale de cette thèse est *quelles mesures actuelles permettent de limiter les impacts des cyclones dans le futur ?*

Elle se décompose en deux grandes catégories de questions. D'une part, des questions opérationnelles, qui justifient l'usage d'un modèle et de techniques de prospective. Celles-ci répondent directement à la question centrale : 

- Quelle est la distribution spatiale des dommages ? 
- Peut-on, par des mesures d'aménagement, modifier la distribution de ces impacts ? 
- Quels sont les choix d'aménagement disponibles ? 



D'autre part, des questions épistémiques sur l'intérêt de ce type de modélisation. On évalue là la pertinence du couplage modèle de prospective - analyse spatiale pour répondre à des questions d'aménagement de long terme. \\ 

- Cette technique permet-elle d'évaluer les dommages de manière plus globale, notamment en prenant en compte des dommages non monétaires (notamment naturels) ? 
- Arrive-t-on à prendre en compte l'effet de phénomènes extrêmes, et notamment localisés dans le temps et dans l'espace ? 
- Peut-on rendre compte de dommages non monétaires ? 
- Comment associer des données qualitatives et quantitatives ? 


## Méthodologie

On simule l'effet du passage d'un cyclone sur une île des petites Antilles. On peut décomposer cette approche en quatre phases principales. D'abord, on crée une représentation de l'île avec des données choisies, avec un maillage dense. On définit des fonctions de dommage, c'est-à-dire l'effet du passage du cyclone et de ses composantes (vent, vague, précipitation) sur les données choisies (destruction de l'habitat, changement d'usage). On réalise des simulations du passage de cyclones à l'aide de cyclones synthétiques, et on évalue le niveau de dommage. On peut renouveler la simulation en faisant varier la représentation initiale de l'île, c'est-à-dire en faisant des choix d'aménagement différents. Une version simplifiée du modèle, tel qu'il est envisagé aujourd'hui, est disponible en figure {numref}`fig-modele`.

### Choix des données et représentations

On utilise des données spatialisées variées pour représenter les enjeux du territoire choisi. 

Quatre grands types de données sont associés : topographie (élévation , pente, bathymétrie {cite:p}`institutgeographiquenationalBDTOPO2025`) ; cyclones synthétiques (précipitation, vents, marée cyclonique {cite:p}`bloemendaalSTORMIBTrACSPresent2022,bloemendaalSTORMClimateChange2023`); aménagement (usages des sols {cite:p}`zanagaESAWorldCover102022`, routes, bâtis {cite:p}`OSM`); et socio-économiques (densité de population, taux de pauvreté {cite:p}`inseeFilosofi2021`).

Le niveau de granularité n'est pas encore défini ; il devrait être de l'ordre de la dizaine de mètres ou de la centaine de mètres. Pour comparaison, les données de Filosofi sont disponibles à 200m; les données de couverture du sol à 10m; de topographie à 30m. 



### Modélisation des fonctions de dommage

On modélise les fonctions de dommage, c'est-à-dire qu'on définit la relation entre le passage d'un cyclone et les autres variables. En d'autres termes, on écrit une fonction mathématique qui donne les impacts à partir du cyclone. Cette représentation se fait de deux manières. D'une part, on se base sur la revue de littérature pour mobiliser des fonctions de dommage existantes et les adapter aux données spatiales. D'autre part, des entretiens permettent d'inclure des données qualitatives dans les fonctions de dommage.


### Simulation et itération

On simule le passage d'un cyclone et on observe les évolutions de nos variables. On recommence les opérations 1 à 3 avec différentes options d'aménagement pour les comparer.



```mermaid
:caption: Représentation simplifiée du modèle envisagé
:name: fig-modele

graph TD;

S1{STORM} -->|cyclones synthétiques| M
S2{SSP ? } -->|evolution économique| M
S3{INSEE} -->|densité, pauvreté| S
S4{OSM} -->|route, usage des sols, bati| S
S5{IGN} -->|élévation, pente| T
S6{SHOM} -->|coraux, bathy| T
S7{Entretiens}--> |besoins, vulnérabilité, scénarios de dév| A


subgraph input[input]
M[Climato]
S[socio-éco]
T[Topographie]
A[Aménagement]
end

M --> |intensité| C
T --> |augmente| Al
A --> |atténue| Al
S --> |distribue| En
A --> |augmente| En 

subgraph modele[Représentation]

C[Cyclone] 
Al[Aléa]
C --> Al 

En[Enjeu]

Ri[Risque]
Al -->|influence| Ri
En -->|influence| Ri

end

Ri --> Ca

Al --> Ca
En --> Ca

subgraph output[output]

Ca[Carte]
end



```


## Références  

```{bibliography}
