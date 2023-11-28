"""
This is the app file where all the apis' will be present for our FastAPI backend application
"""
import base64

from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi.responses import JSONResponse
import redis

from config import Settings

app = FastAPI()
redis_client = redis.Redis(host='localhost',port=6379)
email_threshold_var = 'threshold'


templates = Jinja2Templates(directory="templates")
settings = Settings()



@app.get("/")
def root():
    return {"Status": "Application is up and running!"}

@repeat_every(seconds=300)
async def periodic_alert_check():
    send_mail()

@app.on_event("startup")
async def startup_event():
    await periodic_alert_check()


pihole_api_url_summary = f"http://{settings.PIHOLE_IP}/admin/api.php?summary&auth={settings.AUTH}"
pihole_api_url = f"http://{settings.PIHOLE_IP}/admin/api.php"

@app.get("/pihole/get_email_threshold")
def get_email_threshold():
    current_email_threshold = redis_client.get(email_threshold_var)
    print(int(current_email_threshold))
    return current_email_threshold

@app.get("/pihole/get_enabled_status")
def get_enabled_status():
    url = f"http://127.0.0.1/admin/api.php?status&auth={settings.AUTH}"
    data = requests.get(url)
    return data.json()

@app.post("/pihole/set_email_threshold")
def set_email_threshold(threshold: dict):
    thresholdVal = threshold.get('threshold', '')

    redis_client.set(email_threshold_var, thresholdVal)
    response = {
        "Status": "Threshold Updated!"
    }
    return response


@app.get("/pihole/summary")
def get_pihole_summary(request: Request):
    try:
        response = requests.get(pihole_api_url_summary)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        data = response.json()
        #data = {"domains_being_blocked": "158, 149", "ads_blocked_today": "10"}
        return templates.TemplateResponse("index.html", {"request": request, "data": data})
        #return data
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Pi-hole API: {str(e)}")


@app.post("/pihole/ads/send_email")
def send_mail():
    try:
        response = requests.get(pihole_api_url_summary)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
        data = response.json()

        ads = int(data["ads_blocked_today"])
        ads_threshold = get_email_threshold()
        print("This is threshold", ads_threshold)
        ads = 100
        if ads > int(ads_threshold):
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
                print("Server login done")
                
                # Send the email
                server.sendmail(settings.sender_email, settings.receiver_email, message.as_string())

                print("Mail sent")

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/pihole/domains/add_whitelist")
def add_whitelist(request: Request, domain: dict):
    # try:
    data = domain.get('domain', '')
    #     print("Received data:", data)
    #     # Your processing logic here
    #     return JSONResponse(content={"status": data})
    # except Exception as e:
    #     raise HTTPException(status_code=422, detail=str(e))
    token = "5c6AD7R1czB60fgkh6whE8upMj4COgqNKtIitDjnT2o%3D" #Add token from Pihole dash here - REMOVE LATER - GET FROM ENV FILE
    url = "http://127.0.0.1/admin/scripts/pi-hole/php/groups.php" # GET FROM ENV FILE

    payload = f"action=add_domain&domain={data}&type=0&comment=&token={token}"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'PHPSESSID=fd7f1g3lg2t5bi40ee3k6j3oeo'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

    if response.status_code == 200:
        print(f"Domain '{data}' whitelisted successfully.")
        redis_client.append('whitelisted', ","+data)

    else:
        print(f"Error whitelisting domain '{data}'.")


    return response.json()

@app.post("/pihole/domains/add_blacklist")
def add_blacklist(domain: dict):

   try:
       data = domain.get('domain', '')
       token = "5c6AD7R1czB60fgkh6whE8upMj4COgqNKtIitDjnT2o%3D"
       url = "http://127.0.0.1/admin/scripts/pi-hole/php/groups.php"

       payload = f"action=add_domain&domain={data}&type=1&comment=&token={token}"
       headers = {
           'Content-Type': 'application/x-www-form-urlencoded',
           'Cookie': 'PHPSESSID=fd7f1g3lg2t5bi40ee3k6j3oeo'
       }

       response = requests.request("POST", url, headers=headers, data=payload)

       print(response.text)

       if response.status_code == 200:
           print(f"Domain '{data}' blacklisted successfully.")
           redis_client.append('blacklisted', "," + data)

       else:
           print(f"Error blacklisting domain '{data}'.")

       return response.json()

   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))


#@app.get("/pihole/domains/get_blacklist")
#def get_blacklist():
#    domains = redis_client.get('blacklisted')
#    print("Blacklisted domains are", str(domains))
#    blacklist_dict = {
#        "Blacklist": domains
#    }
#    return blacklist_dict


#@app.get("/pihole/domains/get_whitelist")
#def get_whitelist():
#    domains = redis_client.get('whitelisted')
#    print("Whitelisted domains are", str(domains))
#    whitelist_dict = {
#        "Whitelist": domains
#    }
#    return whitelist_dict

@app.get("/pihole/domains/get_blacklist_whitelist")
def get_blacklist_whitelist():
    blacklisted_domains = redis_client.get('blacklisted')
    whitelisted_domains = redis_client.get('whitelisted')

    print("Blacklisted domains are", str(blacklisted_domains))
    print("Whitelisted domains are", str(whitelisted_domains))

    result_dict = {
        "Blacklist": blacklisted_domains,
        "Whitelist": whitelisted_domains
    }

    return result_dict
@app.get("/pihole/enable")
def enable_pihole(request: Request):
    try:
        response = requests.get(f"{pihole_api_url}?enable&auth={settings.AUTH}")
        if response.status_code == 200:
            print("Pi-hole enabled.")
            subject = "Ad Blocker Alert"
            body = "The Pihole has been enabled!"

            message = MIMEMultipart()
            message["From"] = settings.sender_email
            message["To"] = ", ".join(settings.receiver_email)
            message["Subject"] = subject

            message.attach(MIMEText(body, "plain"))

            # Establish a connection with the SMTP server
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                print("connection established")
                # Login to your Gmail account
                server.login(settings.sender_email, settings.password)
                print("Server login done")
                # Send the email
                server.sendmail(settings.sender_email, settings.receiver_email, message.as_string())
                print("Mail sent")


            #return templates.TemplateResponse("index.html", {"request": request, "enabled": "Yes"})
        else:
            print("Error enabling Pi-hole.")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pihole/disable")
def disable_pihole():
    try:
        response = requests.get(f"{pihole_api_url}?disable=0&auth={settings.AUTH}")
        if response.status_code == 200:
            print("Pi-hole disabled indefinitely.")
            subject = "Ad Blocker Alert"
            body = "The Pihole has been disabled!"

            message = MIMEMultipart()
            message["From"] = settings.sender_email
            message["To"] = ", ".join(settings.receiver_email)
            message["Subject"] = subject

            message.attach(MIMEText(body, "plain"))

            # Establish a connection with the SMTP server
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                print("connection established")
                # Login to your Gmail account
                server.login(settings.sender_email, settings.password)
                print("Server login done")
                # Send the email
                server.sendmail(settings.sender_email, settings.receiver_email, message.as_string())
                print("Mail sent")
        else:
            print("Error disabling Pi-hole.")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
