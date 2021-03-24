import pandas as pd
from IPython import display
import spacy
from collections import Counter
import re  ### regular expressions
import hashlib
import os

from bs4 import BeautifulSoup
import requests
import numpy as np
import random
import time
import json

import torch
import sentencepiece
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from transformers import CamembertForSequenceClassification, CamembertTokenizer, AdamW
import concurrent.futures


class ProgressTask(object):

	def __init__(self):
		self.model, self.TOKENIZER = self.init_nlp()
		self.cacheEnable = True
		self.cacheTime = "1 day"
		self.task_progress = 0
		self.task_progress_max = 100
		self.task_status = "complete"
		self.task_result = ""
	
	def start_get_json_from_category_link(self, category_link, max_reviews=5, max_companies=10):
		self.task_progress = 0
		self.task_progress_max = 100
		self.task_status = "in_progress"
		self.task_label = ""
		self.task_result = ""
		self.json = ""
		self.f1 = concurrent.futures.ThreadPoolExecutor().submit(self.get_json_from_category_link, category_link,
		                                               max_companies=max_companies, max_reviews=max_reviews)
		#self.get_json_from_category_link(category_link, max_companies=max_companies, max_reviews=max_reviews)


	"""

	GET JSON FROM CATGEGORY_LINK.PY

	"""

	def make_json(self, df_companies, df_reviews) -> dict:
		json = {}

		if df_companies.shape[0] == 0:
			return json

		json["nb_companies"] = df_companies.shape[0]
		if df_reviews.shape[0] == 0:
			return json

		json["stars_mean"] = df_companies["stars_average"].mean()
		json["nb_reviews"] = df_reviews.shape[0]

		json["repartition_sentiment"] = {"pos": df_reviews[(df_reviews["sentiment"] == 1)].shape[0],
										"neg": df_reviews[df_reviews["sentiment"] == 0].shape[0]}

		df_reviews["stars"] = df_reviews["stars"].astype(int)
		df_reviews["date_published"] = pd.to_datetime(df_reviews["date_published"], infer_datetime_format=True)
		df_reviews["month"] = pd.DatetimeIndex(df_reviews["date_published"]).month
		df_reviews["year"] = pd.DatetimeIndex(df_reviews["date_published"]).year

		year = df_reviews["year"].max()
		month = df_reviews[df_reviews["year"] == year]["month"].max()
		min_year = df_reviews["year"].min()

		stars_evolution_by_month = {}
		sentiment_evolution_by_month = {}

		# for each month
		while year >= min_year:
			if month <= 0:
				month = 12
				year -= 1

			if df_reviews[(df_reviews["year"] == year) & (df_reviews["month"] == month)].shape[0] > 0:
				stars_evolution_by_month[f"{year}-{month}"] = \
				df_reviews[(df_reviews["year"] == year) & (df_reviews["month"] == month)]["stars"].mean()
				sentiment_evolution_by_month[f"{year}-{month}"] = \
				df_reviews[(df_reviews["year"] == year) & (df_reviews["month"] == month)]["sentiment"].mean()
			month -= 1

		json["stars_evolution_by_month"] = stars_evolution_by_month
		json["sentiment_evolution_by_month"] = sentiment_evolution_by_month

		# add wordcloud to json
		json["wordcloud"] = self.get_wordcloud(df_reviews, 10)

		# stats with sentiments
		return json


	def get_json_from_category_link(self, category_link, numberofreviews=0, status="all", timeperiode=0,
									max_companies=-1, max_reviews=-1, delay_min=0.5, delay_max=1.5, max_req=1) -> dict:
		"""
		:param category_link:
		:param numberofreviews: numberofreviews must be in [0, 25, 50, 100, 250, 500]
								C'est le nombre de review minimum des entreprises pour qu'elles apparaissent
		:param status:      status must be in ["all", "unclaimed", "claimed", ""]
		:param timeperiode: timeperiod must be in [0, 6, 12, 18]
							The last review on the site must be more recent than {timeperiod} month
		:param max_companies:
		:param max_reviews:
		:param delay_min:
		:param delay_max:
		:param max_req: Nombre de tentatives
		:return:
		"""
		# scraping category
		companies, reviews = self.scrap_category(category_link, numberofreviews=numberofreviews, status=status,
											timeperiode=timeperiode, max_companies=max_companies, max_reviews=max_reviews,
											delay_min=delay_min, delay_max=delay_max, max_req=max_req)

		df_companies = pd.DataFrame(data=companies)
		df_reviews = pd.DataFrame(data=reviews)

		# display.display(df_reviews.head())

		# apply NLP on reviews
		df_reviews = self.senti_predict(df_reviews)

		# display.display(df_reviews.head())

		# make json from data
		self.json = self.make_json(df_companies, df_reviews)
		print('get_json_from_category_link', self.json)

		self.task_label = "complete"
		self.task_status = "complete"
		return self.json


	# if __name__ == "main":
	#     model, TOKENIZER = init_nlp()
	#
	#     df_categories = pd.read_csv("csv/categories.csv")
	#
	#     json = get_json_from_category_link(df_categories["link"][0], max_companies=2, max_reviews=2, verbose=1)
	#
	#     print("\n", "json".center(6, " ").center(100, "-"), "\n")
	#     print(json)

	# wordcloud

	def get_wordcloud(self, df_reviews: pd.DataFrame, len_wordcloud: int):
		nlp = spacy.load("fr_core_news_sm")

		# find pos words frequency
		df_pos = df_reviews[df_reviews["sentiment"] == 1]
		pos_reviews = " ".join(df_pos["content_review"].values.tolist()).replace("\n", " ")
		pos_reviews = " ".join(re.sub('[/]', ' ', pos_reviews).split())
		doc = nlp(pos_reviews)
		words = [token.lemma_
				for token in doc
				if not token.is_stop and not token.is_punct and token.text != " "]
		word_freq = Counter(words)
		pos_common_words = word_freq.most_common(len_wordcloud * 2)

		# add those words to list
		pos_words_list = []
		pos_words_count = []
		for pos_words in pos_common_words:
			pos_words_list.append(pos_words[0])
			pos_words_count.append(pos_words[1])

		# find neg words frequency
		df_neg = df_reviews[df_reviews["sentiment"] == 0]
		neg_reviews = " ".join(df_neg["content_review"].values.tolist()).replace("\n", " ")
		neg_reviews = " ".join(re.sub('[/]', ' ', neg_reviews).split())
		doc = nlp(neg_reviews)
		words = [token.lemma_
				for token in doc
				if not token.is_stop and not token.is_punct and token.text != " "]
		word_freq = Counter(words)
		neg_common_words = word_freq.most_common(len_wordcloud * 2)

		# add those words to list
		neg_words_list = []
		neg_words_count = []
		for neg_words in neg_common_words:
			neg_words_list.append(neg_words[0])
			neg_words_count.append(neg_words[1])


		# pop same words in neg and pos list
		len_pos_words_list = len(pos_words_list)
		len_neg_words_list = len(neg_words_list)
		i = 0
		while i < len_pos_words_list:
			x = 0
			while x < len_neg_words_list:
				# if we find same word
				if pos_words_list[i] == neg_words_list[x]:
					# drop word
					pos_words_list.pop(i)
					neg_words_list.pop(x)
					# drop word count
					pos_words_count.pop(i)
					neg_words_count.pop(x)
					# decrease len
					len_pos_words_list -= 1
					len_neg_words_list -= 1
				x += 1
			i += 1

		# wordcloud to json
		return {
				"pos": 	{
						"words": pos_words_list[0:len_wordcloud],
						"count": pos_words_count[0:len_wordcloud]
						},
				"neg": 	{
						"words": neg_words_list[0:len_wordcloud],
						"count": neg_words_count[0:len_wordcloud]
						}
				}
	
	"""


	SCRAPING.PY



	"""
	


	def get_url_or_cache(self, url):

		# Create a temporary directory if needed
		cacheDir = 'cache'
		if not os.path.exists(cacheDir):
			os.mkdir(cacheDir)

		try:
			urlMD5 = hashlib.md5(url.encode())
			localFile = cacheDir + "\\" + urlMD5.hexdigest()
		except ValueError:
			print(ValueError)
			return ""


		if not self.cacheEnable or (self.cacheEnable and not os.path.isfile(localFile)):
			# Download web page
			print(f'{url} has been loaded from web. Save to cache ->', localFile)
			req = requests.get(url)

			# Save web page in local file
			f = open(localFile, mode="w", encoding='utf-8')
			f.write(req.text)  # Save pretty format
			f.close()
			return req.text

		else:
			# Read the file containing the web page
			print(f'{url} has been loaded from cache ->', localFile)
			f = open(localFile, mode="r", encoding='utf-8')
			req = f.read()
			f.close()
			return req



	def get_soup_from_url(self, url, max_req, delay_min, delay_max):
		req_done = False
		nb_try = 0
		while not req_done:
			try:
				req = self.get_url_or_cache(url)
				try:
					soup = BeautifulSoup(req, "lxml")
				except:
					soup = BeautifulSoup(req, "html.parser")
				if soup != None:
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

	def get_dict_company(self, script, company_link):
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
			stars_average = float(script["aggregateRating"]["ratingValue"])
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


	def get_dict_review(self, review):
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
		dict_review = {
			"date_published": date_published,
			"title_review": title_review,
			"content_review": content_review,
			"stars": stars
		}
		return dict_review


	def scrap_company(self, company_link, max_reviews=-1, delay_min=0.5, delay_max=1, max_req=1):
		url = "https://fr.trustpilot.com/review/" + company_link + "?page="

		page = 1

		# get soup from url
		soup = self.get_soup_from_url(url + str(page), max_req, delay_min, delay_max)

		dict_reviews = {"date_published": [], "title_review": [], "content_review": [], "stars": [], "company_link": []}

		# get script content from soup
		try:
			script = json.loads(soup.find('script', type='application/ld+json').string)[0]
		except:
			return None, None

		# scrap infos of company
		dict_company = self.get_dict_company(script, company_link)

		# init df_reviews

		# if max reviews==0, return empty df_reviews
		if max_reviews == 0:
			return dict_company, dict_reviews

		# scrap reviews
		total_reviews = 0
		while True:

			if page != 1:
				# get soup from url
				soup = self.get_soup_from_url(url + str(page), max_req, delay_min, delay_max)
				# get script content from soup
				script = json.loads(soup.find('script', type='application/ld+json').string)[0]

			review_count = 0
			# for each review on page
			for review in script["review"]:
				new_dict_review = self.get_dict_review(review)

				# add those reviews to dict_reviews_list
				for key, value in new_dict_review.items():
					dict_reviews[key].append(new_dict_review[key])
				dict_reviews["company_link"].append(company_link)

				review_count += 1
				total_reviews += 1

				# if we have scrapped {max_reviews} reviews
				if max_reviews > 0 and total_reviews >= max_reviews:
					self.task_progress += 1
					if self.task_progress_max == -100 and self.task_progress >= 100:
						self.task_progress = 0
					return dict_company, dict_reviews

			# if the page has less than 20 reviews, then we are on the last page, we stop the func
			if review_count < 19:
				self.task_progress += 1
				if self.task_progress_max == -100 and self.task_progress >= 100:
					self.task_progress = 0
				return dict_company, dict_reviews

			page += 1
			self.task_progress += 1
			if self.task_progress_max == -100 and self.task_progress >= 100:
				self.task_progress = 0

			time.sleep(random.uniform(delay_min, delay_max))

		return dict_company, dict_reviews


	##
	## SRAP COMPANIES
	##

	def scrap_companies_from_category_link(self, category_link, location=False, numberofreviews=0, status="all",
										timeperiode=0, scrap_best_score=True,
										max_companies=-1, delay_min=0.5, delay_max=1, max_req=1):
		page = 1

		url = "https://fr.trustpilot.com/categories/" + category_link + "?"
		if location:
			url += "location=" + str(location) + "&"
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
			soup = self.get_soup_from_url(url + str(page), max_req, delay_min, delay_max)
			# print('scrap_companies_from_category_link :', soup)
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
						link = splitted[len(splitted) - 2] + "/" + splitted[len(splitted) - 1]
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
						self.task_progress += 1
						if self.task_progress_max == -100 and self.task_progress >= 100:
							self.task_progress = 0
						return companies

			self.task_progress += 1
			if self.task_progress_max == -100 and self.task_progress >= 100:
				self.task_progress = 0

			if company_count_on_page >= 20:
				page += 1
				time.sleep(random.uniform(delay_min, delay_max))
			else:
				done = True

		return companies


	##
	## REGROUP COMPANIES AND REVIEWS
	##

	def scrap_category(self, category_link, location=False, numberofreviews=0, status="all", timeperiode=0,
					max_companies=-1, max_reviews=-1, delay_min=0.5, delay_max=1, max_req=1):
		#self.task_label = "Scraping"
		self.task_label = "Blbl"
		self.task_progress = 0
		if (max_companies==-1 or max_reviews==-1):
			self.task_progress_max = -100
		else:
			self.task_progress_max = int(max_companies/20)+1 + (int(max_reviews/20)+1) * max_companies

		companies = self.scrap_companies_from_category_link(category_link, location=location, numberofreviews=numberofreviews,
													status=status,
													timeperiode=timeperiode, max_companies=max_companies,
													delay_min=delay_min, delay_max=delay_max, max_req=max_req)
		print('scrap_category', len(companies['link']))
		dict_reviews = {"date_published": [], "title_review": [], "content_review": [], "stars": [], "company_link": []}

		dict_companies = {"name": [], "category_link": [], "company_link": [], "type": [], "location": [], "logo": [],
						"url": [],
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
			new_dict_company, new_dict_reviews = self.scrap_company(companies["link"][i], max_reviews=max_reviews,
															delay_min=delay_min,
															delay_max=delay_max, max_req=max_req)

			for key, value in dict_reviews.items():
				dict_reviews[key] += new_dict_reviews[key]
			for key, value in new_dict_company.items():
				dict_companies[key].append(new_dict_company[key])

			dict_companies["name"].append(companies["name"][i])
			dict_companies["category_link"].append(category_link)
			i += 1

		return dict_companies, dict_reviews

	"""

	NLP.PY

	"""

	def init_nlp(self, model_path="model_nlp.pt"):
		try:
			nlp = spacy.load("fr_core_news_sm")
		except:
			os.system("python -m spacy download fr")
			os.system("python -m spacy download fr_core_news_md")

		# load model camembert
		state_dict = torch.load(model_path, map_location=torch.device('cpu'))
		#print("Loading trained model...")
		model = CamembertForSequenceClassification.from_pretrained(
			'camembert-base', num_labels = 2,
			state_dict=state_dict)
		#print("Trained model loaded!")

		# load TOKENIZER camembert
		TOKENIZER = CamembertTokenizer.from_pretrained(
		'camembert-base',
		do_lower_case=True)
		return model, TOKENIZER


	def preprocess(self, raw_reviews, sentiments=None):
		"""
		Cette fonction prends de la donnée brute en argument et retourne un 'dataloader' pytorch

		Args
			raw_reviews (array-like) : Une liste de reviews sous forme de 'str'
			
			sentiments : Une liste 'sentiments' (0 = negatif, 1 = positif) de la meme taille que
						'raw_review'
		
		Returns
			inputs_ids, attention_masks, sentiments(optionel) : Objet  de PyTorch qui contient 
						les versions tokenisees et encodees des donnees brutes
		"""
		
		encoded_batch = self.TOKENIZER.batch_encode_plus(raw_reviews,
													add_special_tokens=True,
													return_attention_mask=True,
													padding=True,
													truncation=True,
													return_tensors = 'pt')
		if sentiments:
			sentiments = torch.tensor(sentiments)
			return encoded_batch['input_ids'], encoded_batch['attention_mask'], sentiments
		return encoded_batch['input_ids'], encoded_batch['attention_mask']


	def predict(self, reviews, model):
		with torch.no_grad():
			model.eval()
			input_ids, attention_mask = self.preprocess(reviews)
			retour = model(input_ids, attention_mask=attention_mask)
			#print(retour)
			return torch.argmax(retour[0], dim=1)


	def senti_predict(self, df_reviews, len_max=200):
		"""
		Fonction qui prend un dataframe 
		et 
		ajoute une colonne avec le labelle 0 --> sentiment negatif / 1 --> sentiment negatif
		"""
		# prepare dataframe for predict

		df_reviews["content_review"] = df_reviews['content_review'].fillna(df_reviews['title_review'])
		df_reviews = df_reviews.dropna(subset=['content_review'])

		# stock reviews in list
		reviews = df_reviews['content_review'].values.tolist()

		# init variables for while
		size_dataframe = df_reviews.shape[0]
		already_predict = 0
		senti = []

		# predict reviews {len_max} by {len_max}, package per package
		while already_predict < size_dataframe:

			# nb of reviews to predict for this package
			len_to_predict = len_max
			if already_predict + len_to_predict > size_dataframe:
				len_to_predict = size_dataframe - already_predict

			# stock reviews to predict for this package
			reviews_to_predict = reviews[already_predict:already_predict+len_to_predict]

			# predict this package
			senti_predict = self.predict(reviews_to_predict, self.model).numpy().tolist()

			# add this package to senti list
			if len(senti_predict) == 1:
				senti.append(senti_predict)
			else:
				senti += senti_predict
			
			# count number of reviews predicted
			already_predict += len_to_predict

		# add new feature sentiment
		df_reviews["sentiment"] = senti

		return df_reviews