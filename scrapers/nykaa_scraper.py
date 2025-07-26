#!/usr/bin/env python3
"""
Nykaa scraper for skincare products.
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin
from .base_scraper import BaseScraper

class NykaaScraper(BaseScraper):
    def __init__(self, delay: float = 4.0):
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://www.nykaa.com"
        
    def search_products(self, category: str = "moisturizer", limit: int = 10) -> List[str]:
        """
        Search for skincare products on Nykaa.
        """
        self.logger.info(f"Starting Nykaa search for {category}, limit: {limit}")
        
        product_urls = []
        
        # Category-specific URLs
        category_urls = {
            'moisturizer': [
                f"{self.base_url}/skin/moisturizer",
                f"{self.base_url}/skin/face-moisturizer",
                f"{self.base_url}/skincare/moisturizer"
            ],
            'cleanser': [
                f"{self.base_url}/skin/face-wash",
                f"{self.base_url}/skin/cleanser",
                f"{self.base_url}/skincare/cleanser"
            ]
        }
        
        search_urls = category_urls.get(category, category_urls['moisturizer'])
        
        try:
            for search_url in search_urls:
                self.logger.info(f"Fetching: {search_url}")
                soup = self.get_page(search_url)
                if soup:
                    
                    # Look for product links
                    product_links = soup.find_all('a', href=True)
                    
                    for link in product_links:
                        href = link.get('href', '')
                        
                        # Look for product page patterns
                        if any(pattern in href for pattern in [
                            '/product/', '/p/', '/skin/', '/skincare/'
                        ]):
                            full_url = urljoin(self.base_url, href)
                            if full_url not in product_urls and 'nykaa.com' in full_url:
                                product_urls.append(full_url)
                                if len(product_urls) >= limit:
                                    break
                
                if len(product_urls) >= limit:
                    break
                    
                time.sleep(self.delay)
            
            # If no specific category pages work, try main skin page
            if not product_urls:
                main_url = f"{self.base_url}/skin"
                soup = self.get_page(main_url)
                if soup:
                    links = soup.find_all('a', href=True)
                    
                    for link in links:
                        href = link.get('href', '')
                        text = link.get_text(strip=True).lower()
                        
                        if '/product/' in href or (category in text and href):
                            full_url = urljoin(self.base_url, href)
                            if full_url not in product_urls:
                                product_urls.append(full_url)
                                if len(product_urls) >= limit:
                                    break
                        
        except Exception as e:
            self.logger.error(f"Error searching Nykaa: {e}")
        
        self.logger.info(f"Found {len(product_urls)} product URLs")
        return product_urls[:limit]
    
    def scrape_product_details(self, url: str) -> Optional[Dict]:
        """
        Scrape details from a Nykaa product page.
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
                'source': 'Nykaa',
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
                'h1.product-title',
                'h1',
                '.product-name',
                '[class*="product-title"]',
                '.title'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem and name_elem.get_text(strip=True):
                    product_data['product_name'] = name_elem.get_text(strip=True)
                    break
            
            # Try to find brand
            brand_selectors = [
                '.brand-name',
                '.product-brand',
                '[class*="brand"]',
                '.manufacturer'
            ]
            
            for selector in brand_selectors:
                brand_elem = soup.select_one(selector)
                if brand_elem and brand_elem.get_text(strip=True):
                    product_data['brand'] = brand_elem.get_text(strip=True)
                    break
            
            # Extract brand from product name if not found separately
            if not product_data['brand'] and product_data['product_name']:
                name_parts = product_data['product_name'].split()
                if len(name_parts) > 1:
                    product_data['brand'] = name_parts[0]
            
            # Try to find price
            price_selectors = [
                '.price',
                '[class*="price"]',
                '.product-price',
                '.cost'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if '₹' in price_text or '$' in price_text:
                        product_data['price'] = price_text
                        break
            
            # Try to find rating
            rating_selectors = [
                '.rating',
                '[class*="rating"]',
                '.stars',
                '[class*="star"]'
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
            
            # Look for ingredient sections
            ingredient_selectors = [
                '.ingredients',
                '[class*="ingredient"]',
                '.product-ingredients',
                '.composition',
                '.key-ingredients'
            ]
            
            for selector in ingredient_selectors:
                ingredient_section = soup.select_one(selector)
                if ingredient_section:
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
            
            product_data['ingredients'] = ingredients[:50]
            
            # Determine product type
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
        Scrape products from Nykaa.
        """
        self.logger.info(f"Starting Nykaa scraping for {category} category, limit: {limit}")
        
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
            
            time.sleep(self.delay)
            
            if i % 10 == 0:
                self.logger.info(f"Processed {i} products, taking a short break...")
                time.sleep(5)
        
        self.logger.info(f"Successfully scraped {len(scraped_products)} products from Nykaa")
        return scraped_products