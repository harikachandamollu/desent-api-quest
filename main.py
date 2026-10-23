from fastapi import FastAPI, Body, HTTPException, status
from typing import Any
from pydantic import BaseModel

app = FastAPI(title="Desent API Quest")

# Level 1: Ping
@app.get("/ping")
def ping():
    return {"success": True}

# Level 2: Echo
@app.post("/echo")
def echo(payload: Any = Body(...)):
    return payload

# Book schema for request validation
class CreateBook(BaseModel):
    title: str
    author: str
    year: int

# Temporary in-memory storage for books
books: dict[int, dict] = {}
next_book_id = 1

# Level 3a: Create a book
@app.post("/books", status_code=status.HTTP_201_CREATED)
def create_book(book: CreateBook):
    global next_book_id

    new_book = {
        "id": next_book_id,
        **book.model_dump()
    }

    books[next_book_id] = new_book
    next_book_id += 1

    return new_book

#Level 3b: Get all books
@app.get("/books")
def get_books():
    return list(books.values())

# Level 3c: Get a book by ID
@app.get("/books/{book_id}")
def get_book(book_id: int):
    
    if book_id not in books:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    return books[book_id]

# Level 4a: Update an existing book
@app.put("/books/{book_id}")
def update_book(book_id: int, book: CreateBook):
    
    if book_id not in books:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    updated_book = {
        "id": book_id,
        **book.model_dump()
    }
    books[book_id] = updated_book
    
    return updated_book

# Level 4b: Delete a book by ID
@app.delete("/books/{book_id}", status_code=status.HTTP_200_OK)
def delete_book(book_id: int):
    
    if book_id not in books:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    del books[book_id]
    
    return {
        "success": True,
        "message": "Book deleted successfully."
    }