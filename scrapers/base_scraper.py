import time
import logging
import pandas as pd
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import requests
from bs4 import BeautifulSoup


class BaseScraper(ABC):
    """Base class for all scrapers with common functionality"""
    
    def __init__(self, delay: float = 2.0, use_selenium: bool = False):
        self.delay = delay
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.driver = None
        self.ua = UserAgent()
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/{self.__class__.__name__}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def setup_selenium(self):
        """Setup Selenium WebDriver with appropriate options"""
        if not self.driver:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'--user-agent={self.ua.random}')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            self.driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=options
            )
    
    def setup_session(self):
        """Setup requests session with headers"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch page content using requests or selenium"""
        self.logger.info(f"Fetching: {url}")
        
        if self.use_selenium:
            if not self.driver:
                self.setup_selenium()
            
            self.driver.get(url)
            time.sleep(self.delay)
            return BeautifulSoup(self.driver.page_source, 'html.parser')
        else:
            if not self.session.headers.get('User-Agent'):
                self.setup_session()
            
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                time.sleep(self.delay)
                return BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                self.logger.error(f"Error fetching {url}: {e}")
                return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        return " ".join(text.strip().split())
    
    def parse_ingredients(self, ingredients_text: str) -> List[str]:
        """Parse ingredients from text into list"""
        if not ingredients_text:
            return []
        
        # Clean up common marketing text patterns first
        clean_text = ingredients_text
        
        # Remove common marketing phrases
        marketing_patterns = [
            r'EWG Verified.*?mark',
            r'meaning that.*?ingredients',
            r'including fragrance.*?scientists',
            r'At the time of verification.*?concerns',
            r'Click on an ingredient.*?information',
            r'CONCERNS.*?INGREDIENT',
            r'EWG has reviewed.*?formulations',
            r'Visit the ingredient page.*?more',
            r'LEARN MORE.*?INGREDIENT',
            r'Unacceptable List.*?transparency',
            r'full transparency.*?fragrance'
        ]
        
        for pattern in marketing_patterns:
            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE | re.DOTALL)
        
        # Look for actual ingredient names (usually in CAPS or Title Case)
        # Common ingredient patterns
        ingredient_patterns = [
            r'\b[A-Z][A-Z0-9\-\s]+(?:\([^)]+\))?(?:\s+[A-Z]+)*\b',  # All caps ingredients like "SODIUM CHLORIDE" or "C13-15 ALKANE"
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+\([^)]+\))?\b',  # Title case like "Sodium Chloride"
        ]
        
        found_ingredients = []
        for pattern in ingredient_patterns:
            matches = re.findall(pattern, clean_text)
            for match in matches:
                # Filter out common non-ingredient words but be less aggressive
                match_lower = match.lower()
                if (len(match) > 2 and  # Allow shorter ingredients
                    not any(bad_word in match_lower for bad_word in 
                           ['the', 'and', 'this', 'that', 'with', 'from', 'click', 'learn', 'more', 'about', 'visit', 'page']) and
                    # Only filter out if it's clearly not an ingredient
                    not (any(bad_phrase in match_lower for bad_phrase in 
                            ['unacceptable list', 'concerns however', 'formulation transparency']) or
                         match_lower in ['unacceptable', 'however', 'concerns', 'click', 'learn', 'more', 'about', 'ewg', 'verified'])):
                    found_ingredients.append(self.clean_text(match))
        
        if found_ingredients:
            # Remove duplicates while preserving order
            seen = set()
            unique_ingredients = []
            for ing in found_ingredients:
                if ing.lower() not in seen:
                    seen.add(ing.lower())
                    unique_ingredients.append(ing)
            return unique_ingredients
        
        # Fallback to original comma-separated parsing
        separators = [',', ';', '•', '|']
        
        for sep in separators:
            if sep in clean_text:
                ingredients = [self.clean_text(ing.strip()) for ing in clean_text.split(sep)]
                # Filter out obviously non-ingredient items
                filtered_ingredients = []
                for ing in ingredients:
                    if (ing and len(ing) > 2 and 
                        not any(bad_phrase in ing.lower() for bad_phrase in 
                               ['click here', 'learn more', 'visit', 'ewg', 'concerns', 'however'])):
                        filtered_ingredients.append(ing)
                return filtered_ingredients
        
        # If no separator found, return as single ingredient if it looks valid
        if (clean_text and len(clean_text) > 3 and 
            not any(bad_phrase in clean_text.lower() for bad_phrase in 
                   ['click here', 'learn more', 'visit', 'ewg verified'])):
            return [self.clean_text(clean_text)]
        
        return []
    
    @abstractmethod
    def scrape_products(self, limit: Optional[int] = None) -> List[Dict]:
        """Main scraping method to be implemented by each scraper"""
        pass
    
    def save_data(self, data: List[Dict], filename: str):
        """Save scraped data to CSV and JSON"""
        if not data:
            self.logger.warning("No data to save")
            return
            
        df = pd.DataFrame(data)
        
        # Save as CSV
        csv_path = f"data/{filename}.csv"
        df.to_csv(csv_path, index=False)
        self.logger.info(f"Saved {len(data)} records to {csv_path}")
        
        # Save as JSON
        json_path = f"data/{filename}.json"
        df.to_json(json_path, orient='records', indent=2)
        self.logger.info(f"Saved {len(data)} records to {json_path}")
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        if self.session:
            self.session.close()