from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from src.scraper import scrape_outbreaks
import traceback

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/update-outbreaks')
@login_required
def update_outbreaks():
    try:
        message = scrape_outbreaks()
        flash(message, 'info')
    except Exception as e:
        print("--- TRACEBACK ---")
        traceback.print_exc()
        print("--- END TRACEBACK ---")
        flash(f"An unexpected error occurred: {e}. Check the console for details.", 'danger')
    return redirect(url_for('outbreaks.outbreaks'))