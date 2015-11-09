import json

class Config:

    def __init__(self):
        try:
            self.config = json.load(file("/etc/api/config.json"))
        except ValueError:
            raise Exception("Config file is not found or is not valid JSON")