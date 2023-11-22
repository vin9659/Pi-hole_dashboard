"""
This is the app file where all the apis' will be present for our FastAPI backend application
"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"Status": "Application is up and running!"}
