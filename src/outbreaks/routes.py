from flask import Blueprint, render_template
from src.models import Outbreak

outbreaks_bp = Blueprint('outbreaks', __name__)

@outbreaks_bp.route('/outbreaks')
def outbreaks():
    outbreaks_data = Outbreak.query.order_by(Outbreak.date.desc()).all()
    return render_template('outbreaks.html', outbreaks=outbreaks_data)

@outbreaks_bp.route('/outbreaks/<int:outbreak_id>')
def outbreak_details(outbreak_id):
    outbreak = Outbreak.query.get_or_404(outbreak_id)
    return render_template('outbreak_details.html', outbreak=outbreak)