import time
import asyncio
from http import HTTPStatus
from typing import Dict, List
from uuid import UUID, uuid4
import uvicorn # A installer 'Serveur uvicorn'
from fastapi import Body, FastAPI, HTTPException, BackgroundTasks
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic.schema import schema
from fastapi.encoders import jsonable_encoder
import pandas as pd
from functools import partial
from difflib import SequenceMatcher
import re  ### regular expressions
import numpy as np

from utils import remove_accents


from progress_task import *

#---------- LOADING AND CLEANING CSV -------------
# On charge les compagnies déjà scrappées pour gagner du temps
df_companies = pd.read_csv('companies.csv', sep=';', dtype={'name': str,
                                                            'link': str,
                                                            'stars': np.float32,
                                                            'review_count': np.float32,
                                                            'category': str,
                                                            'location': str,
                                                            'logo': str,
                                                            'url': str,
                                                            'phone': str,
                                                            'mail': str})

# On remplace les accents par des lettres standards pour faciliter la recherche
df_companies_name = df_companies['name'].apply(remove_accents)

# On supprime les caractères spéciaux et on passe en minuscule
df_companies_name = df_companies_name.str.replace('[^A-Za-z0-9 ]+', '', regex=True).str.lower()

# Nettoyage des floats
df_companies['stars'].replace(np.nan, 0, inplace=True)
df_companies['review_count'].replace(np.nan, 0, inplace=True)
df_companies['stars_average'].replace(np.nan, 0, inplace=True)

df_companies['link'].replace(np.nan, "Inconnu", inplace=True)
df_companies['location'].replace(np.nan, "Inconnu", inplace=True)
df_companies['logo'].replace(np.nan, "Inconnu", inplace=True)
df_companies['url'].replace(np.nan, "Inconnu", inplace=True)
df_companies['phone'].replace(np.nan, "Inconnu", inplace=True)
df_companies['mail'].replace(np.nan, "Inconnu", inplace=True)

# On charge les catégories déjà scrappées pour gagner du temps
df_categories = pd.read_csv('categories.csv', sep=';', dtype={'name': str, 'link': str, 'level': str})

# On remplace les accents par des lettres standards pour faciliter la recherche selon l'écriture
df_categories_name = df_categories['name'].apply(remove_accents)

# On supprime les caractères spéciaux et on passe en minuscule
df_categories_name = df_categories_name.str.replace('[^A-Za-z0-9 ]+', '', regex=True).str.lower()

# On convertit le nom de la catégorie en sa version explicite
df_companies['category'] = df_companies['category'].map(df_categories.set_index('link')['name'])

#---------- SAVE CSV CLEANED -------------
# df_companies['name_clean'] = df_companies_name
# df_categories['name_clean'] = df_categories_name

# df_companies.to_csv('companies_cleaned.csv', sep=';')
# df_categories.to_csv('categories_cleaned.csv', sep=';')

#---------- LOADING CSV CLEANED -------------
# df_companies = pd.read_csv('companies_cleaned.csv', sep=';', dtype={'name': str,
#                                                             'name_clean': str,
#                                                             'link': str,
#                                                             'stars': np.float32,
#                                                             'review_count': np.float32,
#                                                             'category': str,
#                                                             'location': str,
#                                                             'logo': str,
#                                                             'url': str,
#                                                             'phone': str,
#                                                             'mail': str})
# df_categories = pd.read_csv('categories_cleaned.csv', sep=';', dtype={'name': str, 'name_clean': str, 'link': str, 'level': str})

# df_companies_name = df_companies['name_clean']
# df_categories_name = df_categories['name_clean']

#--------------------------------

list_companies = str(df_companies['link'].values.tolist())
list_categories = str(df_categories['link'].values.tolist())

#---------- INIT NLP -------------


#---------- TEST NLP -------------
# json = get_json_from_category_link(df_categories["link"][0], max_companies=10, max_reviews=10)
# print("\n", "json".center(6, " ").center(100, "-"), "\n")
# print(json)


#---------- CONFIG FASTAPI -------------
# Création d'une instance de FastAPI
app = FastAPI(
    title="NLP project",
    description="<h3>Description:</h3>API for sentiment analysis market research using Truspilot services" +
                "<h3>Authors:</h3> David, Théo and Jean-Marie",
    version="v1.0.0",
    #openapi_tags=tags_metadata,
)

API_VERSION = "v1"
PATH_ROOT = "/api/" + API_VERSION + "/"

# Pour autoriser les tests en local et bypasser la sécurité cross-origin
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#---------- DASHBOARD -------------
class Job(BaseModel):
    uid: UUID = Field(default_factory=uuid4)
    status: str = "in_progress"
    label: str = ""
    progress: int = 0
    progress_max: int = 100
    result: dict = None


# On crée un dictionnaire pour enregistrer les tâches un peu longues
jobs: Dict[UUID, Job] = {}  # Dict as job storage


# Fonction principale sous surveillance
# async def task_nlp(queue: asyncio.Queue, category_id: int):
#     for i in range(1, 10):  # do work and return our progress
#         await asyncio.sleep(0.5)
#         await queue.put(i)
#         print(task_progress)
#     await queue.put(None)

task_label = ""
task_progress = 0
task_progress_max = 100

# async def task_watching(queue: asyncio.Queue):
#     global task_progress, task_progress_max
#     print('watching : Started!')
#     while task_progress != abs(task_progress_max):
#         await asyncio.sleep(0.5)
#         print('watching : ', task_progress, '/', task_progress_max)
#         await queue.put(task_progress)
#         task_progress += 1
#     await queue.put(None)


# async def monitor_watching() -> None:
#     global task_progress

#     queue = asyncio.Queue()
#     task = asyncio.create_task(task_watching(queue))
#     while (1):
#         progress = await queue.get() # monitor task progress
#         if progress == None:
#             break
#         task_progress += 1

#     print('watching : Finished!')


# # async def task_nlp(queue: asyncio.Queue, category_id: int):
# #     category_link = df_categories['link'][category_id]
# #     category_link = category_link.split("/")[-1]
# #     json_category_npl = get_json_from_category_link(queue, category_link, max_companies=10, max_reviews=20)
# #     await queue.put(json_category_npl)


# async def task_nlp(queue: asyncio.Queue, category_id: int):
#     category_link = df_categories['link'][category_id]
#     category_link = category_link.split("/")[-1]
#     json_category_npl = get_json_from_category_link(category_link, max_companies=5, max_reviews=10)
#     await queue.put(json_category_npl)


# # async def task_progress(queue: asyncio.Queue, category_id: int):
# #     for i in range(1, 10):  # do work and return our progress
# #         await asyncio.sleep(0.5)
# #         print(task_progress)


# async def monitor_nlp_from_category(uid: UUID, category_id: int) -> None:
#     queue = asyncio.Queue()
#     task = asyncio.create_task(task_nlp(queue, category_id))
#     progress = await queue.get() # monitor task progress
#     jobs[uid].result = progress
#     jobs[uid].progress = 100
#     jobs[uid].progress_max = 100
#     jobs[uid].label = task_label

#     print("UUID:", uid, "task complete!")
#     jobs[uid].status = "complete"

# #Fonction de surveillance de la fonction principale complexe
# # async def monitor_nlp_from_category(uid: UUID, category_id: int) -> None:
# #     queue = asyncio.Queue()
# #     task = asyncio.create_task(task_nlp(queue, category_id))
# #     print("monitor_nlp_from_category: Start")
# #     while (1):
# #         progress = await queue.get() # monitor task progress
# #         print("monitor_nlp_from_category: ", progress)
# #         if isinstance(progress, int):
# #             # Réception de la progression
# #             jobs[uid].progress = abs(progress)
# #             jobs[uid].progress_max = abs(task_progress_max)
# #         if isinstance(progress, dict):
# #             # Cette fois on a reçu le résultat
# #             jobs[uid].result = progress
# #             jobs[uid].progress = 100
# #             jobs[uid].progress_max = 100
# #             jobs[uid].label = task_label
# #             break
# #
# #     print("UUID:", uid, "task complete!")
# #     jobs[uid].status = "complete"


# @app.get(PATH_ROOT+"dashboard/summary/category/{category_id}",
#          tags=["Dashboard"],
#          response_model=Job,
#          summary="Start an NLP task to get the feelings of the category.",
#          description="Asynchronous function returning a UUID, which will allow you to follow the progress of the task. The result will be available upon completion of this task. **CAUTION, this operation can be very long!**",
#          status_code=HTTPStatus.ACCEPTED)
# async def launch_nlp_from_category(background_tasks: BackgroundTasks, category_id: int) -> Job:
#     new_task = Job() # Création d'une tâche
#     new_task.progress = 0
#     new_task.status = "in_progress"
#     new_task.result = ""
#     jobs[new_task.uid] = new_task # Sauvegarde de la tâche en cours
#     # Lancement d'une tache asynchrone, car le scraping peut être très long
#     background_tasks.add_task(monitor_nlp_from_category, new_task.uid, category_id)
#     # background_tasks.add_task(watching)
#     return new_task


    

progress_task = ProgressTask()

@app.get(PATH_ROOT+"dashboard/summary/status/{uid}",
         tags=["Dashboard"],
         response_model=Job,
         summary="Returns the progress of the last NPL query")
async def status_handler(uid: UUID) -> Job:
    try:
        #task = jobs[uid]
        jobs[uid].label = progress_task.task_label
        jobs[uid].status = progress_task.task_status
        jobs[uid].progress = progress_task.task_progress
        jobs[uid].progress_max = progress_task.task_progress_max
        jobs[uid].result = progress_task.json
        print(jobs[uid])
        return jobs[uid]
    except Exception as err:
        print('Status error :', err)
        raise HTTPException(status_code=404, detail=f"uid '{uid}' not found")

@app.get(PATH_ROOT+"dashboard/summary/category/{category_id}",
         tags=["Dashboard"],
         response_model=Job,
         summary="Start an NLP task to get the feelings of the category.",
         description="Asynchronous function returning a UUID, which will allow you to follow the progress of the task. The result will be available upon completion of this task. **CAUTION, this operation can be very long!**",
         status_code=HTTPStatus.ACCEPTED)
async def launch_nlp_from_category(background_tasks: BackgroundTasks, category_id:int) -> Job:
    new_task = Job()
    new_task.progress = 0
    new_task.status = "in_progress"
    new_task.result = ""
    jobs[new_task.uid] = new_task # Sauvegarde de la tâche en cours
    category_link = df_categories['link'][category_id]
    category_link = category_link.split("/")[-1]
    progress_task.start_get_json_from_category_link(category_link,  max_companies=21, max_reviews=5)
    return new_task


#---------- COMPANIES -------------
class Company(BaseModel):
    name: str
    link: str
    stars: float
    review_count: float
    category: str
    location: str
    logo: str
    url: str
    phone: str
    mail: str

    class Config:
        schema_extra = {
            "example": {
                "name": "La Fourche",
                "link": "lafourche.fr",
                "stars": 4.8,
                "review_count": 3364.0,
                "category": "Aliments, boissons & tabac",
                "location": "60 Avenue Lucie Aubrac Livry - Gargan 93190 FR",
                "logo": "https://s3-eu-west-1.amazonaws.com/tpd/screenshotlogo-domain/5b0ebb6897ae1c0001e39a75/198x149.png",
                "url": "http://www.lafourche.fr",
                "phone": "",
                "mail": "contact@lafourche.fr",
            }
        }


@app.get(PATH_ROOT+"companies",
         tags=["Companies"],
         response_model=Company,
         summary="Returns the list of all companies.")
def get_all_companies():
    return list_companies


@app.get(PATH_ROOT+"company/{id}",
         tags=["Companies"],
         response_model=Company,
         summary="Returns a company according to its identifier.")
def get_company_by_id(id: int):
    company = df_companies.iloc[id]
    # print(id, company)
    if not company.empty:
        result = {
            'name': company['name'],
            'link': company['link'],
            'stars': float(company['stars']),
            'review_count': float(company['review_count']),
            'category': company['category'],
            "location": company['location'],
            "logo": company['logo'],
            "url": company['url'],
            "phone": company['phone'],
            "mail": company['mail'],
        }
        return result
    else:
        raise HTTPException(status_code=404, detail="Company not found")


@app.get(PATH_ROOT+"company/query/{name}",
         tags=["Companies"],
         response_model=Company,
         summary="Returns a company according to its name.")
async def get_company_by_name(name: str):
    # On recherche les noms commençant par 'name' et plus large si insuffisant

    if name:
        NB_RESULT_TO_RETURN = 5

        # On remplace les accents par des lettres standards pour faciliter la recherche
        name = remove_accents(name)

        # On supprime les caractères spéciaux et on passe en minuscule
        name = re.sub('[^A-Za-z0-9 ]+', '', name)
        name = name.strip().lower()

        df_name = df_companies_name.copy()
        # On ne garde que les premières lettres
        df_search = df_companies_name.str.slice(stop=len(name))
        # On cherche les meilleures correspondances
        df_search = df_search.apply(lambda x: SequenceMatcher(None, name, x).ratio())
        # On trie les résultats pour avoir les meilleurs résultats en tête de liste
        df_search.sort_values(inplace=True, ascending=False)

        # On accèpte une correspondance à 90%
        df_best_result = df_search[df_search >= 0.9]
        nb_best_result = df_best_result.count()  # Nombre de correspondance

        if nb_best_result > NB_RESULT_TO_RETURN:
            # On a assez de résultat à proposer
            df_result = df_companies.iloc[df_best_result.index[:NB_RESULT_TO_RETURN]]
            # print(df_result.to_json())
            return JSONResponse(content=df_result['name'].to_json())
        else:
            # Il nous faut un peu plus de résultats, donc on cherche des correspondances plus larges
            if nb_best_result > 0:
                # Pour l'instant on prend au moins les résultats déjà trouvés
                df_result = df_companies.iloc[df_best_result.index[:nb_best_result]]

                # On supprime les noms déjà utilsés
                df_name.drop(df_best_result.index[:nb_best_result], inplace=True)

            # On cherche les meilleures correspondances
            df_search = df_name.apply(lambda x: SequenceMatcher(None, name, x).ratio())

            # On trie les résultats pour avoir les meilleurs résultats en tête de liste
            df_search.sort_values(inplace=True, ascending=False)

            # On ne garde que le nombre de résultats qui nous manquaient
            df_search = df_companies.iloc[df_search.index[:NB_RESULT_TO_RETURN - nb_best_result]]

            if nb_best_result > 0:
                df_result = pd.concat([df_result, df_search])
            else:
                df_result = df_search

            # print(df_result.to_json())
            return JSONResponse(content=df_result['name'].to_json())


#---------- CATEGORIES -------------
class Category(BaseModel):
    name: str
    link: str
    level: str

    class Config:
        schema_extra = {
            "example": {
                "name": "Maison & jardin",
                "link": "home_garden",
                "level": "0",
            }
        }


@app.get(PATH_ROOT+"categories",
         tags=["Categories"],
         response_model=Category,
         summary="Returns the list of all categories.",
         responses={200: {'model': Category}, 404: {'model': None}})
def get_all_categories():
    return list_categories


@app.get(PATH_ROOT+"category/{id}",
         tags=["Categories"],
         response_model=Category,
         summary="Returns a category according to its identifier.")
def get_category_by_id(id: int) -> Category :
    category = df_categories.iloc[id]
    result = {
        'name': category['name'],
        'link': category['link'],
        'level': category['level'],
    }
    return result


@app.get(PATH_ROOT+"category/query/{name}",
         tags=["Categories"],
         response_model=Category,
         summary="Returns a category according to its name.")
async def get_category_by_name(name: str):
    # On recherche les noms commençant par 'name' et plus large si insuffisant

    if name:
        NB_RESULT_TO_RETURN = 5

        # On remplace les accents par des lettres standards pour faciliter la recherche
        name = remove_accents(name)
        # On supprime les caractères spéciaux et on passe en minuscule
        name = re.sub('[^A-Za-z0-9 ]+', '', name)
        name = name.strip().lower()

        df_name = df_categories_name.copy()
        # On ne garde que les premières lettres
        df_search = df_categories_name.str.slice(stop=len(name))
        # On cherche les meilleures correspondances
        df_search = df_search.apply(lambda x: SequenceMatcher(None, name, x).ratio())
        # On trie les résultats pour avoir les meilleurs résultats en tête de liste
        df_search.sort_values(inplace=True, ascending=False)

        # On accèpte une correspondance à 90%
        df_best_result = df_search[df_search >= 0.9]
        nb_best_result = df_best_result.count()  # Nombre de correspondance

        if nb_best_result > NB_RESULT_TO_RETURN:
            # On a assez de résultat à proposer
            df_result = df_categories.iloc[df_best_result.index[:NB_RESULT_TO_RETURN]]
            # print(df_result.to_json())
            return JSONResponse(content=df_result.to_json())
        else:
            # Il nous faut un peu plus de résultats, donc on cherche des correspondances plus larges
            if nb_best_result > 0:
                # Pour l'instant on prend au moins les résultats déjà trouvés
                df_result = df_categories.iloc[df_best_result.index[:nb_best_result]]

                # On supprime les noms déjà utilsés
                df_name.drop(df_best_result.index[:nb_best_result], inplace=True)

            # On cherche les meilleures correspondances
            df_search = df_name.apply(lambda x: SequenceMatcher(None, name, x).ratio())

            # On trie les résultats pour avoir les meilleurs résultats en tête de liste
            df_search.sort_values(inplace=True, ascending=False)

            # On ne garde que le nombre de résultats qui nous manquaient
            df_search = df_categories.iloc[df_search.index[:NB_RESULT_TO_RETURN - nb_best_result]]

            if nb_best_result > 0:
                df_result = pd.concat([df_result, df_search])
            else:
                df_result = df_search

            # print(df_result.to_json())
            return JSONResponse(content=df_result['name'].to_json())


if __name__ == "__main__":
    # uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
    # uvicorn main:app --reload