from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router # Import the v1 router
from app.core.config import settings

app = FastAPI(
    title="Auth Boilerplate API",
    openapi_url="/api/v1/openapi.json", # Match the router prefix
    docs_url="/api/v1/docs", # Customize docs URL
    redoc_url="/api/v1/redoc" # Customize redoc URL
)

# Set all CORS enabled origins
# In production, restrict this more carefully!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    # allow_origins=["http://localhost:3000", "http://localhost:8080"], # Example specific origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# Include the API router
app.include_router(api_router, prefix="/api/v1") # Prefix for versioning

@app.get("/")
async def root():
    return {"message": "Auth API is running"}

# Optional: Add startup/shutdown events if needed
# @app.on_event("startup")
# async def startup_event():
#     # Initialize DB, etc. (Alembic handles schema)
#     pass

# @app.on_event("shutdown")
# async def shutdown_event():
#     # Close DB connections, etc.
#     pass