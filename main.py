from bs4 import BeautifulSoup
import requests

req = requests.get('https://en.wikipedia.org/wiki/Python_(programming_language)')
soup = BeautifulSoup(req.text, "lxml")

section = soup.find("section", class_="categories_rightColumn__x8o71")

div = section.find("div", id="food_beverages_tobacco")
print(div)