import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.utils.logging_config import configure_logging
from backend.routes import (
    user,
    development_testing,
    project,
    brand,
    prompt,
    tracking_config,
    topic,
    tag,
    reports,
    reference,
    scrape,
    admin,
    health,
)


# Configure structured logging (LOG_LEVEL from env) before the app starts.
configure_logging()

# App.
app = FastAPI()

# Include all routes
# app.include_router(adm.router)


#Middleware for React server
# Explicit allow-list from env (never "*"): strip whitespace and drop empties
# so a trailing comma / blank value can't produce a bogus "" origin.
origins = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(development_testing.router)
app.include_router(project.router)
app.include_router(brand.router)
app.include_router(prompt.router)
app.include_router(tracking_config.router)
app.include_router(topic.router)
app.include_router(tag.router)
app.include_router(reports.router)
app.include_router(reference.router)
app.include_router(scrape.router)
app.include_router(admin.router)
app.include_router(health.router)

# Run.
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
