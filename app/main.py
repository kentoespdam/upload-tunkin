from fastapi import FastAPI, UploadFile
from starlette.middleware.cors import CORSMiddleware

from app import TunkinRepository

app = FastAPI(
    title="Upload Tunkin API",
    root_path="/v1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)


@app.get("/")
def index():
    return {"Hello": "World"}


@app.post("/tunkin")
async def upload_file(file: UploadFile):
    repository = TunkinRepository()
    result = repository.read_excel(file)
    return result
