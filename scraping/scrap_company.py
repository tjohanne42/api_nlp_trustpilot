from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
import random
import time
import json

def get_soup_from_url(url, max_req, delay_min, delay_max):
	req_done = False
	nb_try = 0
	while not req_done:
		try:
			req = requests.get(url)
			try:
				soup = BeautifulSoup(req.text, "lxml")
			except:
				soup = BeautifulSoup(req.text, "html.parser")
			req_done = True
		except:
			nb_try += 1
			if max_req > 0 and nb_try >= max_req:
				raise ValueError("Connection not found.")
			time.sleep(random.uniform(delay_min, delay_max))
	return soup

def get_dict_company(script, company_link):
	try:
		streetAddress = script["address"]["streetAddress"]
	except:
		streetAddress = ""
	try:
		addressLocality = script["address"]["addressLocality"]
	except:
		addressLocality = ""
	try:
		postalCode = script["address"]["postalCode"]
	except:
		postalCode = ""
	try:
		addressCountry = script["address"]["addressCountry"]
	except:
		addressCountry = ""
	location = streetAddress + " " + addressLocality + " " + postalCode + " " + addressCountry
#	location = script["address"]["streetAddress"] + " " + script["address"]["addressLocality"] + " " + script["address"]["postalCode"] + " " + script["address"]["addressCountry"]

	try:
		d_type = script["@type"]
	except:
		d_type = np.nan
	try:
		logo = script["image"]
	except:
		logo = np.nan
	try:
		url = script["url"]
	except:
		url = np.nan
	try:
		phone = script["telephone"]
	except:
		phone = np.nan
	try:
		review_count = script["aggregateRating"]["reviewCount"]
	except:
		review_count = np.nan
	try:
		stars_average = script["aggregateRating"]["ratingValue"]
	except:
		stars_average = np.nan
	try:
		mail = script["email"]
	except:
		mail = np.nan
	dict_company = {
					"company_link": company_link,
					"type": d_type,
					"location": location,
					"logo": logo,
					"url": url,
					"phone": phone,
					"review_count": review_count,
					"stars_average": stars_average,
					"mail": mail
					}
	return dict_company

def get_dict_review(review):
	try:
		date_published = review["datePublished"]
	except:
		datePublished = np.nan
	try:
		title_review = review["headline"]
	except:
		title_review = np.nan
	try:
		content_review = review["reviewBody"]
	except:
		content_review = np.nan
	try:
		stars = review["reviewRating"]["ratingValue"]
	except:
		stars = np.nan
	dict_review =   {
					"date_published": date_published,
					"title_review": title_review,
					"content_review": content_review,
					"stars": stars
					}
	return dict_review

def scrap_company(company_link, max_reviews=-1, delay_min=0.5, delay_max=1.5, max_req=1):
	url = "https://fr.trustpilot.com/review/" + company_link + "?page="
	
	page = 1
	
	# get soup from url
	soup = get_soup_from_url(url + str(page), max_req, delay_min, delay_max)
	# get script content from soup
	script = json.loads(soup.find('script', type='application/ld+json').string)[0]

	# scrap infos of company
	dict_company = get_dict_company(script, company_link)
	
	# init df_reviews
	dict_reviews = {"date_published": [], "title_review": [], "content_review": [], "stars": [], "company_link": []}
	
	# if max reviews==0, return empty df_reviews
	if max_reviews==0:
		return dict_company, dict_reviews
	
	# scrap reviews
	total_reviews = 0
	while True:
		
		if page != 1:
			# get soup from url
			soup = get_soup_from_url(url + str(page), max_req, delay_min, delay_max)
			# get script content from soup
			script = json.loads(soup.find('script', type='application/ld+json').string)[0]
		
		review_count = 0
		# for each review on page
		for review in script["review"]:
			new_dict_review = get_dict_review(review)
			
			# add those reviews to dict_reviews_list
			for key, value in new_dict_review.items():
				dict_reviews[key].append(new_dict_review[key])
			dict_reviews["company_link"].append(company_link)
				
			review_count += 1
			total_reviews += 1
			
			# if we have scrapped {max_reviews} reviews
			if max_reviews > 0 and total_reviews >= max_reviews:
				return dict_company, dict_reviews
		
		# if the page has less than 20 reviews, then we are on the last page, we stop the func
		if review_count < 19:
			 return dict_company, dict_reviews

		page += 1
		time.sleep(random.uniform(delay_min, delay_max))

	return dict_company, dict_reviews
