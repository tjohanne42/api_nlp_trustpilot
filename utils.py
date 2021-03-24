import os
import requests
from tqdm import tqdm # for progress bar
import unicodedata
import unidecode


def remove_accents(input_str):
    """
        example :
            input_str = "Montréal, über, 12.89, Mère, Françoise, noël, 889"
            return      "Montreal, uber, 12.89, Mere, Francoise, noel, 889"
    """
    nkfd_form = unicodedata.normalize('NFKD', unidecode.unidecode(input_str))
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None


def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in tqdm(response.iter_content(CHUNK_SIZE)):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)


def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = get_confirm_token(response)

    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)

    save_response_content(response, destination)


if not os.path.isfile("model_nlp.pt"):
    ret = input("model_nlp.pt not foud. Do you want to download it? y/n\n")
    if "y" in ret or "Y" in ret:
        download_file_from_google_drive("1IwWzki8oEywewiTadbqfyX8hLb60litJ", "model_nlp.pt")
    else:
        print("Exit program...")
        exit()