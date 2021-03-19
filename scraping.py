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

##
## REVIEWS
##

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

##
## SRAP COMPANIES
##

def scrap_companies_from_category_link(category_link, location=False, numberofreviews=0, status="all",
								  timeperiode=0, scrap_best_score=True,
								  max_companies=-1, delay_min=0.5, delay_max=1.5, max_req=1):
	

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
		
	soup = get_soup_from_url(url + str(page), max_req, delay_min, delay_max)

	done = False
	while not done:
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

##
## REGROUP COMPANIES AND REVIEWS
##

def scrap_category(category_link, location=False, numberofreviews=0, status="all", timeperiode=0,
					max_companies=-1, max_reviews=-1, delay_min=0.5, delay_max=1.5, max_req=1):

	companies = scrap_companies_from_category_link(category_link, location=location, numberofreviews=numberofreviews, status=status, 
													timeperiode=timeperiode, max_companies=max_companies,
													delay_min=delay_min, delay_max=delay_max, max_req=max_req)


	dict_reviews = {"date_published": [], "title_review": [], "content_review": [], "stars": [], "company_link": []}

	dict_companies = {"name": [], "category_link": [], "company_link": [], "type": [], "location": [], "logo": [], "url": [],
					"phone": [], "review_count": [], "stars_average": [], "mail": []}

	size = len(companies["link"])
	i = 0
	while i < size:
		# try:
		# 	new_dict_company, new_dict_reviews = scrap_company(companies["link"][i], max_reviews=max_reviews, delay_min=delay_min,
		# 													delay_max=delay_max, max_req=max_req)
		# except:
		# 	i += 1
		# 	continue
		new_dict_company, new_dict_reviews = scrap_company(companies["link"][i], max_reviews=max_reviews, delay_min=delay_min,
		 													delay_max=delay_max, max_req=max_req)

		for key, value in dict_reviews.items():
			dict_reviews[key] += new_dict_reviews[key]
		for key, value in new_dict_company.items():
			dict_companies[key].append(new_dict_company[key])

		dict_companies["name"].append(companies["name"][i])
		dict_companies["category_link"].append(category_link)
		i += 1

	return dict_companies, dict_reviews
