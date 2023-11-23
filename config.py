from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PIHOLE_IP: str = ""   # IP address
    AUTH:str = ""               # API token from API settings of PiHole
    sender_email: str = ""
    receiver_email: list = [""]
    password: str = ""         # App password from Google account of sender