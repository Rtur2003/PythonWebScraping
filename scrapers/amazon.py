import re
import json
from bs4 import BeautifulSoup
from datetime import datetime
import requests

def scrape_amazon(html: str,url: str) -> dict:
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    }
    r = requests.get(url, headers=headers)
    soup=BeautifulSoup(r.content, 'lxml')
    productName_tag = soup.find('span', class_=['a-size-large', 'product-title-word-break'])
    productName = productName_tag.text.strip() if productName_tag else ""

    description_tag = soup.find('span', attrs={'class':'product-title-word-break'})
    description = description_tag.text.strip() if description_tag else ""

    img_tag = soup.find('img', attrs={'id':'landingImage'})
    imageUrl = img_tag['src'] if img_tag else ""

    price_tag = soup.find('span', attrs={'class':'a-price-whole'})
    price = price_tag.text.strip().rstrip(',') if price_tag else ""

    return {
        "platformName": "Amazon",
        "productName": productName,
        "description": description,
        "productUrl": url,
        "imageUrl": imageUrl,
        "price": price,
        "currency": "TRY",
        "scrapedDate": datetime.utcnow().isoformat()
    } 

    