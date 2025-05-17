from flask import Flask, render_template_string, request
from geopy.geocoders import Nominatim
import requests
from datetime import datetime, timedelta, timezone
import random
import re

# secure the api key 

from dotenv import load_dotenv
import os
load_dotenv()  # Loads the .env file
api_key = os.getenv("API_KEY")


app = Flask(__name__)

# -----------------------
# Coordinate Parsing
# -----------------------

def dms_to_decimal(coord_str):
    match = re.match(r"(\d+)[°:](\d+)['](\d+(?:\.\d+)?)[\"]?([NSEW])", coord_str.strip(), re.IGNORECASE)
    if not match:
        raise ValueError("Invalid DMS format")
    degrees, minutes, seconds, direction = match.groups()
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    if direction.upper() in ['S', 'W']:
        decimal *= -1
    return decimal

def parse_coordinates(coord_input):
    try:
        # Try direct float conversion first (decimal degrees)
        return float(coord_input)
    except ValueError:
        # If fails, try DMS format
        return dms_to_decimal(coord_input)

# -----------------------
# Weather and Outfit Functions
# -----------------------

def get_lat_lon(address):
    geolocator = Nominatim(user_agent="weather_app")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None, None

def get_weather_data(lat, lon, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def convert_utc_to_ist(utc_time):
    utc_time = datetime.fromtimestamp(utc_time, timezone.utc)
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    return ist_time.strftime('%Y-%m-%d %H:%M:%S')

def is_daytime(weather_data):
    current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    sunrise = datetime.fromtimestamp(weather_data['sys']['sunrise']) + timedelta(hours=5, minutes=30)
    sunset = datetime.fromtimestamp(weather_data['sys']['sunset']) + timedelta(hours=5, minutes=30)
    return sunrise <= current_time <= sunset

def get_color_palette():
    palettes = [
        ("Sky Blue", "Soft White"), ("Pastel Pink", "Ivory"), ("Beige", "Olive Green"),
        ("Lavender", "Misty Grey"), ("Peach", "Cream"), ("Mint Green", "Ash Grey"),
        ("Powder Blue", "Sand"), ("Soft Coral", "Pale Yellow"), ("Light Mauve", "Dusty Rose"),
        ("Pistachio", "Taupe")
    ]
    return random.choice(palettes)

def recommend_outfit(weather_data, party):
    if not weather_data:
        return "No weather data available for outfit recommendation."

    temp = weather_data['main']['temp']
    humidity = weather_data['main']['humidity']
    wind_speed = weather_data['wind']['speed']
    day_time = is_daytime(weather_data)
    top_color, bottom_color = get_color_palette()

    # Define outfit options
    casual_outfits = [
        ("cotton t-shirt", "denim jeans"),
        ("polo shirt", "chino shorts"),
        ("linen shirt", "light trousers"),
        ("casual kurta", "cotton pajama"),
        ("henley tee", "joggers")
    ]

    cool_weather_outfits = [
        ("hoodie", "jeans"),
        ("full-sleeve sweater", "corduroy pants"),
        ("light jacket", "denim"),
        ("knit pullover", "thermal pants")
    ]

    cold_weather_outfits = [
        ("puffer jacket", "thermal joggers"),
        ("overcoat", "wool pants"),
        ("fleece jacket", "lined jeans")
    ]

    hot_weather_outfits = [
        ("sleeveless tee", "shorts"),
        ("light vest", "chinos"),
        ("cotton shirt", "breathable pants")
    ]

    party_outfits = [
        ("dress shirt with blazer", "tailored trousers"),
        ("semi-formal printed shirt", "slim-fit chinos"),
        ("black shirt", "grey pants"),
        ("navy shirt", "white trousers")
    ]

    # Outfit decision logic
    if party:
        outfit = random.choice(party_outfits)
    elif temp > 30:
        outfit = random.choice(hot_weather_outfits)
    elif 20 < temp <= 30:
        outfit = random.choice(casual_outfits)
    elif 10 < temp <= 20:
        outfit = random.choice(cool_weather_outfits)
    else:
        outfit = random.choice(cold_weather_outfits)

    # Add extras
    extras = []
    if wind_speed > 10:
        extras.append("windbreaker or light scarf")
    if humidity > 70:
        extras.append("breathable fabrics or carry an umbrella")

    outfit_text = f"<b>Top:</b> {outfit[0]} in {top_color}<br>" \
                  f"<b>Bottom:</b> {outfit[1]} in {bottom_color}<br>"

    if extras:
        outfit_text += f"<b>Extras:</b> {', '.join(extras)}<br>"

    outfit_text += f"<b>Time:</b> {'Daytime' if day_time else 'Nighttime'}<br>"

    return outfit_text

def get_avatar_url(gender):
    avatars = {
        'male': "https://i.pravatar.cc/150?img=12",
        'female': "https://i.pravatar.cc/150?img=47"
    }
    return avatars.get(gender.lower(), "https://i.pravatar.cc/150?img=1")

# -----------------------
# HTML Template
# -----------------------

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>AI Weather-Based Outfit Recommender</title>
<link
  rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
/>
<link rel="icon" type="image/png" href="{{ url_for('static', filename='favicon.png') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
<script src="{{ url_for('static', filename='script.js') }}"></script>
<style>
  body {
    margin: 0;
    padding: 0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #e0f7fa, #f1f8e9);
    display: flex;
    height: 100vh;
    overflow: hidden;
  }
  .container {
    display: flex;
    width: 100%;
    padding: 40px;
    box-sizing: border-box;
    animation: fadeIn 1s ease-in-out;
  }
  .left-section {
    flex: 1;
    padding: 30px;
    background-color: #ffffffdd;
    border-radius: 20px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    animation: slideInLeft 0.8s ease;
    overflow-y: auto;
  }
  .left-section h2 {
    text-align: center;
    color: #00796b;
    margin-bottom: 20px;
  }
  .input-group {
    margin-bottom: 20px;
  }
  label {
    font-weight: bold;
    color: #444;
    margin-bottom: 5px;
    display: block;
  }
  input,
  select {
    width: 100%;
    padding: 10px;
    font-size: 16px;
    border: 1px solid #ccc;
    border-radius: 10px;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
    transition: 0.3s;
  }
  input:focus,
  select:focus {
    border-color: #00796b;
    outline: none;
    box-shadow: 0 0 5px rgba(0, 150, 136, 0.3);
  }
  button {
    padding: 12px;
    background-color: #00796b;
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }
  button:hover {
    background-color: #004d40;
  }
  .right-section {
    flex: 1.1;
    margin-left: 40px;
    display: flex;
    flex-direction: column;
    background-color: #ffffffdd;
    border-radius: 20px;
    padding: 30px;
    box-shadow: 0 0 25px rgba(0, 0, 0, 0.1);
    animation: slideInRight 0.8s ease;
    overflow-y: auto;
  }
  .weather-info {
    margin-bottom: 25px;
  }
  .weather-info h3 {
    color: #00796b;
    margin-bottom: 10px;
  }
  .map {
    width: 100%;
    height: 280px;
    margin-bottom: 30px;
    border-radius: 15px;
    overflow: hidden;
  }
  iframe {
    width: 100%;
    height: 100%;
    border: none;
  }
  .outfit-avatar {
    display: flex;
    align-items: center;
    gap: 25px;
  }
  .outfit-avatar img {
    border-radius: 50%;
    width: 130px;
    height: 130px;
    object-fit: cover;
    border: 3px solid #00796b;
    box-shadow: 0 0 12px rgba(0, 150, 136, 0.5);
  }
  .outfit-details {
    font-size: 18px;
    color: #004d40;
    background: #a7ffeb88;
    padding: 20px;
    border-radius: 15px;
    flex-grow: 1;
    box-shadow: inset 0 0 10px #004d4022;
  }
  .error {
    color: red;
    margin-top: 15px;
    font-weight: bold;
    text-align: center;
  }
  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  @keyframes slideInLeft {
    from {
      transform: translateX(-60px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  @keyframes slideInRight {
    from {
      transform: translateX(60px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  @media (max-width: 900px) {
    body {
      flex-direction: column;
      height: auto;
      padding: 20px;
    }
    .container {
      flex-direction: column;
      padding: 0;
    }
    .left-section,
    .right-section {
      margin: 0 0 30px 0;
      width: 100%;
    }
  }
</style>
</head>
<body>
  <div class="container">
    <div class="left-section">
      <h2>AI Weather-Based Outfit Recommender</h2>
      <form method="post" novalidate>
        <div class="input-group">
          <label for="address">City or Address (e.g. Delhi, India):</label>
          <input
            type="text"
            name="address"
            id="address"
            placeholder="Enter city or full address"
            value="{{ address | default('') }}"
          />
        </div>
        <div class="input-group">
          <label for="gender">Select Gender:</label>
          <select name="gender" id="gender" required>
            <option value="male" {% if gender == 'male' %}selected{% endif %}>Male</option>
            <option value="female" {% if gender == 'female' %}selected{% endif %}>Female</option>
          </select>
        </div>
        <div class="input-group">
          <label for="party">Are you going to a party?</label>
          <select name="party" id="party" required>
            <option value="no" {% if party == 'no' %}selected{% endif %}>No</option>
            <option value="yes" {% if party == 'yes' %}selected{% endif %}>Yes</option>
          </select>
        </div>
        <button type="submit">Get Outfit Recommendation</button>
      </form>
      {% if error %}
      <div class="error">{{ error }}</div>
      {% endif %}
    </div>

    <div class="right-section">
      {% if weather %}
      <div class="weather-info">
        <h3>Weather in {{ location_name }}</h3>
        <p><b>Temperature:</b> {{ weather['main']['temp'] }}°C</p>
        <p><b>Weather:</b> {{ weather['weather'][0]['description'].title() }}</p>
        <p><b>Humidity:</b> {{ weather['main']['humidity'] }}%</p>
        <p><b>Wind Speed:</b> {{ weather['wind']['speed'] }} m/s</p>
        <p><b>Sunrise (IST):</b> {{ sunrise_ist }}</p>
        <p><b>Sunset (IST):</b> {{ sunset_ist }}</p>
      </div>

      <div class="map">
        <iframe
          src="https://maps.google.com/maps?q={{ lat }},{{ lon }}&z=12&output=embed"
          allowfullscreen
          loading="lazy"
        ></iframe>
      </div>

     <div class="outfit-details">
          {{ outfit_recommendation|safe }}
      </div>
      {% endif %}
    </div>
  </div>
</body>
</html>
'''

# -----------------------
# Flask Route
# -----------------------

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    weather = None
    outfit_recommendation = None
    avatar_url = None
    sunrise_ist = None
    sunset_ist = None
    location_name = None

    # For form fields to remember
    address = ""
    lat_input = ""
    lon_input = ""
    gender = "male"
    party = "no"

    if request.method == "POST":
        address = request.form.get("address", "").strip()
        lat_input = request.form.get("lat", "").strip()
        lon_input = request.form.get("lon", "").strip()
        gender = request.form.get("gender", "male").lower()
        party = request.form.get("party", "no").lower()

        # Validate gender and party
        if gender not in ("male", "female"):
            gender = "male"
        if party not in ("yes", "no"):
            party = "no"

        # Parse lat/lon
        lat = None
        lon = None
        try:
            if lat_input and lon_input:
                lat = parse_coordinates(lat_input)
                lon = parse_coordinates(lon_input)
            elif address:
                lat, lon = get_lat_lon(address)
                if lat is None or lon is None:
                    error = "Could not find coordinates for the address provided."
            else:
                error = "Please provide either address or latitude and longitude."
        except Exception as e:
            error = f"Error parsing coordinates: {str(e)}"

        if not error and lat is not None and lon is not None:
            # Use your OpenWeatherMap API key here
            # API_KEY = "e70fc322e766309fdd52f6543af57391"

            weather = get_weather_data(lat, lon, api_key)
            if weather is None:
                error = "Failed to retrieve weather data."

            if weather:
                sunrise_ist = convert_utc_to_ist(weather['sys']['sunrise'])
                sunset_ist = convert_utc_to_ist(weather['sys']['sunset'])
                location_name = weather.get('name', address) or f"{lat},{lon}"
                outfit_recommendation = recommend_outfit(weather, party == "yes")
                avatar_url = get_avatar_url(gender)

    return render_template_string(
        HTML_TEMPLATE,
        error=error,
        weather=weather,
        outfit_recommendation=outfit_recommendation,
        avatar_url=avatar_url,
        sunrise_ist=sunrise_ist,
        sunset_ist=sunset_ist,
        lat=lat if 'lat' in locals() else '',
        lon=lon if 'lon' in locals() else '',
        address=address,
        lat_input=lat_input,
        lon_input=lon_input,
        gender=gender,
        party=party,
        location_name=location_name,
    )


if __name__ == "__main__":
    app.run(debug=True)
