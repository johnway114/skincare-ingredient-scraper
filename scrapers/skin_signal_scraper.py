#!/usr/bin/env python3
"""
Skin Signal scraper for skincare products and ingredient analysis.
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin
from .base_scraper import BaseScraper

class SkinSignalScraper(BaseScraper):
    def __init__(self, delay: float = 3.0):
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://www.skinsignal.com"
        
    def search_products(self, category: str = "moisturizer", limit: int = 10) -> List[str]:
        """
        Search for skincare products on Skin Signal.
        """
        self.logger.info(f"Starting Skin Signal search for {category}, limit: {limit}")
        
        product_urls = []
        
        # Category-specific search terms
        search_terms = {
            'moisturizer': ['moisturizer', 'cream', 'lotion', 'balm'],
            'cleanser': ['cleanser', 'cleansing', 'wash', 'foam']
        }
        
        terms = search_terms.get(category, ['moisturizer', 'cleanser'])
        
        try:
            # Try different approaches to find products
            search_urls = [
                f"{self.base_url}/products",
                f"{self.base_url}/skincare",
                f"{self.base_url}/ingredients",
                f"{self.base_url}"
            ]
            
            for search_url in search_urls:
                self.logger.info(f"Fetching: {search_url}")
                soup = self.get_page(search_url)
                
                if soup:
                    
                    # Look for product links
                    links = soup.find_all('a', href=True)
                    
                    for link in links:
                        href = link.get('href', '')
                        text = link.get_text(strip=True).lower()
                        
                        # Look for product-related links
                        if any(pattern in href for pattern in [
                            '/product/', '/review/', '/ingredient/', '/brand/'
                        ]):
                            full_url = urljoin(self.base_url, href)
                            if full_url not in product_urls and 'skinsignal.com' in full_url:
                                product_urls.append(full_url)
                                
                        # Also check text content for relevant products
                        elif any(term in text for term in terms):
                            if href and not href.startswith('#'):
                                full_url = urljoin(self.base_url, href)
                                if full_url not in product_urls and 'skinsignal.com' in full_url:
                                    product_urls.append(full_url)
                        
                        if len(product_urls) >= limit:
                            break
                
                if len(product_urls) >= limit:
                    break
                    
                # Rate limiting between requests
                time.sleep(self.delay)
            
            # If still no products found, try search functionality
            if not product_urls:
                for term in terms[:3]:  # Try first 3 terms
                    search_url = f"{self.base_url}/search?q={term}"
                    product_urls.append(search_url)
                    if len(product_urls) >= limit:
                        break
                        
        except Exception as e:
            self.logger.error(f"Error searching Skin Signal: {e}")
        
        self.logger.info(f"Found {len(product_urls)} product URLs")
        return product_urls[:limit]
    
    def scrape_product_details(self, url: str) -> Optional[Dict]:
        """
        Scrape details from a Skin Signal product page.
        """
        try:
            self.logger.info(f"Fetching: {url}")
            soup = self.get_page(url)
            
            if not soup:
                self.logger.error(f"Failed to fetch {url}")
                return None
            
            # Extract product information
            product_data = {
                'url': url,
                'source': 'Skin Signal',
                'product_name': '',
                'brand': '',
                'price': '',
                'rating': '',
                'ingredients': [],
                'date_published': '',
                'hazard_score': '',
                'product_type': 'skincare'
            }
            
            # Try to find product name
            name_selectors = [
                'h1',
                '.product-name',
                '.product-title',
                '.title',
                '[class*="name"]',
                '.page-title'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem and name_elem.get_text(strip=True):
                    product_data['product_name'] = name_elem.get_text(strip=True)
                    break
            
            # Try to find brand
            brand_selectors = [
                '.brand',
                '.brand-name',
                '[class*="brand"]',
                '.manufacturer'
            ]
            
            for selector in brand_selectors:
                brand_elem = soup.select_one(selector)
                if brand_elem and brand_elem.get_text(strip=True):
                    product_data['brand'] = brand_elem.get_text(strip=True)
                    break
            
            # Try to find price
            price_selectors = [
                '.price',
                '[class*="price"]',
                '.cost',
                '[data-price]'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if '$' in price_text or '£' in price_text or '€' in price_text:
                        product_data['price'] = price_text
                        break
            
            # Try to find rating
            rating_selectors = [
                '.rating',
                '[class*="rating"]',
                '.score',
                '[class*="score"]',
                '.stars'
            ]
            
            for selector in rating_selectors:
                rating_elem = soup.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    if any(char.isdigit() for char in rating_text):
                        product_data['rating'] = rating_text
                        break
            
            # Extract ingredients
            ingredients = []
            
            # Look for ingredient lists
            ingredient_selectors = [
                '.ingredients',
                '[class*="ingredient"]',
                '.inci',
                '[class*="inci"]',
                '.components',
                '.composition'
            ]
            
            for selector in ingredient_selectors:
                ingredient_section = soup.select_one(selector)
                if ingredient_section:
                    # Try different ways to extract ingredients
                    ingredient_list = ingredient_section.find('ul')
                    if ingredient_list:
                        items = ingredient_list.find_all('li')
                        for item in items:
                            ingredient = item.get_text(strip=True)
                            if ingredient and len(ingredient) > 2:
                                ingredients.append(ingredient)
                    else:
                        # Try comma-separated or line-separated ingredients
                        text = ingredient_section.get_text()
                        if ',' in text:
                            parts = text.split(',')
                            for part in parts:
                                ingredient = part.strip()
                                if ingredient and len(ingredient) > 2:
                                    ingredients.append(ingredient)
                        else:
                            lines = text.split('\n')
                            for line in lines:
                                ingredient = line.strip()
                                if ingredient and len(ingredient) > 2 and not ingredient.lower().startswith('ingredient'):
                                    ingredients.append(ingredient)
                    break
            
            # If no structured ingredients found, look for ingredient information in text
            if not ingredients:
                text_content = soup.get_text()
                if 'ingredient' in text_content.lower():
                    paragraphs = soup.find_all('p')
                    for p in paragraphs:
                        text = p.get_text()
                        if 'ingredient' in text.lower():
                            # Extract potential ingredients from this paragraph
                            sentences = text.split('.')
                            for sentence in sentences:
                                if 'ingredient' in sentence.lower():
                                    # Look for ingredient names in the sentence
                                    words = sentence.split()
                                    for word in words:
                                        word = word.strip('.,()[]')
                                        if len(word) > 4 and word.lower() not in ['ingredient', 'ingredients', 'contains', 'includes']:
                                            ingredients.append(word)
            
            product_data['ingredients'] = ingredients[:50]  # Limit to 50 ingredients
            
            # Try to extract hazard/safety score
            safety_text = soup.get_text().lower()
            if 'toxic' in safety_text or 'harmful' in safety_text:
                product_data['hazard_score'] = 'High'
            elif 'caution' in safety_text or 'moderate' in safety_text:
                product_data['hazard_score'] = 'Medium'
            elif 'safe' in safety_text or 'clean' in safety_text:
                product_data['hazard_score'] = 'Low'
            
            # Determine product type from name
            name_lower = product_data['product_name'].lower()
            if any(term in name_lower for term in ['moistur', 'cream', 'lotion', 'balm']):
                product_data['product_type'] = 'moisturizer'
            elif any(term in name_lower for term in ['cleans', 'wash', 'foam']):
                product_data['product_type'] = 'cleanser'
            
            if not product_data['product_name']:
                self.logger.warning(f"No product name found for {url}")
                return None
                
            self.logger.info(f"Scraped product: {product_data['product_name']} ({len(product_data['ingredients'])} ingredients)")
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return None
    
    def scrape_products(self, category: str = "moisturizer", limit: int = 10) -> List[Dict]:
        """
        Scrape products from Skin Signal.
        """
        self.logger.info(f"Starting Skin Signal scraping for {category} category, limit: {limit}")
        
        # Get product URLs
        product_urls = self.search_products(category, limit)
        
        if not product_urls:
            self.logger.warning("No product URLs found")
            return []
        
        scraped_products = []
        
        for i, url in enumerate(product_urls, 1):
            self.logger.info(f"Scraping product {i}/{len(product_urls)}")
            
            product_data = self.scrape_product_details(url)
            if product_data:
                scraped_products.append(product_data)
            
            # Rate limiting
            time.sleep(self.delay)
            
            # Progress break for large scrapes
            if i % 10 == 0:
                self.logger.info(f"Processed {i} products, taking a short break...")
                time.sleep(5)
        
        self.logger.info(f"Successfully scraped {len(scraped_products)} products from Skin Signal")
        return scraped_products