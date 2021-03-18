import pandas as pd
from IPython import display

from scraping import *

def blbl(category_link, numberofreviews=0, status="all", timeperiode=0, max_companies=-1, max_reviews=-1,
		delay_min=0.5, delay_max=1.5, max_req=1):

	json = {}


	# scraping category
	companies, reviews = scrap_category(category_link, numberofreviews=numberofreviews, status=status,
										timeperiode=timeperiode, max_companies=max_companies, max_reviews=max_reviews,
										delay_min=delay_min, delay_max=delay_max, max_req=max_req)
	df_companies = pd.DataFrame(data=companies)
	df_reviews = pd.DataFrame(data=reviews)

	if verbose > 0:
		display.display(df_companies.info())
		display.display(df_companies.head())

		display.display(df_reviews.info())
		display.display(df_reviews.head())


	# apply NLP on reviews
	#df_reviews = label_df(df_reviews)


	# make json
	json["nb_companies"] = df_companies.shape[0]
	json["nb_reviews"] = df_reviews.shape[0]
	json["stars_mean"] = df_companies["stars"].mean()

	# wordclouds

	# stats with sentiments

	return json



df_categories = pd.read_csv("csv/categories.csv")

json = blbl(df_categories["link"][0], max_companies=2, max_reviews=2, verbose=1)

print("\n", "json".center(6, " ").center(100, "-"), "\n")
print(json)