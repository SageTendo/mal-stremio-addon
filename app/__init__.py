from config import Config

web_protocol = "http" if Config.DEBUG == 1 else "https"
