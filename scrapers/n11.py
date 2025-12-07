import re
from bs4 import BeautifulSoup
from datetime import datetime
import cloudscraper


def scrape_n11(url: str) -> dict:
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    response = scraper.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    product_name_tag = soup.find("h1", class_="proName")
    product_name = product_name_tag.text.strip().split("(")[0] if product_name_tag else ""

    description_tag = soup.find("h1", class_="proName")
    description = description_tag.text.strip() if description_tag else ""

    image_url = ""
    div_tag = soup.find("div", class_="imgObj")
    if div_tag:
        img_tag = div_tag.find("img")
        if img_tag:
            image_url = (
                img_tag.get("data-src") or img_tag.get("data-original") or img_tag.get("src") or ""
            )

    price = ""
    script_text = soup.find("script", text=re.compile("var google_cust_params"))
    price_match = None
    if script_text and script_text.string:
        price_match = re.search(r'"pfinalprice":"([\d.]+)"', script_text.string)
    else:
        # Some product pages omit the analytics script; keep price parsing tolerant. @Rtur2003
        price_match = None

    if price_match:
        price_value = float(price_match.group(1))
        price = (
            "{:,.2f}".format(price_value)
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
    else:
        price_tag = soup.select_one("ins#productPrice") or soup.select_one("div.newPrice ins")
        if price_tag:
            raw_price = price_tag.get_text(strip=True)
            price = re.sub(r"[^\d,\.]", "", raw_price)

    return {
        "platformName": "n11",
        "productName": product_name,
        "description": description,
        "productUrl": url,
        "imageUrl": image_url,
        "price": price,
        "currency": "TRY",
        "scrapedDate": datetime.utcnow().isoformat(),
    }
