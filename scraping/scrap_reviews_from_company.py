from bs4 import BeautifulSoup
import requests
import numpy as np
import pandas as pd
import random
import time

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
