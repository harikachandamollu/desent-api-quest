import secrets

from fastapi import FastAPI, Body, HTTPException, status, Header, Query, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from typing import Any
from pydantic import BaseModel


app = FastAPI(title="Desent API Quest")

# Level 7: Custom error handling for validation errors
@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request,
    exc: RequestValidationError
):
    errors = exc.errors()

    # Invalid book ID in the URL: return 404
    if (
        request.method in {"GET", "PUT", "DELETE"}
        and any(
            error.get("loc", ())[:2] == ("path", "book_id") for error in errors
        )
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Book not found"}
        )

    # Missing required book fields: return 400
    if (
        request.method == "POST"
        and request.url.path == "/books"
        and any(
            error.get("type") == "missing"
            and error.get("loc", ())[0:1] == ("body",) for error in errors
        )
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Missing required book fields"}
        )

    # Preserving FastAPI's default validation error handling for other cases
    return await request_validation_exception_handler(request, exc)


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
def get_books(authorization: str | None = Header(default=None),
              author: str | None = None,
              page: int | None = Query(default=None, ge=1),
              limit: int | None = Query(default=None, ge=1)):

    # Level 6: Allow public filtering and pagination
    if author is None and page is None and limit is None:
        verify_token(authorization)
    
    # Retrieve all books
    result = list(books.values())

    # Filter by author if query parameter is provided
    if author is not None:
        result = [
            book for book in result if book["author"].casefold() == author.casefold()
        ]

    # Apply pagination if query parameters are provided
    if page is not None or limit is not None:
        page = page if page is not None else 1
        limit = limit if limit is not None else 10

        start = (page - 1) * limit
        end = start + limit

        result = result[start:end]
    
    return result

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

# Level 5: Authentication
class LoginRequest(BaseModel):
    
    username: str
    password: str

# Token generated when the server starts
ACCESS_TOKEN = secrets.token_urlsafe(32)

@app.post("/auth/token")
def create_token(credentials: LoginRequest):

    valid_username = secrets.compare_digest(credentials.username, "admin")
    valid_password = secrets.compare_digest(credentials.password, "password")

    if not (valid_username and valid_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return {
        "token": ACCESS_TOKEN,
        "access_token": ACCESS_TOKEN,
        "token_type": "bearer"
    }

def verify_token(authorization: str | None):

    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")

    scheme, separator, token = authorization.partition(" ")

    if (
        not separator
        or scheme.lower() != "bearer"
        or not secrets.compare_digest(token, ACCESS_TOKEN)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")