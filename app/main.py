
from flask import render_template, Blueprint

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('home.html')