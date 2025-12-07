import re
from bs4 import BeautifulSoup
from datetime import datetime
import requests


def scrape_trendyol(html: str, url: str) -> dict:
    content = html
    if not content:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        content = response.text

    soup = BeautifulSoup(content, "lxml")

    product_tag = soup.find("h1", class_="product-title")
    product_name = product_tag.get_text(strip=True) if product_tag else ""

    description = product_name

    image_tag = soup.find("img", class_="_carouselImage_abb7111")
    image_url = image_tag.get("src", "") if image_tag else ""

    price_tag = soup.find("span", class_="discounted") or soup.find("span", class_="original")
    if not price_tag:
        price_tag = soup.select_one("div.campaign-price-wrapper p.new-price")
    price_raw = price_tag.get_text(strip=True) if price_tag else ""
    price = re.sub(r"[^\d,\.]", "", price_raw) if price_raw else ""

    return {
        "platformName": "Trendyol",
        "productName": product_name,
        "description": description,
        "productUrl": url,
        "imageUrl": image_url,
        "price": price,
        "currency": "TRY",
        "scrapedDate": datetime.utcnow().isoformat(),
    }
