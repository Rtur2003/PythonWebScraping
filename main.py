from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import cloudscraper
from urllib.parse import urlparse
from models import ScrapeRequest, ProductResponse
from scrapers import scrape_amazon, scrape_trendyol, scrape_n11
from typing import List
import re
from urllib.parse import quote_plus
from difflib import SequenceMatcher

app = FastAPI(title="Product Scraping Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def detect_platform(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    
    if 'amazon' in domain:
        return 'amazon'
    elif 'trendyol' in domain:
        return 'trendyol'
    elif 'n11' in domain:
        return 'n11'
    else:
        raise ValueError(f"Desteklenmeyen platform: {domain}")

def fetch_html(url: str, use_cloudscraper: bool = True) -> str:
    """HTML çek - varsayılan olarak Cloudscraper kullan"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    try:
        if use_cloudscraper:
            scraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
            )
            response = scraper.get(url, headers=headers, timeout=30)
        else:
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        
        response.raise_for_status()
        print(f"[FETCH] {response.status_code} - {len(response.text)} bytes")
        return response.text
    except Exception as e:
        print(f"[FETCH ERROR] {url}: {e}")
        raise

def clean_product_name(name: str) -> str:
    if not name:
        return ""
    name = name.strip()
    name = re.sub(r'\([^)]*\)', ' ', name)
    name = re.sub(r'(\d+)(GB|TB|MB)', r'\1 \2', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip(':-,. ')
    color_pattern = r'\s*[-–]\s*(Mavi|Siyah|Beyaz|Kırmızı|Yeşil|Sarı|Pembe|Mor|Gri|Turuncu|Blue|Black|White|Red|Green|Yellow|Pink|Purple|Gray|Orange).*$'
    name = re.sub(color_pattern, '', name, flags=re.IGNORECASE)
    patterns = [
        r'\s*\[[^\]]*\]\s*',  
        r'\s+\d+\s*(Adet|Li|lü|lu)\s*', 
        r'\s*:\s*$',                  
        r'\s*-\s*$',                 
    ]
    for pattern in patterns:
        name = re.sub(pattern, ' ', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()
    words = name.split(' ')
    if len(words) > 4:
        name = ' '.join(words[:4])
    print(f"[CLEAN] '{name}'")
    return name

def search_trendyol(query: str) -> str:
    try:
        query_encoded = quote_plus(query)
        search_url = f"https://www.trendyol.com/sr?q={query_encoded}"
        print(f"[TRENDYOL] Arama: {search_url}")
        
        html = fetch_html(search_url, use_cloudscraper=True)
        soup = BeautifulSoup(html, "lxml")
        
        script = soup.find('script', id='__NEXT_DATA__')
        if script:
            import json
            data = json.loads(script.string)
            products = (
                data.get('props', {})
                .get('pageProps', {})
                .get('searchResult', {})
                .get('products', [])
            )
            
            if products:
                first_product = products[0]
                product_url = f"https://www.trendyol.com{first_product.get('url', '')}"
                print(f"[TRENDYOL] Bulunan: {product_url}")
                return product_url
        
        link = soup.select_one("a.product-card")
        if not link:
            link = soup.select_one('a[href*="/p-"]')
        
        if link:
            href = link.get('href')
            if not href.startswith('http'):
                href = 'https://www.trendyol.com' + href
            print(f"[TRENDYOL] Bulunan (DOM): {href}")
            return href
        
        raise Exception("Ürün bulunamadı")
        
    except Exception as e:
        print(f"[TRENDYOL ERROR] {e}")
        return None

def search_amazon(query: str) -> str:
    try:
        search_url = f"https://www.amazon.com.tr/s?k={query.replace(' ', '+')}"
        print(f"[AMAZON] Arama: {search_url}")
        
        html = fetch_html(search_url, use_cloudscraper=True)
        soup = BeautifulSoup(html, "lxml")
        
        selectors = [
            "div[data-component-type='s-search-result'] h2 a",
            "div[data-component-type='s-search-result'] a.a-link-normal",
            "div.s-result-item[data-asin] h2 a",
        ]
        
        first_link = None
        for selector in selectors:
            first_link = soup.select_one(selector)
            if first_link:
                print(f"[AMAZON] Selector kullanıldı: {selector}")
                break
        
        if not first_link:
            raise Exception("Ürün bulunamadı")
        
        href = first_link.get('href', '')
        
        if '/dp/' in href:
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
            if asin_match:
                asin = asin_match.group(1)
                product_url = f"https://www.amazon.com.tr/dp/{asin}"
                print(f"[AMAZON] Bulunan: {product_url}")
                return product_url
        
        if '/sspa/' in href:
            decoded = requests.utils.unquote(href)
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', decoded)
            if asin_match:
                asin = asin_match.group(1)
                product_url = f"https://www.amazon.com.tr/dp/{asin}"
                print(f"[AMAZON] Bulunan (sspa): {product_url}")
                return product_url
        
        raise Exception("ASIN bulunamadı")
        
    except Exception as e:
        print(f"[AMAZON ERROR] {e}")
        return None

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def search_n11(query: str) -> str:
    try:
        search_url = f"https://www.n11.com/arama?q={query.replace(' ', '+')}"
        print(f"[N11] Arama: {search_url}")
        
        html = fetch_html(search_url, use_cloudscraper=True)
        soup = BeautifulSoup(html, "lxml")
        
        results = soup.select('li.column a.plink')
        best_match = None
        best_ratio = 0
        if not results:
            single_result = soup.select_one('a.plink')
            results = [single_result] if single_result else []
        
        for link in results:
            title = link.get('title', '') or link.get_text(strip=True)
            ratio = similar(query.lower(), title.lower())
            if ratio > best_ratio:
                best_ratio = ratio
                href = link.get('href')
                if not href.startswith('http'):
                    href = 'https://www.n11.com' + href
                best_match = href
        
        if best_match:
            print(f"[N11] En iyi eşleşme: {best_match} (benzerlik: {best_ratio:.2f})")
            return best_match
        
        raise Exception("Ürün bulunamadı")
        
    except Exception as e:
        print(f"[N11 ERROR] {e}")
        return None

@app.post("/api/compare", response_model=List[ProductResponse])
async def compare_products(request: ScrapeRequest):
    try:
        base_product = await scrape_product(request)
        base_name = clean_product_name(base_product.productName)
        print(f"[INFO] Aranacak ürün adı: '{base_name}'")
        
        results = [base_product.model_dump()]
        current_platform = detect_platform(request.url)

        if current_platform != 'trendyol':
            try:
                trendyol_url = search_trendyol(base_name)
                if trendyol_url:
                    trendyol_req = ScrapeRequest(url=trendyol_url)
                    trendyol_data = await scrape_product(trendyol_req)
                    results.append(trendyol_data.model_dump())
            except Exception as e:
                print(f"[WARN] Trendyol hatası: {e}")
        
        if current_platform != 'amazon':
            try:
                amazon_url = search_amazon(base_name)
                if amazon_url:
                    amazon_req = ScrapeRequest(url=amazon_url)
                    amazon_data = await scrape_product(amazon_req)
                    results.append(amazon_data.model_dump())
            except Exception as e:
                print(f"[WARN] Amazon hatası: {e}")
        
        if current_platform != 'n11':
            try:
                n11_url = search_n11(base_name)
                if n11_url:
                    n11_req = ScrapeRequest(url=n11_url)
                    n11_data = await scrape_product(n11_req)
                    results.append(n11_data.model_dump())
            except Exception as e:
                print(f"[WARN] N11 hatası: {e}")
        
        if len(results) == 1:
            print("[WARN] Sadece orijinal platform bulundu, diğerleri başarısız")
        
        print(f"[SUCCESS] {len(results)} platform bulundu")
        return results
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape", response_model=ProductResponse)
async def scrape_product(request: ScrapeRequest):
    try:
        platform = detect_platform(request.url)
        print(f"[INFO] Platform: {platform}, URL: {request.url}")
        
        if platform == 'amazon':
            html = fetch_html(request.url, use_cloudscraper=True)
            product_data = scrape_amazon(html, request.url)
        elif platform == 'trendyol':
            html = fetch_html(request.url, use_cloudscraper=True)
            product_data = scrape_trendyol(html, request.url)
        elif platform == 'n11':
            product_data = scrape_n11(request.url)
        else:
            raise HTTPException(status_code=400, detail="Desteklenmeyen platform")
        
        print(f"[SUCCESS] Ürün: {product_data['productName']}, Fiyat: {product_data['price']}")
        return ProductResponse(**product_data)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"HTTP hatası: {str(e)}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scraping hatası: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
