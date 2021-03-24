import pandas as pd
from IPython import display
import spacy
from collections import Counter
import re  ### regular expressions
from scraping import *
from nlp import *


def make_json(df_companies, df_reviews) -> dict:
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
    json["wordcloud"] = get_wordcloud(df_reviews, 10)

    # stats with sentiments

    return json


def get_json_from_category_link(category_link, numberofreviews=0, status="all", timeperiode=0,
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
    companies, reviews = scrap_category(category_link, numberofreviews=numberofreviews, status=status,
                                        timeperiode=timeperiode, max_companies=max_companies, max_reviews=max_reviews,
                                        delay_min=delay_min, delay_max=delay_max, max_req=max_req)

    df_companies = pd.DataFrame(data=companies)
    df_reviews = pd.DataFrame(data=reviews)

    # display.display(df_reviews.head())

    # apply NLP on reviews
    df_reviews = senti_predict(df_reviews)

    # display.display(df_reviews.head())

    # make json from data
    json = make_json(df_companies, df_reviews)
    print('get_json_from_category_link', json)

    return json


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

def get_wordcloud(df_reviews: pd.DataFrame, len_wordcloud: int):
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