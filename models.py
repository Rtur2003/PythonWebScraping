from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ScrapeRequest(BaseModel):
    url: str = Field(alias="url")

class ProductResponse(BaseModel):
    platformName: str
    productName: str
    description: str
    productUrl: str
    imageUrl: str
    price: str
    currency: str = "TRY"
    scrapedDate: datetime