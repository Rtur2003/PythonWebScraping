import re
import json
from bs4 import BeautifulSoup
from datetime import datetime
import requests

def scrape_trendyol(html: str,url: str) -> dict:
    r = requests.get(url)
    soup=BeautifulSoup(r.content, 'html.parser')
    productName=""
    product_tag=soup.find('h1', class_='product-title')
    productName = product_tag.get_text(strip=True) if product_tag else None
    description=""
    description=productName
    imageUrl=""
    img_tag = soup.find('img', class_='_carouselImage_abb7111')
    imageUrl = img_tag["src"] if img_tag else None 
    price=""
    price_tag = soup.find("span", class_="discounted") or soup.find("span", class_="original")
    if not price_tag:
        price_tag = soup.select_one("div.campaign-price-wrapper p.new-price")
    price_raw = price_tag.get_text(strip=True) if price_tag else None
    price = None
    if price_raw:
        price = re.sub(r'[^\d,\.]', '', price_raw)

    return {
        "platformName": "Trendyol",
        "productName": productName,
        "description": description,
        "productUrl": url,
        "imageUrl": imageUrl,
        "price": price,
        "currency": "TRY",
        "scrapedDate": datetime.utcnow().isoformat()
    }