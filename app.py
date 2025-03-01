from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
from datetime import datetime

app = Flask(__name__)

# Configure MySQL Database (Replace with your actual XAMPP MySQL credentials)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/energy_forecast"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your_secret_key"


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    plant_name = db.Column(db.String(100), nullable=False)
    location_lat = db.Column(db.Float, nullable=False)
    location_long = db.Column(db.Float, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class FutureForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.String(50), nullable=False, unique=True)  # Store forecast date
    sunlight_intensity = db.Column(db.Float, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)

class SolarForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    sunlight_intensity = db.Column(db.Float, nullable=False)
    predicted_solar_energy = db.Column(db.Float, nullable=False)  # Prediction Output

class WindForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    predicted_wind_energy = db.Column(db.Float, nullable=False)  # Prediction Output


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Route to open login page first
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
    logout_user()  # Logs out the current user
    session.clear() 
    # flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

def fetch_weather_data(lat, lon):
    API_KEY = "11ce42b4689bce3362df94c0ab388127"
    URL = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(URL)
        response.raise_for_status()
        data = response.json()

        forecast_data = []
        for i in range(0, len(data["list"]), 8):  # Every 8th entry (~24 hours apart)
            entry = data["list"][i]
            date = entry["dt_txt"].split()[0]
            temperature = entry["main"]["temp"]
            sunlight_intensity = 100 - entry["clouds"]["all"]
            wind_speed = entry["wind"]["speed"]

            forecast_data.append({
                "date": date,
                "temperature": temperature,
                "sunlight_intensity": sunlight_intensity,
                "wind_speed": wind_speed
            })

        return forecast_data

    except requests.exceptions.RequestException as e:
        print("Error fetching weather data:", e)
        return None

@app.route("/predict", methods=["GET"])
@login_required
def predict_energy():
    lat = current_user.location_lat
    lon = current_user.location_long

    weather_data = fetch_weather_data(lat, lon)
    if not weather_data:
        return jsonify({"error": "Failed to fetch data"}), 500

    try:
        for data in weather_data:
            date = data["date"]
            temperature = data["temperature"]
            sunlight_intensity = data["sunlight_intensity"]
            wind_speed = data["wind_speed"]

            # Solar Energy Prediction
            solar_pred = solar_model.predict([[temperature, sunlight_intensity]])[0]

            # Wind Energy Prediction
            wind_pred = wind_model.predict([[temperature, wind_speed]])[0]

            # Store Solar Prediction
            existing_solar = SolarForecast.query.filter_by(user_id=current_user.id, date=date).first()
            if existing_solar is None:
                solar_entry = SolarForecast(
                    user_id=current_user.id,
                    date=date,
                    temperature=temperature,
                    sunlight_intensity=sunlight_intensity,
                    predicted_solar_energy=solar_pred
                )
                db.session.add(solar_entry)

            # Store Wind Prediction
            existing_wind = WindForecast.query.filter_by(user_id=current_user.id, date=date).first()
            if existing_wind is None:
                wind_entry = WindForecast(
                    user_id=current_user.id,
                    date=date,
                    temperature=temperature,
                    wind_speed=wind_speed,
                    predicted_wind_energy=wind_pred
                )
                db.session.add(wind_entry)

        db.session.commit()
        return jsonify({"message": "Predictions stored successfully"})

    except Exception as e:
        db.session.rollback()
        print("Database Commit Error:", e)
        return jsonify({"error": "Database error"}), 500


@app.route("/forecast", methods=["GET"])
@login_required
def forecast_energy():
    lat = current_user.location_lat
    lon = current_user.location_long

    predictions = fetch_weather_data(lat, lon)
    if not predictions:
        return jsonify({"error": "Failed to fetch data"}), 500

    try:
        for prediction in predictions:
            existing_entry = FutureForecast.query.filter_by(user_id=current_user.id, date=prediction["date"]).first()
            
            if existing_entry is None:
                forecast = FutureForecast(
                    user_id=current_user.id,
                    date=prediction["date"],
                    sunlight_intensity=prediction["sunlight_intensity"],
                    wind_speed=prediction["wind_speed"],
                    temperature=prediction["temperature"]
                )
                db.session.add(forecast)

        db.session.commit()
        print("Data committed to the database")  # Debugging
    except Exception as e:
        db.session.rollback()  # Rollback in case of failure
        print("Database Commit Error:", e)
        return jsonify({"error": "Database error"}), 500

    return jsonify(predictions)


@app.route('/dashboard')
@login_required
def dashboard():
    forecasts = FutureForecast.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', forecasts=forecasts, current_user=current_user)

# =========================== RUN FLASK SERVER =========================== #
if __name__ == "__main__":
    app.run(debug=True)
