import flask
from flask import Flask
import http.client
import base64

class BaseAPI:
    api = "api.upcloud.com"
    api_version = "1.3"
    token = base64.b64encode("tapaug2021ee:gr4D334uG2021".encode())

    def get(self, endpoint):
        conn = http.client.HTTPSConnection(self.api)
        url = "/" + self.api_version + endpoint
        headers = {
            "Authorization": "Basic " + self.token.decode(),
            "Content-Type": "application/json"
        }
        conn.request("GET", url, None, headers)
        res = conn.getresponse()
        self.printresponse(res.read())

    def printresponse(self, res):
        data = res.decode(encoding="UTF-8")
        print(data)


class account(BaseAPI):
    endpoint = "/account"

    def do(self):
        self.get(self.endpoint)

class plans(BaseAPI):
    endpoint="/plan"
    def do(self):
        self.get(self.endpoint)

class server(BaseAPI):
    endpoint="/server"

    def do(self):
        self.get(self.endpoint)

if __name__ == '__main__':
     plans().do()