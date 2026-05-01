from flask import Flask, render_template, redirect, request
import requests
from config import Config

app = Flask(__name__)
API_KEY = Config.API_KEY


# route for the index page of the website
@app.route('/')
def home():
    return render_template('index.html')


# route for the find recipe page
@app.route('/find', methods = ['GET', 'POST'])
def findRecipe():
    if request.method == "POST":

        ingredients = request.form.get('ingredients')

        url = f'https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients}&apiKey={API_KEY}'

        response = requests.get(url)

        if response.status_code == 200:
            recipes = response.json()
            return render_template('find.html', recipes = recipes)
        
        else:
            error_message = 'Sorry there was an error fetching recipes, please try again.'
            return render_template('find.html', error_message = error_message)
    
    return render_template("find.html")    


@app.route('/recipe/<int:recipe_id>')
def recipe(recipe_id):

    url = f'https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={API_KEY}'

    response = requests.get(url)

    if response.status_code == 200:
        recipe_details = response.json()
        return render_template('recipe.html', recipe = recipe_details)

    else:
        error_message = 'Sorry there was an error fetching recipes, please try again.'
        return render_template('find.html', error_message = error_message)
    
    


app.run(debug=True)