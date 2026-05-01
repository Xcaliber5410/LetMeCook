import os
from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import requests
from config import Config
from db import DatabaseManager

app = Flask(__name__)
app.secret_key = 'super_secret_cooked_key_for_flash_messages'

# Session Config
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Upload Config
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

API_KEY = Config.API_KEY
db = DatabaseManager('localhost', 'root', 'Omkar#140706', 'cooked_db')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Exception Handling concept
        try:
            hashed_pwd = generate_password_hash(password)
            user_id = db.execute_query(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)", 
                (username, hashed_pwd)
            )
            if user_id:
                session['user_id'] = user_id
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                flash('Username already exists.', 'error')
        except Exception as e:
            flash(f'Database error: {e}', 'error')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = db.fetch_one("SELECT * FROM users WHERE username = %s", (username,))
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    favorites = db.fetch_all("SELECT * FROM favorite_meals WHERE user_id = %s ORDER BY saved_at DESC", (user_id,))
    user_recipes = db.fetch_all("SELECT * FROM user_recipes WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    notes = db.fetch_all("SELECT * FROM meal_notes WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    
    return render_template('dashboard.html', favorites=favorites, user_recipes=user_recipes, notes=notes)

@app.route('/add_note', methods=['POST'])
def add_note():
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    title = request.form.get('title')
    notes = request.form.get('notes')
    db.execute_query(
        "INSERT INTO meal_notes (user_id, title, notes) VALUES (%s, %s, %s)",
        (session['user_id'], title, notes)
    )
    return redirect(url_for('dashboard'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        ingredients = request.form.get('ingredients')
        instructions = request.form.get('instructions')
        
        # File Handling Concept
        file = request.files.get('recipe_image')
        filename = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        db.execute_query(
            "INSERT INTO user_recipes (user_id, title, ingredients, instructions, image_filename) VALUES (%s, %s, %s, %s, %s)",
            (session['user_id'], title, ingredients, instructions, filename)
        )
        flash('Recipe successfully uploaded!', 'success')
        return redirect(url_for('upload'))
        
    return render_template('upload.html')

@app.route('/find', methods=['GET', 'POST'])
def findRecipe():
    if request.method == 'POST':
        ingredients = request.form.get('ingredients')
        
        # 1. Search Spoonacular API
        url = f'https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients}&apiKey={API_KEY}'
        response = requests.get(url)
        api_recipes = []
        if response.status_code == 200:
            api_recipes = response.json()

        # 2. Search Local User Recipes
        terms = [t.strip() for t in ingredients.split(',') if t.strip()]
        local_recipes = []
        if terms:
            conditions = []
            params = []
            for t in terms:
                conditions.append("(ingredients LIKE %s OR title LIKE %s)")
                params.extend([f"%{t}%", f"%{t}%"])
            query = "SELECT * FROM user_recipes WHERE " + " OR ".join(conditions)
            local_recipes = db.fetch_all(query, tuple(params))
            
        if not api_recipes and not local_recipes:
            error_message = 'Sorry, we found no recipes matching those ingredients.'
            return render_template('find.html', error_message=error_message)

        return render_template('find.html', recipes=api_recipes, local_recipes=local_recipes)

    return render_template('find.html')

@app.route('/local_recipe/<int:recipe_id>', methods=['GET'])
def local_recipe(recipe_id):
    recipe = db.fetch_one("SELECT * FROM user_recipes WHERE id = %s", (recipe_id,))
    if not recipe:
         return redirect(url_for('findRecipe'))
         
    author = db.fetch_one("SELECT username FROM users WHERE id = %s", (recipe['user_id'],))
    author_name = author['username'] if author else 'Community Member'
    
    return render_template('local_recipe.html', recipe=recipe, author=author_name)
    
@app.route('/recipe/<int:recipe_id>', methods=['GET'])
def recipe(recipe_id):
    url = f'https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={API_KEY}'
    response = requests.get(url)

    if response.status_code == 200:
        recipe_details = response.json()
        
        # Check if already favorited
        is_favorite = False
        if session.get('user_id'):
            fav = db.fetch_one("SELECT id FROM favorite_meals WHERE user_id = %s AND api_recipe_id = %s", (session['user_id'], recipe_id))
            if fav: is_favorite = True
            
        return render_template('recipe.html', recipe=recipe_details, is_favorite=is_favorite)

    error_message = 'Sorry, there was an error fetching that recipe. Please try again.'
    return render_template('find.html', error_message=error_message)

@app.route('/save_favorite', methods=['POST'])
def save_favorite():
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    api_recipe_id = request.form.get('api_recipe_id')
    recipe_title = request.form.get('recipe_title')
    recipe_image = request.form.get('recipe_image')
    
    db.execute_query(
        "INSERT INTO favorite_meals (user_id, api_recipe_id, recipe_title, recipe_image) VALUES (%s, %s, %s, %s)",
        (session['user_id'], api_recipe_id, recipe_title, recipe_image)
    )
    return redirect(url_for('recipe', recipe_id=api_recipe_id))

if __name__ == '__main__':
    app.run(debug=True)