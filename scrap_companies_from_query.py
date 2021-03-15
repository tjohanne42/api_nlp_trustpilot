from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
import random
import time

def scrap_companies_from_query(query, max_companies=-1, verbose=0, delay=0.5, max_req=1):
	url = "https://fr.trustpilot.com/search?query=" + query
	companies = {"name": [], "link": [], "stars": [], "review_count": []}
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

	return companies
