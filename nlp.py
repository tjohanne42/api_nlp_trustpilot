import os

import spacy
import torch
import pandas as pd
import numpy as np
import sentencepiece
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from transformers import CamembertForSequenceClassification, CamembertTokenizer, AdamW

model = None
TOKENIZER = None

def init_nlp(model_path="model_nlp.pt"):
    global model, TOKENIZER

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


def preprocess(raw_reviews, sentiments=None):
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
    
    encoded_batch = TOKENIZER.batch_encode_plus(raw_reviews,
                                                add_special_tokens=True,
                                                return_attention_mask=True,
                                                padding=True,
                                                truncation=True,
                                                return_tensors = 'pt')
    if sentiments:
        sentiments = torch.tensor(sentiments)
        return encoded_batch['input_ids'], encoded_batch['attention_mask'], sentiments
    return encoded_batch['input_ids'], encoded_batch['attention_mask']


def predict(reviews, model):
    with torch.no_grad():
        model.eval()
        input_ids, attention_mask = preprocess(reviews)
        retour = model(input_ids, attention_mask=attention_mask)
        #print(retour)
        return torch.argmax(retour[0], dim=1)


def senti_predict(df_reviews, len_max=200):
    """
    Fonction qui prend un dataframe 
    et 
    ajoute une colonne avec le labelle 0 --> sentiment negatif / 1 --> sentiment negatif
    """
    # prepare dataframe for predict
    global model

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
        senti_predict = predict(reviews_to_predict, model).numpy().tolist()

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
    