import io
import re
import logging
from urllib.parse import urljoin
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from .extensions import db
from .models import Outbreak

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
def parse_date(date_str):
    """Parse date string like '27 February 2025' to datetime object."""
    try:
        date_obj = datetime.strptime(date_str, '%d %B %Y')
        return date_obj
    except ValueError:
        try:
            date_obj = datetime.strptime(date_str, '%d %b %Y')
            return date_obj
        except ValueError:
            log.warning(f"Could not parse date: {date_str}")
            return None
