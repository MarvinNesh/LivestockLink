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
def extract_text_from_pdf(pdf_url):
    """Extracts text content from a PDF file."""
    try:
        response = requests.get(pdf_url, verify=False)
        response.raise_for_status()
        with io.BytesIO(response.content) as open_pdf_file:
            reader = PdfReader(open_pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
    except Exception as e:
        log.error(f"Error extracting text from PDF {pdf_url}: {e}", exc_info=True)
        return ""

def extract_text_from_html(html_url):
    """Extracts text content from an HTML page, trying multiple selectors."""
    try:
        response = requests.get(html_url, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        content_selectors = ['article', 'main', 'div.content', 'div.item-page']
        for selector in content_selectors:
            article_body = soup.select_one(selector)
            if article_body:
                return article_body.get_text(separator='\n', strip=True)
        return ""
    except Exception as e:
        log.error(f"Error extracting text from HTML {html_url}: {e}", exc_info=True)
        return ""
def scrape_outbreaks():
    """
    Scrapes the NDA website for outbreak news, extracts relevant information,
    and stores it in the Outbreak database model.
    """
    log.info("Starting outbreak scraping process.")
    url = "https://www.nda.gov.za/index.php/newsroom/media-release"
    try:
        log.info(f"Fetching URL: {url}")
        # Disable SSL verification for local development
        response = requests.get(url, verify=False)
        response.raise_for_status()
        log.info("Successfully fetched URL.")
    except requests.exceptions.RequestException as e:
        log.error(f"Error fetching the URL: {e}")
        return f"Error fetching the URL: {e}"

    soup = BeautifulSoup(response.content, 'html.parser')

    log.info("Looking for article links.")
    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))
    log.info(f"Found {len(pdf_links)} potential PDF article links.")

    keywords = [
        'outbreak', 'disease', 'foot and mouth', 
        'avian influenza', 'anthrax', 'rabies', 'brucellosis', 'fmd'
    ]