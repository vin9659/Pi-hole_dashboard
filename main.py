"""
Start uvicorn server and serve the app from app.py file
Can access app through port 8000
"""
from fastapi import FastAPI
import uvicorn
import redis

from app import app


if __name__ == "__main__":

    uvicorn.run(app, host="127.0.0.1", port=8000)
