from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from google import genai 
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-hackathon-key' # Required for secure logins
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' # Creates a local DB file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 👉 1. PUT YOUR NEW API KEY HERE
client = genai.Client(api_key="AIzaSyDPX7LyYNmSngWRBUifGwwFClGwp0MesSY")

# --- INITIALIZE DATABASE & LOGIN MANAGER ---
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirects here if they aren't logged in

# --- DATABASE MODEL ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    
    # Track their health data in their profile!
    age = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    target_calories = db.Column(db.Integer, nullable=True)
    bmi = db.Column(db.Float, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create the database file if it doesn't exist
with app.app_context():
    db.create_all()

# --- MATH CALCULATORS (Kept exactly the same) ---
def calculate_bmr(gender, weight, height, age):
    if gender.lower() == "male": return 10 * weight + 6.25 * height - 5 * age + 5
    else: return 10 * weight + 6.25 * height - 5 * age - 161

def daily_calorie_needs(bmr, activity_level):
    factors = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
    return bmr * factors.get(activity_level, 1.2)

def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 1)

def get_health_risk(bmi, age):
    if bmi < 18.5:
        if age >= 55: return {"category": "Underweight", "risk": "High risk of osteoporosis, muscle wasting, and weakened immunity at this age.", "color": "#ef4444"}
        else: return {"category": "Underweight", "risk": "Increased risk of nutritional deficiencies, anemia, and weakened immunity.", "color": "#f59e0b"}
    elif 18.5 <= bmi < 24.9:
        return {"category": "Normal Weight", "risk": "Low risk of lifestyle diseases. Keep up the good work and maintain active habits!", "color": "#10b981"}
    elif 25 <= bmi < 29.9:
        if age >= 40: return {"category": "Overweight", "risk": "Moderate-to-high risk of high blood pressure, elevated cholesterol, and early joint strain.", "color": "#f59e0b"}
        else: return {"category": "Overweight", "risk": "Moderate risk. Focus on preventing further weight gain to protect your future metabolic health.", "color": "#f59e0b"}
    else:
        if age >= 40: return {"category": "Obese", "risk": "Severe risk of Cardiovascular Disease, Type 2 Diabetes, sleep apnea, and osteoarthritis.", "color": "#ef4444"}
        else: return {"category": "Obese", "risk": "High risk of early-onset Type 2 Diabetes and cardiovascular issues. Early lifestyle intervention is highly recommended.", "color": "#ef4444"}

def generate_diet_plan(target_calories, preference):
    ratio = target_calories / 2000.0
    if preference == "vegan":
        return {
            "breakfast": [{"food": "Oats with Almond Milk & Chia", "calories": int(250*ratio), "protein": int(8*ratio), "carbs": int(40*ratio), "fat": int(7*ratio)}, {"food": "Tofu Scramble", "calories": int(150*ratio), "protein": int(15*ratio), "carbs": int(5*ratio), "fat": int(9*ratio)}],
            "lunch": [{"food": "Quinoa Bowl with Veggies", "calories": int(250*ratio), "protein": int(10*ratio), "carbs": int(45*ratio), "fat": int(5*ratio)}, {"food": "Lentil Soup", "calories": int(150*ratio), "protein": int(12*ratio), "carbs": int(22*ratio), "fat": int(2*ratio)}],
            "snacks": [{"food": "Roasted Chana", "calories": int(120*ratio), "protein": int(7*ratio), "carbs": int(20*ratio), "fat": int(2*ratio)}],
            "dinner": [{"food": "Vegan Chickpea Curry", "calories": int(220*ratio), "protein": int(12*ratio), "carbs": int(30*ratio), "fat": int(6*ratio)}, {"food": "Brown Rice", "calories": int(110*ratio), "protein": int(3*ratio), "carbs": int(22*ratio), "fat": int(1*ratio)}]
        }
    elif preference == "non_veg":
        return {
            "breakfast": [{"food": "Masala Omelette (3 Eggs)", "calories": int(240*ratio), "protein": int(18*ratio), "carbs": int(4*ratio), "fat": int(16*ratio)}, {"food": "Whole Wheat Toast", "calories": int(150*ratio), "protein": int(6*ratio), "carbs": int(26*ratio), "fat": int(2*ratio)}],
            "lunch": [{"food": "Grilled Chicken Breast", "calories": int(240*ratio), "protein": int(46*ratio), "carbs": int(0*ratio), "fat": int(5*ratio)}, {"food": "Brown Rice", "calories": int(150*ratio), "protein": int(4*ratio), "carbs": int(30*ratio), "fat": int(1*ratio)}],
            "snacks": [{"food": "Boiled Eggs (2)", "calories": int(140*ratio), "protein": int(12*ratio), "carbs": int(1*ratio), "fat": int(10*ratio)}],
            "dinner": [{"food": "Baked Fish", "calories": int(200*ratio), "protein": int(25*ratio), "carbs": int(6*ratio), "fat": int(8*ratio)}, {"food": "Multigrain Roti", "calories": int(160*ratio), "protein": int(6*ratio), "carbs": int(28*ratio), "fat": int(2*ratio)}]
        }
    else: 
        return {
            "breakfast": [{"food": "Poha with Veggies", "calories": int(250*ratio), "protein": int(6*ratio), "carbs": int(45*ratio), "fat": int(7*ratio)}, {"food": "Moong Usal", "calories": int(140*ratio), "protein": int(10*ratio), "carbs": int(22*ratio), "fat": int(2*ratio)}],
            "lunch": [{"food": "Multigrain Roti", "calories": int(200*ratio), "protein": int(6*ratio), "carbs": int(34*ratio), "fat": int(2*ratio)}, {"food": "Dal Tadka", "calories": int(150*ratio), "protein": int(9*ratio), "carbs": int(20*ratio), "fat": int(5*ratio)}],
            "snacks": [{"food": "Roasted Chana", "calories": int(120*ratio), "protein": int(7*ratio), "carbs": int(20*ratio), "fat": int(2*ratio)}],
            "dinner": [{"food": "Vegetable Khichdi", "calories": int(220*ratio), "protein": int(8*ratio), "carbs": int(35*ratio), "fat": int(4*ratio)}, {"food": "Cucumber Salad", "calories": int(30*ratio), "protein": int(1*ratio), "carbs": int(6*ratio), "fat": int(0*ratio)}]
        }

# --- AUTHENTICATION ROUTES ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user already exists
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify({"error": "Username already exists!"}), 400
            
        # Hash the password and save to database
        new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()
        
        # 👉 CHANGED: Removed auto-login and changed the redirect to 'login'
        return jsonify({"success": "Account created successfully! Please log in.", "redirect": url_for('login')})
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return jsonify({"success": "Login successful!", "redirect": url_for('home')})
        else:
            return jsonify({"error": "Invalid username or password."}), 401
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/community')
@login_required
def community():
    # 1. FETCH DATA: Ask the database for every single user
    all_users = User.query.all()
    
    # 2. DISPLAY DATA: Send that list to a new HTML page called 'community.html'
    return render_template('community.html', users=all_users)

@app.route('/profile')
@login_required
def profile():
    # Pass the logged-in user's data to the profile template
    return render_template('profile.html', user=current_user)

# --- CORE APP ROUTES ---

@app.route('/')
@login_required # 👉 Forces users to log in before seeing the form!
def home():
    return render_template('index.html', user=current_user)

@app.route('/result')
@login_required
def result():
    return render_template('result.html')

@app.route('/risk')
@login_required
def risk():
    return render_template('risk.html')

@app.route('/recommend', methods=['POST'])
@login_required
def recommend():
    data = request.json
    try:
        age, weight, height = int(data["age"]), float(data["weight"]), float(data["height"])
        if not (14 <= age <= 100) or not (35 <= weight <= 250) or not (120 <= height <= 250):
            return jsonify({"error": "Please enter valid values."}), 400
    except ValueError:
        return jsonify({"error": "Invalid data format."}), 400

    bmr = calculate_bmr(data["gender"], weight, height, age)
    calories = daily_calorie_needs(bmr, data["activity_level"])
    bmi = calculate_bmi(weight, height)
    health_risk = get_health_risk(bmi, age)

    if data["goal"] == "weight_loss": calories -= 300
    elif data["goal"] == "weight_gain": calories += 300

    # 👉 SAVE THEIR LATEST STATS TO THEIR DATABASE PROFILE!
    current_user.age = age
    current_user.weight = weight
    current_user.height = height
    current_user.target_calories = calories
    current_user.bmi = bmi
    db.session.commit()

    diet = generate_diet_plan(calories, data.get("preference", "veg"))

    return jsonify({
        "bmr": round(bmr, 2),
        "daily_calories": round(calories, 2),
        "bmi": bmi,                  
        "health_risk": health_risk,  
        "diet_plan": diet
    })

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message")
    calories = data.get("calories")
    goal = data.get("goal")
    bmi = data.get("bmi", "Unknown")
    risk = data.get("risk", "Unknown")

    system_instruction = f"""
    You are an expert AI Nutrition Coach inside a diet app.
    The user has a daily target of {calories} kcal and their goal is to {goal}.
    Their current BMI is {bmi}, which puts them in the '{risk}' category.
    Keep answers concise, encouraging, and related to fitness and diet.
    User's message: {user_message}
    """
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=system_instruction)
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"reply": "API Error: Please check your terminal for details."}), 500

if __name__ == "__main__":
    app.run(debug=True)