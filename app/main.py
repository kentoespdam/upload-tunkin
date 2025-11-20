from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.routers import tunkin, auth

app = FastAPI(
    title="Upload Tunkin API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)


@app.get("/")
def index():
    return {"Hello": "World"}


app.include_router(auth.router)
app.include_router(tunkin.router)
