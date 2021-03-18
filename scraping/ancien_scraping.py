from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
import random
import time

def scrap_companies_from_query(query, max_companies=-1, verbose=0, delay=0.5, max_req=1):
	url = "https://fr.trustpilot.com/search?query=" + query
	companies = {"name": [], "link": [], "stars": [], "review_count": [], "category": []}
	if max_companies == 0:
		return companies
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
			print("try {nb_try} failed:", url)
			time.sleep(random.uniform(delay, delay+1))
	if verbose > 0:
		print(url)
	# to create a list of compaghy
	compagny_list = soup.find("div", class_="results")
	compagny_cards = compagny_list.find_all("div", class_="item clearfix")
	counts = 0
	for compagny_card in compagny_cards:
		counts = counts + 1
		if counts <= max_companies or max_companies == -1:
			# Name from the compagny
			compagny_name = compagny_card.find("h3").find("a").text.split("|")[0]
			# Adress from the compagny
			compagny_name_to_request = compagny_card.find("a")["href"].split("/")[-1]
			# number of reviews from compagny
			compagny_nb_review_writed = compagny_card.find("span", class_="review-count").text.replace(chr(160), "").split(" ")[0]
			# average scores of reviews from compagny
			try:
				compagny_trustscore = compagny_card.find("span", class_="trustscore").text.split(" ")[-1].replace(",", ".")
			except:
				return companies  
			#############
			#add to dic
			companies["name"].append(compagny_name)
			companies["link"].append(compagny_name_to_request)
			companies["stars"].append(float(compagny_trustscore))
			companies["review_count"].append(int(compagny_nb_review_writed))
			companies["category"].append(np.nan)

	return companies



def scrap_reviews_from_company(company, category=False, page=1, max_reviews=-1, verbose=0, delay=0.5, max_req=1):
	url = "https://fr.trustpilot.com/review/" + company + "?page="
	reviews = {"consumer_name": [], "consumer_nb_review_writed": [], "stars": [],
			   "title_review": [], "content_review": [], "date_experience": [], "company": [], "category": []}
	if max_reviews == 0:
		return reviews
	done = False
	while not done:
		req_done = False
		nb_try = 0
		while not req_done:
			try:
				req = requests.get(url + str(page))
				try:
					soup = BeautifulSoup(req.text, "lxml")
				except:
					soup = BeautifulSoup(req.text, "html.parser")
				req_done = True
			except:
				nb_try += 1
				if max_req > 0 and nb_try >= max_req:
					raise ValueError("Connection not found.")
				print("try {nb_try} failed:", url + str(page))
				time.sleep(random.uniform(delay, delay+1))

		if verbose > 0:
			print("url:", url + str(page))
		
		nb_review_on_page = 0
		review_list = soup.find("div", class_="review-list")
		try:
			review_cards = review_list.find_all("div", class_="review-card")
		except:
			raise ValueError("TrustPilot blocked you.")
		
		for review_card in review_cards:
			
			#consumer_name
			try:
				consumer_name = " ".join(review_card.find("div", class_="consumer-information__name").text.split())
			except:
				consumer_name = np.nan
			
			#consumer_nb_review_writed
			try:
				consumer_nb_review_writed = int(review_card.find("div", class_="consumer-information__review-count").find("span").text.split()[0])
			except:
				consumer_nb_review_writed = np.nan
			
			#stars
			try:
				stars = int(review_card.find("div", class_="star-rating star-rating--medium").find("img")["alt"].split()[0])
			except:
				stars = np.nan
			
			#title_review
			try:
				title_review = " ".join(review_card.find("h2", class_="review-content__title").find("a").text.split())
			except:
				title_review = np.nan
			
			#content_review
			try:
				content_review = " ".join(review_card.find("p", class_="review-content__text").text.split())
			except:
				content_review = np.nan
			
			#date_experience
			try:
				date_experience = " ".join(review_card.find("p", class_="review-content__dateOfExperience").text.split(":")[-1].split())
			except:
				date_experience = np.nan
				
			#add to dic
			reviews["consumer_name"].append(consumer_name)
			reviews["consumer_nb_review_writed"].append(consumer_nb_review_writed)
			reviews["stars"].append(stars)
			reviews["title_review"].append(title_review)
			reviews["content_review"].append(content_review)
			reviews["date_experience"].append(date_experience)
			reviews["company"].append(company)
			if category:
				reviews["category"].append(category)
			else:
				reviews["category"].append(np.nan)
			
			#count nb of reviews
			nb_review_on_page += 1
			
			if max_reviews > 0 and len(reviews["consumer_name"]) >= max_reviews:
				return reviews
			
			
		if verbose > 0:
			print(f"nb_review_on_page {page} : {nb_review_on_page}")
		if nb_review_on_page < 20:
			done = True
		else:
			page += 1
			time.sleep(random.uniform(delay, delay+1))
	return reviews



def scrap_companies_from_category(category, location=False, numberofreviews=0, status="all",
								  timeperiode=0, page=1, verbose=0, scrap_best_score=True,
								  max_companies=-1, delay=0.5, max_req=1):
	
	"""
	func :  scrap all results from a category search on trustpilor and return dict
			on their site, first results are companies_with_best_score and then they are all results
			in facts I don't see any difference between those results, so I add an arg scrap_best_score, if it sets True we scrap only firsts results,
			else we scrap only seconds results (if we scrap both of them we get only doublons)
			on the other way, the site shows 20+ results if we are not on the last page, that's why I count them with companies_count
			if companies_count < 20 then we are on the last page
			by the way, the site himself provides doublons, so if the link is already in our dic, we skip it
	
	params:
		category : str -> category_link to search
		location : str -> code postal or ville
		numberofreviews : int -> must be in [0, 25, 50, 100, 250, 500]
		status : str -> must be in ["all", "unclaimed", "claimed", ""]
		timeperiode : int -> must be in [0, 6, 12, 18]
		page : int -> load this page and higher
		verboses : bool -> print steps
		scrap_best_score : bool -> scrap best_score_companies or ALL (no difference between them, set this param to True it's faster)
		max_companies : int -> exit func when nb_companies >= max_companies
		max_reviews : int -> exit func when nb_reviews >= max_reviews
	"""
	
	url = "https://fr.trustpilot.com/categories/" + category + "?"
	if location:
		url += "location=" + location + "&"
	url += "numberofreviews=" + str(numberofreviews) + "&"
	if status != "":
		url += "status=" + status + "&"
	url += "timeperiode=" + str(timeperiode) + "&"
	url += "page="
	
	companies = {"name": [], "link": [], "stars": [], "review_count": [], "location": [], "category": []}
	if max_companies == 0:
		return companies
	done = False
	while not done:
		req_done = False
		nb_try = 0
		while not req_done:
			try:
				req = requests.get(url + str(page))
				try:
					soup = BeautifulSoup(req.text, "lxml")
				except:
					soup = BeautifulSoup(req.text, "html.parser")
				req_done = True
			except:
				nb_try += 1
				if max_req > 0 and nb_try >= max_req:
					raise ValueError("Connection not found.")
				print("try {nb_try} failed:", url + str(page))
				time.sleep(random.uniform(delay, delay+1))

		if verbose > 0:
			print(url + str(page))
		
		company_count_on_page = 0
		
		# possibly 2 blocks of companies (most rated and all)
		div_containers = soup.find_all("div", class_="styles_businessUnitCardsContainer__1ggaO")

		for div_container in div_containers:
			# for each block
			div = div_container.find("div", class_="styles_categoryBusinessListWrapper__2H2X5")
			
			companies_with_best_score = True
			if div == None:
				# if we find div with 2H2X5 class it's companies_with_best_score so we need to enter in this div
				# else it's all we don't have to enter anywhere
				div = div_container
				companies_with_best_score = False
				
			a_balises = div.find_all("a")
			for a_balise in a_balises:
				
				# if not companies_with_best_score, we don't want to scrap, only to count them to know if we are on last page
				if scrap_best_score:
					if not companies_with_best_score:
						continue
				else:
					if companies_with_best_score:
						company_count_on_page += 1
						continue
				
				# for each entreprise, find link, title, stars
				link = a_balise["href"].split("/")[-1]
				if link == "fr":
					splitted = a_balise["href"].split("/")
					link = splitted[len(splitted)-2] + "/" + splitted[len(splitted)-1]
				title = a_balise.find("div", class_="styles_businessTitle__1IANo").text
				
				# try to get more info if they have
				try:
					infos_div = a_balise.find("div", class_="styles_textRating__19_fv").text
					infos = infos_div.split("\xa0·\xa0")
					infos[0] = int(infos[0].split()[0])
					infos[1] = float(infos[1].split()[-1])
				except:
					if verbose == 2:
						print("No stars and nb_reviews for", title, link)
					infos = [np.nan, np.nan]
				# try to get location  if they have
				try:
					div_locations = a_balise.find("div", class_="styles_location__3JATO")
					spans_location = div_locations.find_all("span", class_=None)
					location = ""
					if spans_location != None:
						i = 0
						while i < len(spans_location):
							location += spans_location[i].text
							if i == 0:
								location += " . "
							i += 1
				except:
					if verbose == 2:
						print("No location for", title, link)
					location = np.nan

				# if this is a doublon we skip it
				if link in companies["link"]:
					company_count_on_page += 1
					continue
					
				# add infos in dic
				companies["name"].append(title)
				companies["link"].append(link)
				companies["stars"].append(infos[1])
				companies["review_count"].append(infos[0])
				companies["location"].append(location)
				companies["category"].append(category)
				
				company_count_on_page += 1
				if max_companies > 0 and len(companies["name"]) >= max_companies:
					return companies
		
		if verbose > 0:   
			print(f"nb company on page {page} : {company_count_on_page}")
		if company_count_on_page >= 20:
			page += 1
			time.sleep(random.uniform(delay, delay+1))
		else:
			done = True
	return companies



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


def scrap_companies_and_reviews_from_query(query, max_companies=-1, max_reviews=-1, delay=0.5, max_req=1, verbose=0):
	
	#scrap companies
	companies = scrap_companies_from_query(query, max_companies=max_companies, delay=delay, max_req=max_req)
	if verbose > 0:
		print(f"scrap {max_companies} companies for query {query} DONE")
	
	#scrap reviews
	reviews = {"consumer_name": [], "consumer_nb_review_writed": [], "stars": [],
			   "title_review": [], "content_review": [], "date_experience": [], "company": [], "category": []}
	
	size = len(companies["link"])
	i = 0
	while i < size:
		verbose_print = companies["link"][i]
		#get reviews of each company
		try:
			new_reviews = scrap_reviews_from_company(companies["link"][i], category=np.nan, max_reviews=max_reviews, max_req=max_req)
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
	