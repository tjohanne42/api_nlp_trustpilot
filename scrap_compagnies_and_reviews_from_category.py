from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
import random
import time

from scrap_reviews_from_company import *
from scrap_companies_from_category import *

def scrap_companies_and_reviews_from_category(category, location=False, numberofreviews=25, status="",
										 timeperiode=12, max_companies=-1, max_reviews=-1, verbose=0, max_req=1):
	
	#scrap companies
	companies = scrap_companies_from_search_category(category, location=location, numberofreviews=numberofreviews, status=status,
													timeperiode=timeperiode, max_companies=max_companies, max_req=max_req)
	if verbose > 0:
		print("scrap companies DONE")
	
	#scrap reviews
	reviews = {"consumer_name": [], "consumer_nb_review_writed": [], "stars": [],
			   "title_review": [], "content_review": [], "date_experience": [], "company": [], "category": []}
	
	size = len(companies["link"])
	i = 0
	while i < size:
		#get reviews of each company
		new_reviews = scrap_reviews_from_company(companies["link"][i], category=category, max_reviews=max_reviews, max_req=max_req)
		if verbose > 0:
			verbose_print = companies["link"][i]
			print(f"{i}/{size-1} scrap reviews of {verbose_print} DONE")
			
		#join those reviews whith reviews of all companies
		for key, value in reviews.items():
			reviews[key] = reviews[key] + new_reviews[key]
		i += 1
		
	return companies, reviews
	