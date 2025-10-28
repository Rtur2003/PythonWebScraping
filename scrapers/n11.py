import re
import json
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import cloudscraper

def scrape_n11(url: str) -> dict:
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9"
    }
    response = scraper.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    productName_tag = soup.find("h1", class_="proName")
    productName = productName_tag.text.strip().split("(")[0] if productName_tag else ""

    description_tag = soup.find("h1", class_="proName")
    description = description_tag.text.strip() if description_tag else ""

    imageUrl = None
    div_tag = soup.find("div", class_="imgObj")
    if div_tag:
        img_tag = div_tag.find("img")
        if img_tag:
            imageUrl = img_tag.get("data-src") or img_tag.get("data-original") or img_tag.get("src")

    price =None
    script_text = soup.find("script", text=re.compile("var google_cust_params"))
    if script_text:
        match = re.search(r'"pfinalprice":"([\d.]+)"', script_text.string)
    if match:
        price_str = match.group(1)
        price_float = float(price_str)
        price = "{:,.2f}".format(price_float).replace(",", "X").replace(".", ",").replace("X", ".")

        return {
        "platformName": "n11",
        "productName": productName,
        "description": description,
        "productUrl": url,
        "imageUrl": imageUrl,
        "price": price,
        "currency": "TRY",
        "scrapedDate": datetime.utcnow().isoformat()
    }
