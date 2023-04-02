from fastapi import FastAPI
from api.client import LocationKeyClient

app = FastAPI()
client = LocationKeyClient(url= "http://192.168.1.169:8085")

@app.get("/")
def home():
    return client.location(data="testingData")