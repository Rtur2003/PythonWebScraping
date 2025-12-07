from bs4 import BeautifulSoup
from datetime import datetime
import requests


def scrape_amazon(html: str, url: str) -> dict:
    content = html
    if not content:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.text

    soup = BeautifulSoup(content, "lxml")

    product_tag = soup.find("span", class_=["a-size-large", "product-title-word-break"])
    product_name = product_tag.get_text(strip=True) if product_tag else ""

    description_tag = soup.find("span", attrs={"class": "product-title-word-break"})
    description = description_tag.get_text(strip=True) if description_tag else product_name

    image_tag = soup.find("img", attrs={"id": "landingImage"})
    image_url = image_tag.get("src") if image_tag else ""

    price_tag = soup.find("span", attrs={"class": "a-price-whole"})
    price = price_tag.get_text(strip=True).rstrip(",") if price_tag else ""

    return {
        "platformName": "Amazon",
        "productName": product_name,
        "description": description,
        "productUrl": url,
        "imageUrl": image_url,
        "price": price,
        "currency": "TRY",
        "scrapedDate": datetime.utcnow().isoformat(),
    }
