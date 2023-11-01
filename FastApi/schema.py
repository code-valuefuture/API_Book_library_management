
from pydantic import BaseModel
from typing import Optional,List
from datetime import datetime

class Book(BaseModel):
    bookcode: int
    name: str
    author: str
    year_published: int
    category: str
    sumbook: int 
    rating: Optional[float] = None

class RentedBook(BaseModel):
    rentcode:int
    bookcode: int
    account: str
    rent_date: Optional[datetime]=None
    return_date: Optional[datetime]=None

class Renter(BaseModel):
    account: str
    password: str
    name: str= None
    email: str= None
    phone: str= None
    book_list: List[int] = []