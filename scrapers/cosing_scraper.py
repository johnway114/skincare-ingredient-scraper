#!/usr/bin/env python3
"""
CosIng (Cosmetic Ingredient Database) scraper for EU cosmetic ingredients.
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin
from .base_scraper import BaseScraper

class CosIngScraper(BaseScraper):
    def __init__(self, delay: float = 4.0):
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://single-market-economy.ec.europa.eu"
        self.search_url = f"{self.base_url}/sectors/cosmetics/cosmetic-ingredient-database_en"
        
    def search_products(self, category: str = "moisturizer", limit: int = 10) -> List[str]:
        """
        Search for cosmetic ingredients on CosIng database.
        This is an ingredient database, so we'll search for common skincare ingredients.
        """
        self.logger.info(f"Starting CosIng ingredient search, limit: {limit}")
        
        ingredient_urls = []
        
        # Common skincare ingredients to search for
        skincare_ingredients = [
            "hyaluronic acid", "retinol", "niacinamide", "salicylic acid",
            "glycerin", "ceramide", "peptide", "vitamin c", "vitamin e",
            "argan oil", "jojoba oil", "shea butter", "collagen",
            "aloe vera", "zinc oxide", "titanium dioxide"
        ][:limit]
        
        try:
            # Get the main search page first
            self.logger.info(f"Fetching: {self.search_url}")
            soup = self.get_page(self.search_url)
            
            if soup:
                
                # Look for ingredient search functionality or ingredient links
                # CosIng typically has a search form or ingredient listings
                ingredient_links = soup.find_all('a', href=True)
                
                for link in ingredient_links:
                    href = link.get('href', '')
                    if '/ingredient/' in href or '/cosmetic-ingredient/' in href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in ingredient_urls:
                            ingredient_urls.append(full_url)
                            if len(ingredient_urls) >= limit:
                                break
                
                # If no direct links found, try to construct search URLs
                if not ingredient_urls:
                    for ingredient in skincare_ingredients:
                        search_url = f"{self.base_url}/sectors/cosmetics/cosmetic-ingredient-database_en?search={ingredient.replace(' ', '+')}"
                        ingredient_urls.append(search_url)
                        if len(ingredient_urls) >= limit:
                            break
                            
        except Exception as e:
            self.logger.error(f"Error searching CosIng: {e}")
        
        self.logger.info(f"Found {len(ingredient_urls)} ingredient URLs")
        return ingredient_urls[:limit]
    
    def scrape_product_details(self, url: str) -> Optional[Dict]:
        """
        Scrape details from a CosIng ingredient page.
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
                'source': 'CosIng',
                'product_name': '',
                'brand': 'EU Commission',
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
                '.title',
                '[class*="name"]',
                '.main-title'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem and name_elem.get_text(strip=True):
                    product_data['product_name'] = name_elem.get_text(strip=True)
                    break
            
            # Extract ingredient properties/information
            ingredient_info = []
            
            # Look for ingredient functions, restrictions, etc.
            info_sections = soup.find_all(['div', 'section', 'table'])
            for section in info_sections:
                text = section.get_text(strip=True)
                if any(keyword in text.lower() for keyword in [
                    'function', 'restriction', 'cas', 'einecs', 'iupac', 
                    'chemical', 'cosmetic', 'safety'
                ]):
                    # Extract relevant information as pseudo-ingredients
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 3 and len(line) < 200:
                            ingredient_info.append(line)
            
            # If we found ingredient information, add it
            if ingredient_info:
                product_data['ingredients'] = ingredient_info[:50]  # Limit to 50 items
            else:
                # Add the ingredient name itself as the main ingredient
                if product_data['product_name']:
                    product_data['ingredients'] = [product_data['product_name']]
            
            # Try to extract safety/regulatory information
            safety_elements = soup.find_all(text=True)
            for elem in safety_elements:
                text = str(elem).lower()
                if any(term in text for term in ['restriction', 'prohibited', 'limited', 'safe']):
                    if 'restriction' in text or 'prohibited' in text:
                        product_data['hazard_score'] = 'Restricted'
                    elif 'safe' in text:
                        product_data['hazard_score'] = 'Safe'
                    break
            
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
        Scrape cosmetic ingredients from CosIng database.
        """
        self.logger.info(f"Starting CosIng scraping for {category} category, limit: {limit}")
        
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
        
        self.logger.info(f"Successfully scraped {len(scraped_ingredients)} ingredients from CosIng")
        return scraped_ingredients