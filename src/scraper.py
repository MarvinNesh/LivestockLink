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
        # Handle full month names
        date_obj = datetime.strptime(date_str, '%d %B %Y')
        return date_obj
    except ValueError:
        try:
            # Handle abbreviated month names if needed
            date_obj = datetime.strptime(date_str, '%d %b %Y')
            return date_obj
        except ValueError:
            log.warning(f"Could not parse date: {date_str}")
            return None

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

  
    
   
    cutoff_year = 2024
    cutoff_date = datetime(cutoff_year, 1, 1)

    # Get the latest date in DB if exists, else use cutoff
    latest_db_date = None
    try:
        latest_outbreak = db.session.query(Outbreak).order_by(Outbreak.date.desc()).first()
        if latest_outbreak:
            latest_db_date = parse_date(latest_outbreak.date)
            if latest_db_date:
                log.info(f"Latest date in DB: {latest_outbreak.date}")
                cutoff_date = max(cutoff_date, latest_db_date)
            else:
                log.info("Using 2024 cutoff since DB dates could not be parsed.")
    except Exception as e:
        log.error(f"Error querying latest date: {e}")
        log.info("Using 2024 cutoff.")

    articles_found = False
    
    log.info("Looking for article links.")
    # Updated selector: Find all <a> tags that link to PDFs in media releases
    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))
    log.info(f"Found {len(pdf_links)} potential PDF article links.")

    keywords = ['outbreak', 'disease', 'foot and mouth', 'avian influenza', 'anthrax', 'rabies', 'brucellosis', 'fmd']

    for i, a_element in enumerate(pdf_links):
        log.info(f"Processing link {i+1}...")
        try:
            title_text = a_element.get_text(strip=True)
            
            # Updated regex: No brackets, "DD Month YYYY: Title"
            match = re.match(r'(\d{1,2} \w+ \d{4}): (.*)', title_text)
            if not match:
                log.info(f"Skipping link {i+1}: Invalid title format - {title_text[:50]}...")
                continue
            
            date_str = match.group(1)
            title = match.group(2)
            
            date_obj = parse_date(date_str)
            if not date_obj or date_obj < cutoff_date:
                log.info(f"Skipping link {i+1}: Date {date_str} is before cutoff {cutoff_date.date()}")
                continue
            
            if not any(keyword in title.lower() for keyword in keywords):
                log.info(f"Skipping link {i+1}: No relevant keywords in title - {title[:50]}...")
                continue

            link = urljoin(url, a_element['href'])
            
            content = extract_text_from_pdf(link)

            existing_outbreak = Outbreak.query.filter_by(url=link).first()
            if not existing_outbreak:
                new_outbreak = Outbreak(
                    title=title,
                    date=date_str,
                    content=content,
                    url=link
                )
                db.session.add(new_outbreak)
                articles_found = True
                log.info(f"Added outbreak: {title[:50]}...")
            else:
                log.info(f"Skipping link {i+1}: Already exists in DB")
        except Exception as e:
            log.error(f"An error occurred while processing link {i+1}: {e}", exc_info=True)
            continue

    if articles_found:
        log.info("Committing new outbreaks to the database.")
        try:
            db.session.commit()
            return "Outbreaks updated successfully!"
        except Exception as e:
            db.session.rollback()
            return f"Error saving outbreaks to database: {e}"
    else:
        log.info("No new outbreak articles were found to add to the database.")
        return "No new outbreak articles found."

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