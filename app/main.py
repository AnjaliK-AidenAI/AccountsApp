from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Routers
from app.api.v1 import (
    accounts,
    projects,
    departments,
    units,
    verticals,
    locations,
    statuses,
    account_export,
    account_import,
    contact
)

# --------------------------
# Create FastAPI App
# --------------------------
app = FastAPI(
    title="iApps Account Management API",
    version="1.0.0",
    description="Client Accounts, Projects, Contacts, and Lookup Management System",
)


# --------------------------
# CORS (Required for frontend)
# --------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------
# API ROUTES
# --------------------------
API_PREFIX = "/api/v1"

app.include_router(account_export.router, prefix=API_PREFIX)
app.include_router(account_import.router, prefix=API_PREFIX)
app.include_router(accounts.router, prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(departments.router, prefix=API_PREFIX)
app.include_router(units.router, prefix=API_PREFIX)
app.include_router(verticals.router, prefix=API_PREFIX)
app.include_router(locations.router, prefix=API_PREFIX)
app.include_router(statuses.router, prefix=API_PREFIX)
app.include_router(contact.router, prefix=API_PREFIX)



# --------------------------
# ROOT / HEALTH CHECK
# --------------------------
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to the iApps Account Management API (v1)",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

def main():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
if __name__ == "__main__":
    main()