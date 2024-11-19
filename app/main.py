# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi import HTTPException

# Import the upload_router (make sure the import path is correct)
from app import upload_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Document Parser Service...")
    try:
        yield
    finally:
        print("Shutting down Document Parser Service...")

app = FastAPI(
    title="Document Parser Service",
    description="API for parsing various document types",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount the router with prefix
app.include_router(upload_router.router, prefix="/api")

@app.get("/")
async def root():
    """
    Root endpoint that returns a basic welcome message or status.
    """
    return {"message": "Welcome to the Document Parser Service"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    print(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Add this if you're running the file directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)