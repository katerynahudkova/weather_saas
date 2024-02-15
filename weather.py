import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

API_TOKEN = ""
RSA_KEY = ""

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def generate_weather(exclude: str, location, date):
    url_base_url = "https://weather.visualcrossing.com"
    url_api = "VisualCrossingWebServices/rest/services/timeline"
    
    url = f"{url_base_url}/{url_api}/{location}/{date}?unitGroup=metric&include=days&key={RSA_KEY}&contentType=json"

    headers = {"X-Api-Key": RSA_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == requests.codes.ok:
        return json.loads(response.text)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)

def coat(temp):
    if temp > 20:
        return "be fr, it's too warm"
    elif temp > 10:
        return "i mean you may but it might be too hot in it"
    elif temp > 0:
        return "you should"
    else:
        return "of course wear a coat, it's freazing!"


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/weather", methods=["POST"])
def weather_endpoint():
    start_dt = dt.datetime.now()
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)

    token = json_data.get("token")
    location = json_data.get("location")
    date = json_data.get("date")
    requester_name = json_data.get("requester_name")

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    exclude = ""
    if json_data.get("exclude"):
        exclude = json_data.get("exclude")

    weather = generate_weather(exclude, location, date)["days"][0]
    weather_result = {
        "temp_c": weather["temp"],
        "wind_kph": weather["windspeed"],
        "pressure_mb": weather["pressure"],
        "humidity": weather["humidity"],
        "description": weather["description"],
        "should you wear a coat?": coat(int(weather["temp"]))
    }

    timestamp = dt.datetime.now()

    result = {
        "requester_name": requester_name,
        "timestamp": timestamp.isoformat(),
        "location": location,
        "date": date,
        "weather": weather_result
    }

    return result
