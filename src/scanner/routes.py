from flask import render_template
from flask_login import login_required
from . import scanner_bp

@scanner_bp.route('/scanner')
@login_required
def scanner():
    """Renders the symptom scanner page."""
    return render_template('scanner.html')