import pandas as pd
from IPython import display

from scraping import *
from nlp import *


def make_json(df_companies, df_reviews):
	json = {}

	json["nb_companies"] = df_companies.shape[0]
	json["nb_reviews"] = df_reviews.shape[0]
	json["stars_mean"] = df_companies["stars"].mean()

	# wordclouds

	# stats with sentiments

	return json


def get_json_from_category_link(category_link, numberofreviews=0, status="all", timeperiode=0,
							max_companies=-1, max_reviews=-1, delay_min=0.5, delay_max=1.5, max_req=1):


	# scraping category
	companies, reviews = scrap_category(category_link, numberofreviews=numberofreviews, status=status,
										timeperiode=timeperiode, max_companies=max_companies, max_reviews=max_reviews,
										delay_min=delay_min, delay_max=delay_max, max_req=max_req)

	df_companies = pd.DataFrame(data=companies)
	df_reviews = pd.DataFrame(data=reviews)

	display.display(df_reviews.head())



	# apply NLP on reviews
	df_reviews = senti_predict(df_reviews)
	
	display.display(df_reviews.head())

	# make json from data
	json = make_json(df_companies, df_reviews)

	return json



if __name__ == "main":
	model, TOKENIZER = init_nlp()

	print("blbl")
	df_categories = pd.read_csv("csv/categories.csv")

	json = get_json_from_category_link(df_categories["link"][0], max_companies=2, max_reviews=2, verbose=1)

	print("\n", "json".center(6, " ").center(100, "-"), "\n")
	print(json)