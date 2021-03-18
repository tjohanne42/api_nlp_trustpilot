from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
import random
import time

from scrap_reviews_from_company import *
from scrap_companies_from_category import *

def scrap_companies_and_reviews_from_category(category, location=False, numberofreviews=0, status="all",
										 timeperiode=0, max_companies=-1, max_reviews=-1, delay=0.5, max_req=1, verbose=0):
	
	#scrap companies
	companies = scrap_companies_from_category(category, location=location, numberofreviews=numberofreviews, status=status,
													timeperiode=timeperiode, max_companies=max_companies, delay=delay, max_req=max_req)
	if verbose > 0:
		print(f"scrap {max_companies} companies in category {category} DONE")
	
	#scrap reviews
	reviews = {"consumer_name": [], "consumer_nb_review_writed": [], "stars": [],
			   "title_review": [], "content_review": [], "date_experience": [], "company": [], "category": []}
	
	size = len(companies["link"])
	i = 0
	while i < size:
		verbose_print = companies["link"][i]
		#get reviews of each company
		try:
			new_reviews = scrap_reviews_from_company(companies["link"][i], category=category, max_reviews=max_reviews, max_req=max_req)
		except:
			print(f"{verbose_print} failed to load reviews")
			i += 1
			continue
		if verbose > 0:
			print(f"{i+1}/{size} scrap {max_reviews} reviews of {verbose_print} DONE")
			
		#join those reviews whith reviews of all companies
		for key, value in reviews.items():
			reviews[key] = reviews[key] + new_reviews[key]
		i += 1
		
	return companies, reviews
	