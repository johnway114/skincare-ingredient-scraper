#!/usr/bin/env python3
"""
SpecialChem INCI Database scraper for cosmetic ingredients.
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin
from .base_scraper import BaseScraper

class SpecialChemScraper(BaseScraper):
    def __init__(self, delay: float = 3.0):
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://www.specialchem.com"
        self.search_url = f"{self.base_url}/cosmetics/all-inci-ingredients"
        
    def search_products(self, category: str = "moisturizer", limit: int = 10) -> List[str]:
        """
        Search for INCI ingredients on SpecialChem database.
        """
        self.logger.info(f"Starting SpecialChem INCI search, limit: {limit}")
        
        ingredient_urls = []
        
        try:
            # Get the main INCI ingredients page
            self.logger.info(f"Fetching: {self.search_url}")
            soup = self.get_page(self.search_url)
            
            if soup:
                
                # Look for ingredient links
                ingredient_links = soup.find_all('a', href=True)
                
                for link in ingredient_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True).lower()
                    
                    # Look for ingredient-related links
                    if any(pattern in href for pattern in [
                        '/ingredient/', '/inci/', '/cosmetic-ingredient/', '/product/'
                    ]) or any(keyword in text for keyword in [
                        'acid', 'oil', 'extract', 'glycol', 'ester', 'alcohol', 
                        'oxide', 'butter', 'wax', 'vitamin'
                    ]):
                        full_url = urljoin(self.base_url, href)
                        if full_url not in ingredient_urls and 'specialchem.com' in full_url:
                            ingredient_urls.append(full_url)
                            if len(ingredient_urls) >= limit:
                                break
                
                # If no direct links found, try pagination or search
                if not ingredient_urls:
                    # Look for pagination or ingredient list
                    page_links = soup.find_all('a', href=True)
                    for link in page_links:
                        href = link.get('href', '')
                        if 'page=' in href or 'ingredients' in href:
                            full_url = urljoin(self.base_url, href)
                            ingredient_urls.append(full_url)
                            if len(ingredient_urls) >= limit:
                                break
                                
        except Exception as e:
            self.logger.error(f"Error searching SpecialChem: {e}")
        
        self.logger.info(f"Found {len(ingredient_urls)} ingredient URLs")
        return ingredient_urls[:limit]
    
    def scrape_product_details(self, url: str) -> Optional[Dict]:
        """
        Scrape details from a SpecialChem ingredient page.
        """
        try:
            self.logger.info(f"Fetching: {url}")
            soup = self.get_page(url)
            
            if not soup:
                self.logger.error(f"Failed to fetch {url}")
                return None
            
            # Extract ingredient information
            product_data = {
                'url': url,
                'source': 'SpecialChem',
                'product_name': '',
                'brand': 'SpecialChem',
                'price': '',
                'rating': '',
                'ingredients': [],
                'date_published': '',
                'hazard_score': '',
                'product_type': 'ingredient'
            }
            
            # Try to find ingredient name
            name_selectors = [
                'h1',
                '.ingredient-name',
                '.product-name',
                '.title',
                '[class*="name"]',
                '.page-title'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem and name_elem.get_text(strip=True):
                    product_data['product_name'] = name_elem.get_text(strip=True)
                    break
            
            # Extract ingredient properties and information
            ingredient_info = []
            
            # Look for technical specifications, functions, properties
            spec_sections = soup.find_all(['div', 'section', 'table', 'dl'])
            for section in spec_sections:
                # Check if this section contains ingredient information
                section_text = section.get_text().lower()
                if any(keyword in section_text for keyword in [
                    'function', 'property', 'application', 'cas', 'einecs',
                    'chemical', 'formula', 'molecular', 'specification',
                    'cosmetic', 'use', 'benefit'
                ]):
                    # Extract structured data
                    if section.name == 'table':
                        rows = section.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                key = cells[0].get_text(strip=True)
                                value = cells[1].get_text(strip=True)
                                if key and value and len(key) < 100 and len(value) < 200:
                                    ingredient_info.append(f"{key}: {value}")
                    else:
                        # Extract key information from text
                        lines = section.get_text().split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and len(line) > 5 and len(line) < 150:
                                if any(term in line.lower() for term in [
                                    'function:', 'use:', 'cas:', 'formula:', 
                                    'benefit:', 'application:', 'property:'
                                ]):
                                    ingredient_info.append(line)
            
            # Look for ingredient lists or related compounds
            ingredient_lists = soup.find_all(['ul', 'ol'])
            for ul in ingredient_lists:
                items = ul.find_all('li')
                for item in items:
                    text = item.get_text(strip=True)
                    if text and len(text) > 3 and len(text) < 100:
                        # Check if it looks like an ingredient name
                        if any(suffix in text.lower() for suffix in [
                            'acid', 'oil', 'extract', 'glycol', 'ester', 
                            'alcohol', 'oxide', 'butter', 'wax'
                        ]):
                            ingredient_info.append(text)
            
            # Set ingredients
            if ingredient_info:
                product_data['ingredients'] = ingredient_info[:50]  # Limit to 50 items
            elif product_data['product_name']:
                product_data['ingredients'] = [product_data['product_name']]
            
            # Try to extract safety information
            safety_text = soup.get_text().lower()
            if 'hazard' in safety_text or 'danger' in safety_text:
                product_data['hazard_score'] = 'Hazardous'
            elif 'safe' in safety_text or 'non-toxic' in safety_text:
                product_data['hazard_score'] = 'Safe'
            
            if not product_data['product_name']:
                self.logger.warning(f"No ingredient name found for {url}")
                return None
                
            self.logger.info(f"Scraped ingredient: {product_data['product_name']} ({len(product_data['ingredients'])} properties)")
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return None
    
    def scrape_products(self, category: str = "moisturizer", limit: int = 10) -> List[Dict]:
        """
        Scrape INCI ingredients from SpecialChem database.
        """
        self.logger.info(f"Starting SpecialChem scraping for {category} category, limit: {limit}")
        
        # Get ingredient URLs
        ingredient_urls = self.search_products(category, limit)
        
        if not ingredient_urls:
            self.logger.warning("No ingredient URLs found")
            return []
        
        scraped_ingredients = []
        
        for i, url in enumerate(ingredient_urls, 1):
            self.logger.info(f"Scraping ingredient {i}/{len(ingredient_urls)}")
            
            ingredient_data = self.scrape_product_details(url)
            if ingredient_data:
                scraped_ingredients.append(ingredient_data)
            
            # Rate limiting
            time.sleep(self.delay)
            
            # Progress break for large scrapes
            if i % 10 == 0:
                self.logger.info(f"Processed {i} ingredients, taking a short break...")
                time.sleep(5)
        
        self.logger.info(f"Successfully scraped {len(scraped_ingredients)} ingredients from SpecialChem")
        return scraped_ingredients