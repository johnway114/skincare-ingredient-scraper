#!/usr/bin/env python3
"""
PCPC INCIpedia scraper for cosmetic ingredients database.
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin
from .base_scraper import BaseScraper

class PCPCINCIpediaScraper(BaseScraper):
    def __init__(self, delay: float = 3.0):
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://incipedia.personalcarecouncil.org"
        
    def search_products(self, category: str = "moisturizer", limit: int = 10) -> List[str]:
        """
        Search for INCI ingredients on PCPC INCIpedia database.
        """
        self.logger.info(f"Starting PCPC INCIpedia search, limit: {limit}")
        
        ingredient_urls = []
        
        try:
            # Get the main page first
            self.logger.info(f"Fetching: {self.base_url}")
            soup = self.get_page(self.base_url)
            
            if soup:
                
                # Look for ingredient links or search functionality
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True).lower()
                    
                    # Look for ingredient-related links
                    if any(pattern in href for pattern in [
                        '/ingredient/', '/inci/', '/search', '/browse'
                    ]) or any(keyword in text for keyword in [
                        'ingredient', 'search', 'browse', 'database'
                    ]):
                        full_url = urljoin(self.base_url, href)
                        if full_url not in ingredient_urls:
                            ingredient_urls.append(full_url)
                            if len(ingredient_urls) >= limit:
                                break
                
                # If no specific links found, try common ingredient searches
                if not ingredient_urls:
                    common_ingredients = [
                        "hyaluronic-acid", "retinol", "niacinamide", "salicylic-acid",
                        "glycerin", "ceramide", "peptide", "vitamin-c", "vitamin-e",
                        "aloe-vera", "zinc-oxide", "titanium-dioxide"
                    ][:limit]
                    
                    for ingredient in common_ingredients:
                        search_url = f"{self.base_url}/search?q={ingredient}"
                        ingredient_urls.append(search_url)
                        if len(ingredient_urls) >= limit:
                            break
                            
        except Exception as e:
            self.logger.error(f"Error searching PCPC INCIpedia: {e}")
        
        self.logger.info(f"Found {len(ingredient_urls)} ingredient URLs")
        return ingredient_urls[:limit]
    
    def scrape_product_details(self, url: str) -> Optional[Dict]:
        """
        Scrape details from a PCPC INCIpedia ingredient page.
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
                'source': 'PCPC INCIpedia',
                'product_name': '',
                'brand': 'Personal Care Products Council',
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
                '.inci-name',
                '.title',
                '[class*="name"]',
                '.page-title',
                '.ingredient-title'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem and name_elem.get_text(strip=True):
                    product_data['product_name'] = name_elem.get_text(strip=True)
                    break
            
            # Extract ingredient information and properties
            ingredient_info = []
            
            # Look for INCI information, functions, and properties
            info_sections = soup.find_all(['div', 'section', 'table', 'dl', 'p'])
            for section in info_sections:
                section_text = section.get_text().lower()
                
                # Check if this section contains relevant ingredient information
                if any(keyword in section_text for keyword in [
                    'inci', 'function', 'use', 'cas', 'einecs', 'chemical',
                    'formula', 'definition', 'description', 'category',
                    'cosmetic', 'personal care', 'safety', 'regulation'
                ]):
                    # Extract structured information
                    if section.name == 'table':
                        rows = section.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                key = cells[0].get_text(strip=True)
                                value = cells[1].get_text(strip=True)
                                if key and value and len(key) < 50 and len(value) < 200:
                                    ingredient_info.append(f"{key}: {value}")
                    
                    elif section.name == 'dl':
                        # Definition list
                        dts = section.find_all('dt')
                        dds = section.find_all('dd')
                        for dt, dd in zip(dts, dds):
                            term = dt.get_text(strip=True)
                            definition = dd.get_text(strip=True)
                            if term and definition:
                                ingredient_info.append(f"{term}: {definition}")
                    
                    else:
                        # Extract key phrases and sentences
                        text = section.get_text(strip=True)
                        sentences = text.split('.')
                        for sentence in sentences:
                            sentence = sentence.strip()
                            if sentence and len(sentence) > 10 and len(sentence) < 200:
                                if any(term in sentence.lower() for term in [
                                    'function', 'use', 'chemical', 'cas',
                                    'definition', 'category', 'safety'
                                ]):
                                    ingredient_info.append(sentence)
            
            # Look for additional ingredient lists or related information
            lists = soup.find_all(['ul', 'ol'])
            for ul in lists:
                items = ul.find_all('li')
                for item in items:
                    text = item.get_text(strip=True)
                    if text and len(text) > 5 and len(text) < 150:
                        ingredient_info.append(text)
            
            # Set ingredients
            if ingredient_info:
                product_data['ingredients'] = ingredient_info[:50]  # Limit to 50 items
            elif product_data['product_name']:
                product_data['ingredients'] = [product_data['product_name']]
            
            # Try to extract safety/regulatory information
            full_text = soup.get_text().lower()
            if any(term in full_text for term in ['restricted', 'prohibited', 'banned']):
                product_data['hazard_score'] = 'Restricted'
            elif any(term in full_text for term in ['safe', 'approved', 'permitted']):
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
        Scrape ingredients from PCPC INCIpedia database.
        """
        self.logger.info(f"Starting PCPC INCIpedia scraping for {category} category, limit: {limit}")
        
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
        
        self.logger.info(f"Successfully scraped {len(scraped_ingredients)} ingredients from PCPC INCIpedia")
        return scraped_ingredients