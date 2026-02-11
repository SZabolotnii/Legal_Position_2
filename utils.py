import unicodedata
import json
import requests
import re
from bs4 import BeautifulSoup
from typing import Union, List, Dict, Optional

def clean_text(text: str) -> str:
    """Clean text from problematic characters."""
    if not text:
        return text

    replacements = {
        ''': "'", '`': "'", '´': "'", ''': "'", '"': '"', '"': '"',
        '–': '-', '—': '-', '…': '...',
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...',
        '\xa0': ' ', '\u0027': "'", '\u02BC': "'", '\u02B9': "'",
        '\u0301': "", '\u0060': "'", '\u00B4': "'"
    }

    try:
        text = unicodedata.normalize('NFKD', text)
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = ' '.join(text.split())
        text = ''.join(char for char in text
                      if not unicodedata.category(char).startswith('C'))
        return text
    except Exception as e:
        print(f"Error in clean_text: {str(e)}")
        return text

def extract_court_decision_text(url: str) -> str:
    """Extract text from court decision URL - специфічно для reyestr.court.gov.ua."""
    try:
        # Add headers and timeout for better reliability
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Помилка при завантаженні URL: {str(e)}")

    soup = BeautifulSoup(response.content, 'html.parser')

    unwanted_texts = [
        "Доступ до Реєстру здійснюється в тестовому (обмеженому) режимі.",
        "З метою упередження перешкоджанню стабільній роботі Реєстру"
    ]

    result = ""

    # Strategy 1: Look for textarea with id="txtdepository" (reyestr.court.gov.ua specific)
    txtdepository = soup.find('textarea', id='txtdepository')
    if txtdepository:
        # The textarea contains HTML content as text
        embedded_html = txtdepository.get_text()
        # Parse the embedded HTML
        embedded_soup = BeautifulSoup(embedded_html, 'html.parser')
        # Extract text from paragraphs
        paragraphs = []
        for p in embedded_soup.find_all('p'):
            p_text = p.get_text(separator=" ").strip()
            # Replace &nbsp; with spaces
            p_text = p_text.replace('\xa0', ' ').replace('&nbsp;', ' ')
            if p_text and len(p_text) > 10:  # Skip very short paragraphs
                paragraphs.append(p_text)
        if paragraphs:
            result = "\n\n".join(paragraphs)

    # Strategy 2: Try to find paragraphs directly (fallback)
    if not result or len(result) < 100:
        decision_text = []
        for paragraph in soup.find_all('p'):
            text = paragraph.get_text(separator="\n").strip()
            if not any(unwanted_text in text for unwanted_text in unwanted_texts):
                decision_text.append(text)
        result = "\n".join(decision_text).strip()

    # Strategy 3: If still nothing, try wordwrap div
    if not result or len(result) < 100:
        wordwrap = soup.find('div', class_='wordwrap')
        if wordwrap:
            result = wordwrap.get_text(separator="\n").strip()

    # Clean up the result
    if result:
        lines = result.split('\n')
        cleaned_lines = [
            line.strip() for line in lines
            if line.strip() and len(line.strip()) > 5
            and not any(unwanted in line for unwanted in unwanted_texts)
        ]
        result = '\n'.join(cleaned_lines)

    print(f"[DEBUG] Extracted {len(result)} characters from URL")

    if not result or len(result) < 100:
        raise Exception("Не вдалося витягти текст судового рішення з URL. Можливо, сторінка використовує JavaScript або структура змінилася.")

    return result

def parse_doc_ids(doc_ids: Union[List, str, None]) -> List[str]:
    """Parse document IDs from various input formats."""
    if doc_ids is None:
        return []
    if isinstance(doc_ids, list):
        return [str(id).strip('[]') for id in doc_ids]
    if isinstance(doc_ids, str):
        cleaned = doc_ids.strip('[]').replace(' ', '')
        if cleaned:
            return [id.strip() for id in cleaned.split(',')]
    return []

def get_links_html(doc_ids: Union[List, str, None]) -> str:
    """Generate HTML links for document IDs."""
    parsed_ids = parse_doc_ids(doc_ids)
    if not parsed_ids:
        return ""
    links = [f"[Рішення ВС: {doc_id}](https://reyestr.court.gov.ua/Review/{doc_id})"
             for doc_id in parsed_ids]
    return ", ".join(links)

def parse_lp_ids(lp_ids: Union[str, int, None]) -> List[str]:
    """Parse legal position IDs."""
    if lp_ids is None:
        return []
    if isinstance(lp_ids, (str, int)):
        cleaned = str(lp_ids).strip('[]').replace(' ', '')
        if cleaned:
            return [cleaned]
    return []

def get_links_html_lp(lp_ids: Union[str, int, None]) -> str:
    """Generate HTML links for legal position IDs."""
    parsed_ids = parse_lp_ids(lp_ids)
    if not parsed_ids:
        return ""
    links = [f"[ПП ВС: {lp_id}](https://lpd.court.gov.ua/home/search/{lp_id})"
             for lp_id in parsed_ids]
    return ", ".join(links)