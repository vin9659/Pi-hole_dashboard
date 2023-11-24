"""
This is the app file where all the apis' will be present for our FastAPI backend application
"""
from fastapi import FastAPI, HTTPException, Query, Depends
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import Settings

app = FastAPI()
settings = Settings()

@app.get("/")
def root():
    return {"Status": "Application is up and running!"}


pihole_api_url_summary = f"http://{settings.PIHOLE_IP}/admin/api.php?summary&auth={settings.AUTH}"

@app.get("/pihole/summary")
def get_pihole_summary():
    try:
        response = requests.get(pihole_api_url_summary)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        data = response.json()
        return data
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Pi-hole API: {str(e)}")
    

@app.post("/pihole/ads/{ads_threshold}")
def send_mail(ads_threshold: int):
    try:
        response = requests.get(pihole_api_url_summary)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        data = response.json()

        ads = int(data["ads_blocked_today"])

        if ads > ads_threshold:
            subject = "Ad Blocker Alert"
            body = f"The ads blocked by the Pi-Hole have crossed the threshold {ads_threshold}"

            message = MIMEMultipart()
            message["From"] = settings.sender_email
            message["To"] =  ", ".join(settings.receiver_email)
            message["Subject"] = subject

            message.attach(MIMEText(body, "plain"))

            # Establish a connection with the SMTP server
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                print("connection established")
                
                # Login to your Gmail account
                server.login(settings.sender_email, settings.password)
                
                # Send the email
                server.sendmail(settings.sender_email, settings.receiver_email, message.as_string())

                print("Mail sent")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    