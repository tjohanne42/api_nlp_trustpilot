from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
import random
import time
import json


def scrap_companies_from_category_link(category_link, location=False, numberofreviews=0, status="all",
								  timeperiode=0, scrap_best_score=True,
								  max_companies=-1, delay_min=0.5, delay_max=1.5, max_req=1):
	
	"""
	func :  scrap all results from a category_link search on trustpilor and return dict
			on their site, first results are companies_with_best_score and then they are all results
			in facts I don't see any difference between those results, so I add an arg scrap_best_score, if it sets True we scrap only firsts results,
			else we scrap only seconds results (if we scrap both of them we get only doublons)
			on the other way, the site shows 20+ results if we are not on the last page, that's why I count them with companies_count
			if companies_count < 20 then we are on the last page
			by the way, the site himself provides doublons, so if the link is already in our dic, we skip it
	
	params:
		category_link : str -> category_link_link to search
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
	page = 1

	url = "https://fr.trustpilot.com/categories/" + category_link + "?"
	if location:
		url += "location=" + location + "&"
	url += "numberofreviews=" + str(numberofreviews) + "&"
	if status != "":
		url += "status=" + status + "&"
	url += "timeperiode=" + str(timeperiode) + "&"
	url += "page="
	
	companies = {"name": [], "link": [], "stars": [], "review_count": [], "location": [], "category_link": []}
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
				time.sleep(random.uniform(delay_min, delay_max))

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
				companies["category_link"].append(category_link)
				
				company_count_on_page += 1
				if max_companies > 0 and len(companies["name"]) >= max_companies:
					return companies
		
		if company_count_on_page >= 20:
			page += 1
			time.sleep(random.uniform(delay_min, delay_max))
		else:
			done = True
	return companies
