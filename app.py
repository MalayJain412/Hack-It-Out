from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import pickle
from datetime import datetime

# Load the trained ML models
solar_model = pickle.load(open("models/solar_model.pkl", "rb"))
wind_model = pickle.load(open("models/wind_model.pkl", "rb"))

app = Flask(__name__)

# Configure MySQL Database (Change credentials if needed)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/energy_forecast"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your_secret_key"

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# =================== DATABASE MODELS =================== #

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    plant_name = db.Column(db.String(100), nullable=False)
    location_lat = db.Column(db.Float, nullable=False)
    location_long = db.Column(db.Float, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class SolarForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    max_temperature = db.Column(db.Float, nullable=False)
    sunlight_intensity = db.Column(db.Float, nullable=False)
    predicted_solar_energy = db.Column(db.Float, nullable=False)

class WindForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    wind_direction = db.Column(db.Float, nullable=False)
    predicted_wind_energy = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =================== USER AUTHENTICATION =================== #

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        plant_name = request.form["plant_name"]
        location_lat = float(request.form["location_lat"])
        location_long = float(request.form["location_long"])
        city = request.form["city"]
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        
        user = User(
            plant_name=plant_name,
            location_lat=location_lat,
            location_long=location_long,
            city=city,
            username=username,
            password=password
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials!"
    
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

# =================== FETCH WEATHER DATA FROM API =================== #

def fetch_weather_data(lat, lon):
    API_KEY = "11ce42b4689bce3362df94c0ab388127"
    URL = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(URL)
        response.raise_for_status()
        data = response.json()

        forecast_data = []
        for entry in data["list"]:
            date = datetime.strptime(entry["dt_txt"], "%Y-%m-%d %H:%M:%S")
            temperature = entry["main"]["temp"]
            max_temperature = entry["main"]["temp_max"]
            sunlight_intensity = 100 - entry["clouds"]["all"]
            wind_speed = entry["wind"]["speed"]
            wind_direction = entry["wind"]["deg"]

            forecast_data.append({
                "date": date,
                "temperature": temperature,
                "max_temperature": max_temperature,
                "sunlight_intensity": sunlight_intensity,
                "wind_speed": wind_speed,
                "wind_direction": wind_direction
            })
        print(forecast_data)

        return forecast_data

    except requests.exceptions.RequestException as e:
        print("Error fetching weather data:", e)
        return None

# =================== MAKE PREDICTIONS & STORE IN DATABASE =================== #

@app.route("/predict", methods=["GET"])
@login_required
def predict_energy():
    try:
        lat = current_user.location_lat
        lon = current_user.location_long
        print(f"User ID: {current_user.id}, Location: {lat}, {lon}")  # Debugging log

        # Fetch weather data
        weather_data = fetch_weather_data(lat, lon)
        if not weather_data or not isinstance(weather_data, list):
            print("Error: Weather data is empty or incorrect format.")
            return jsonify({"error": "Failed to fetch weather data"}), 500

        solar_entries = []
        wind_entries = []

        for data in weather_data:
            try:
                date = data["date"]
                temperature = data.get("temperature")
                max_temperature = data.get("max_temperature")
                sunlight_intensity = data.get("sunlight_intensity")
                wind_speed = data.get("wind_speed")
                wind_direction = data.get("wind_direction")

                hour = date.hour
                day = date.day
                month = date.month

                if None in [temperature, max_temperature, sunlight_intensity, wind_speed, wind_direction]:
                    print(f"Skipping invalid data: {data}")
                    continue  # Skip invalid rows

                # Make Predictions
                # solar_pred = solar_model.predict([[temperature, max_temperature, sunlight_intensity]])[0]
                wind_pred = wind_model.predict([[wind_speed, wind_direction]])[0]
                print(f"Predicted Wind: {wind_pred}")

                # Store Predictions
                # solar_entries.append(SolarForecast(
                #     user_id=current_user.id, date=date, temperature=temperature,
                #     max_temperature=max_temperature, sunlight_intensity=sunlight_intensity,
                #     predicted_solar_energy=solar_pred
                # ))

                wind_entries.append(WindForecast(
                    user_id=current_user.id, date=date, wind_speed=wind_speed,
                    wind_direction=wind_direction, predicted_wind_energy=wind_pred
                ))

            except Exception as e:
                print("Error processing weather entry:", e)

        # Bulk insert into the database
        if solar_entries:
            db.session.bulk_save_objects(solar_entries)
        if wind_entries:
            db.session.bulk_save_objects(wind_entries)
        
        db.session.commit()
        return jsonify({"message": "Predictions stored successfully"})

    except Exception as e:
        db.session.rollback()
        print("Prediction API Error:", str(e))  # Log error
        return jsonify({"error": str(e)}), 500


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# =================== RUN FLASK APP =================== #
if __name__ == "__main__":
    # db.create_all()  # Ensure tables are created
    app.run(debug=True)
