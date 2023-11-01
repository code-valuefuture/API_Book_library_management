from fastapi import FastAPI, status, HTTPException
from fastapi.responses import FileResponse
import numpy as np
import pandas as pd 
from datetime import datetime
from typing import Optional

import schema
app = FastAPI()
    #   
#A Trang Chu 
@app.get("/",description = 'Chủ đề: Quản lý thư viện sách')
def main():
    textmain= "Chủ đề: Quản lý thư viện Sách"
    return textmain

####
## Data
###
# Các tài khoản người thuê sách
renter_data= pd.DataFrame({
    "account":["Alice", "Bob"],
    "password":["Alice", "Bob"],
    "name":["Alice","Bob"],
    "email": ["alice@gmail.com","bob@gmail.com"],
    "phone": ["01234","09879"],
    "book_list":[[1],[2]]
    })
# Các đầu sách hiện có trong thư viện
book_data= pd.DataFrame({
                            "bookcode":[101,102],
                            "name":["The Great Gatsby","To Kill a Mockingbird"],
                            "author":["F. Scott Fitzgerald","Harper Lee"],
                            "year_published":["1925","1960"],
                            "category":["Fiction","Action"],
                            "sumbook":[3,5],
                            "rating": [4.5, 4.9]
})
# Các phiếu thuê sách
rented_books = pd.DataFrame({
                                "rentcode":[1,2,3],
                                "bookcode":[101,102,102],
                                "account":["Alice","Bob","Alice"],
                                "rent_date":[datetime(2023, 1, 1),datetime(2023, 2, 1),datetime(2023,3,1)],
                                "return_date": [datetime(2023, 3, 11),datetime(2022, 4, 11),datetime(2023,4,1)]
})

####
## #API đăng ký tài khoản renter
####

#API đăng ký tài khoản renter
@app.post("/register")
async def register(acc: schema.Renter):
    if(renter_data["account"].isin([acc.account]).any()== True):
        return {"Đăng ký không thành công": "Tài khoản đã tồn tại mời đặt tài khoản mới"}
    
    renter_data.append({
        "account": acc.account, 
        "password": acc.password,
        "name": acc.name,
        "email": acc.email, 
        "phone": acc.phone, 
        "book_list": []
    },ignore_index = True)
    
    return acc 

#API đăng nhập tài khoản
@app.get("/login") 
async def login(acc: schema.Renter):
    if (renter_data["account"].isin([acc.account]).any()== False):
        return {"Đăng nhập không thành công":"Tên tài khoản không chính xác"}
    elif renter_data[renter_data["account"]==acc.account]["password"].isin([acc.password]).any()== True:
        return {"Thông báo": "Đăng nhập thành công"}
    else:
        return {"Đăng nhập không thành công":"Mật khẩu không chính xác"}

####
##Phương thức thêm sách cho thư viện
####
@app.post("/add_book")
async def add_book(book: schema.Book):
    new_book = {"bookcode": book.bookcode,
               "name": book.name,
               "author": book.author,
               "year_published": book.year_published,
               "category": book.category,
               "sumbook": book.sumbook,
               "rating": book.rating}
    book_data.append(new_book, ignore_index=True)
    return {"Thông báo": "Sách đã thêm thành công"}

####
##Các tương tác thuê trả sách
####
#Phương thức thuê sách
@app.post("/rent_book")
async def rent_book(rented_book: schema.RentedBook):
    # Kiểm tra xem sách có trong thư viện hay không
    if rented_book.bookcode not in book_data.bookcode.values:
        return {"Thuê không thành công": "Không tìm thấy sách"}
    # Kiểm tra xem sách có còn hàng không
    if book_data.loc[book_data['bookcode'] == rented_book.bookcode, 'sumbook'].iloc[0] == 0:# KT Soluong sach
        return {"Thuê không thành công": "Sách chưa sẵn sàng cho thuê"}
    # Kiểm tra xem người thuê có tồn tại không
    if rented_book.account not in renter_data.account.values:
        return {"Thuê không thành công": "Không tìm thấy tài khoản"}
    # Kiểm tra xem đơn thuê đó có tồn tại hay chưa
    if rented_book.rentcode in rented_books.rentcode.values:
        return {"Thuê không thành công": "Mã đơn thuê đã tồn tại"}
     # Cập nhật lại thông tin số lượng sách có sẵn
    book_data.loc[book_data['bookcode'] == rented_book.bookcode, 'sumbook'] -= 1
    rented_book_dict = {
        "rentcode": rented_book.rentcode,
        "bookcode": rented_book.bookcode,
        "account": rented_book.account,
        "rent_date": datetime.now(),
        "return_date": rented_book.return_date
    }
    rented_books.append(rented_book_dict, ignore_index=True)
    #Cập nhật danh sách sách thuê của người thuê
    renter_data.loc[renter_data['account'] == rented_book.account, 'book_list'] = renter_data.loc[renter_data['account'] == rented_book.account, 'book_list'].apply(lambda x: x + [rented_book.bookcode])

    return {"Cho thuê sách thành công. Mã đơn thuê": rented_book.rentcode}

#Phương thức trả sách
@app.post("/return_book")
async def return_book(rent1):
    if(rented_books["rentcode"].isin([int(rent1)]).any()== False):
        return {"Trả không thành công": "Không tìm thấy mã đơn thuê"}
    else:
        # Cập nhật số sách trong thư viện
        bookcode = get_bookcode_by_rentcode(rent1)
        account= get_account_by_rentcode(rent1)
        book_data.loc[book_data['bookcode'] == bookcode, 'sumbook'] += 1
        #Cập nhật list sách người thuê
        renter_data.loc[renter_data['account'] == account, 'book_list'] = \
            renter_data.loc[renter_data['account'] == account, 'book_list'].apply(lambda x: [i for i in x if i != bookcode])
        #Cập nhật dữ liệu các đơn thuê hiện có
        rented_books.drop(rented_books.loc[rented_books['rentcode'] == rent1].index, inplace=True)
        return {"Thông báo": "Sách đã được trả thành công"}
#Hàm lấy mã sách cho mã đơn
def get_bookcode_by_rentcode(rentcode: int) -> Optional[int]:
    rented_book = rented_books[rented_books["rentcode"] == rentcode]
    if rented_book.empty:
        return None
    return rented_book["bookcode"].values[0]
# Hàm lấy tài khoản cho mã đơn
def get_account_by_rentcode(rentcode: int) -> Optional[int]:
    rented_book = rented_books[rented_books["rentcode"] == rentcode]
    if rented_book.empty:
        return None
    return rented_book["account"].values[0]

####
##Các phương thức sử dụng numpy
####

# Hàm để tính trung bình cộng rating của tất cả các sách trong danh sách sách
@app.get("/average_rating")
async def get_average_rating():
    ratings = book_data["rating"].values
    ratings = ratings[~np.isnan(ratings)] # loại bỏ các giá trị NaN
    if len(ratings) == 0:
        return {"Không thành công": "Các sách chưa có Rating"}
    average_rating = np.mean(ratings)
    return {"average_rating": average_rating}

# Hàm để tính tổng số sách đang có trong thư viện
@app.get("/total_books_registered")
async def total_books_registered():
    sumbooks = book_data["sumbook"].values.astype('float64')
    total_books = np.sum(sumbooks)
    return {"total_books": total_books}

#Hàm để đếm số lượng sách trong từng thể loại
@app.get("/count_books_by_category")
async def count_books_by_category():
    categories = book_data["category"].unique()
    result = {}
    for category in categories:
        count = np.count_nonzero(book_data["category"] == category)
        result[category] = count
    return {"count_by_category": result}

#Hàm để tìm sách có rating cao nhất
@app.get("/highest_rated_book")
async def get_highest_rated_book():
    max_rating = np.max(book_data["rating"].values.astype(float))
    highest_rated_books = book_data[book_data["rating"].astype(float) == max_rating]
    return {"highest_rated_book": highest_rated_books["name"].values.tolist()}
