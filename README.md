# Etude de marché par sentiment analysis
![img](https://external-content.duckduckgo.com/iu/?u=http%3A%2F%2Ffondation-valentin-ribet.org%2Fwp-content%2Fuploads%2F2016%2F12%2Flogo-simplon.gif&f=1&nofb=1.png)
# Subject FR
## Contexte du projet
Vous travaillez pour une entreprise qui propose un service d'obtention d'études de marchés à ses utilisateurs. Aux nombreux services existant, il vous est demandé d'ajouter une API proposant un etat des lieux des sentiments qu'ont les prospects de vos utilisateurs (via Trustpilot, Google,...), envers les entreprises concurrentes.

Cette API se branchera à un nouveau tableau de bord développé en parallèle par le pôle web, qui sera proposé à vos clients. L'API permettra a minima de** récupérer, pour un domaine et une localité donnée, un json proposant les données nécessaires à l'établissement d'un tableau de bord efficace.**

Pour cela, il vous faudra proposer des réflexions sur la présentation des données, et des résultats obtenus par votre modèle et plus largement votre API.
Renvoi des avis complets ? Renvoi de l'ensemble des mots significatifs pour un établissement et un sentiment donné ? Renvoi de chaque sentiment, d'une proportion ? Différentiation des avis globaux et et des avis récents pour observer les tendances ? C'est à vous de mener la réflexion en amont de la production de l'API. Vous pouvez dans ces réflexions, solliciter la hiérarchie.
# How to use
## Download the Project
```bash
git clone https://github.com/tjohanne42/api_nlp_trustpilot.git
cd api_nlp_trustpilot
pip install requirements.txt
python main.py starts the API  
```
## Run in your browser
## https://your_address_ip:8000/docs
## To access the documentation. 
You can run https://your_address_ip:8000/redoc aswell.
# Example of usage
## After starting API you can start:
## dashboard/index.html
## Our client web example
You can obtain dashboard with wordclouds, sentiment analysis:
![img](images_readme/dashboard.png)
You can obtain more informations on specific company:
![img](images_readme/companies.png)
## This API use CamemBert, a french model of NLP
## We used transfer learning on this model with our dataset
## Data are based on TrustPilot
# Contibutors:
## Jean-Marie, David, Théo