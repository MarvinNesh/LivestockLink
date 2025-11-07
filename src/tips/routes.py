from flask import Blueprint, render_template, request
from ..tips_data import tips_data

tips_bp = Blueprint('tips', __name__)

@tips_bp.route('/tips')
def tips():
    """
    Renders the main tips page, allowing users to select an animal.
    """
    animals = tips_data.keys()
    return render_template('tips.html', animals=animals, tips_data=tips_data)

@tips_bp.route('/tips/<animal>')
def tip_details(animal):
    """
    Renders the detailed tips for a specific animal.
    """
    tip = tips_data.get(animal)
    if not tip:
        # Handle cases where the animal is not found
        return render_template('tips.html', error="Animal not found.", animals=tips_data.keys(), tips_data=tips_data)
    return render_template('tip_details.html', title=tip['title'], tips=tip['tips'])