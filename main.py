import uvicorn # A installer 'Serveur uvicorn'
from fastapi import Body, FastAPI, HTTPException
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic.schema import schema
from fastapi.encoders import jsonable_encoder
import pandas as pd
from functools import partial
from difflib import SequenceMatcher
import re  ### regular expressions
import numpy as np

from utils import remove_accents

import random

# On charge les compagnies déjà scrappées pour gagner du temps
df_companies = pd.read_csv('companies.csv', sep=';', dtype={'name': str, 'link': str, 'stars': np.float32, 'review_count': np.float32, 'category': str})
list_companies = str(df_companies['link'].values.tolist())

# On remplace les accents par des lettres standards pour faciliter la recherche
df_companies_name = df_companies['name'].apply(remove_accents)

# On supprime les caractères spéciaux et on passe en minuscule
df_companies_name = df_companies_name.str.replace('[^A-Za-z0-9 ]+', '', regex=True).str.lower()

# Nettoyage des floats
df_companies['stars'].replace(np.nan, 0, inplace=True)
df_companies['review_count'].replace(np.nan, 0, inplace=True)

# On charge les catégories déjà scrappées pour gagner du temps
df_categories = pd.read_csv('categories.csv', sep=';', dtype={'name': str, 'link': str, 'level': str})
list_categories = str(df_categories['link'].values.tolist())

# On remplace les accents par des lettres standards pour faciliter la recherche selon l'écriture
df_categories_name = df_categories['name'].apply(remove_accents)

# On supprime les caractères spéciaux et on passe en minuscule
df_categories_name = df_categories_name.str.replace('[^A-Za-z0-9 ]+', '', regex=True).str.lower()

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


#category_link, numberofreviews=0, status="all", timeperiode=0, max_companies=-1, max_reviews=-1, delay=0.5, max_req=1, verbose=0


#---------- COMPANIES -------------
class Company(BaseModel):
    name: str
    link: str
    stars: float
    review_count: float
    category: str

    class Config:
        schema_extra = {
            "example": {
                "name": "La Fourche",
                "link": "lafourche.fr",
                "stars": 4.8,
                "review_count": 3364.0,
                "category": "food_beverages_tobacco",
            }
        }

def scrap_category(category):
    category += " hello world"
    return df

@app.get("/scrap/{category}")
def scrap(category, **kwargs):
    json = get_json_from_category_link(category, **kwargs)
    return JSONResponse(content=df)
    

@app.get(PATH_ROOT+"get_status")
def get_status():
    return JSONResponse(content=random.randint(0, 100))

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
    print(id)
    company = df_companies.iloc[id]
    print(company)
    if not company.empty:
        result = {
            'name': company['name'],
            'link': company['link'],
            'stars': float(company['stars']),
            'review_count': float(company['review_count']),
            'category': company['category']
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
            return JSONResponse(content=df_result.to_json())




if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    # uvicorn main:app --reload