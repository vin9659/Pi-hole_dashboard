from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PIHOLE_IP: str = "127.0.0.1"   # IP address
    AUTH:str = "20600623f9b0c68e5729fe3dff3f5d720ebef999554cc4708e8bc8e350aa0b4f"               # API token from API settings of PiHole
    sender_email: str = "swamykk007@gmail.com"
    receiver_email: list = ["swamykk007@gmail.com"]
    password: str = "bcgf kkba zzot jrji"         # App password from Google account of sender
