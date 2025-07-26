from typing import List, Dict, Optional
import re
import time
from urllib.parse import urljoin, quote
from .base_scraper import BaseScraper


class PaulasChoiceScraper(BaseScraper):
    """Scraper for Paula's Choice Beautypedia ingredient checker and product reviews"""
    
    def __init__(self, delay: float = 3.0):
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://www.paulaschoice.com"
        
        # Add specific headers for Paula's Choice
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
    def search_products(self, category: str = "moisturizer", limit: Optional[int] = None) -> List[str]:
        """Search for Paula's Choice products"""
        
        # Category mapping for Paula's Choice
        category_urls = {
            "moisturizer": [
                "https://www.paulaschoice.com/moisturizers",
                "https://www.paulaschoice.com/face-moisturizers",
                "https://www.paulaschoice.com/night-moisturizers",
                "https://www.paulaschoice.com/day-moisturizers"
            ],
            "cleanser": [
                "https://www.paulaschoice.com/cleansers",
                "https://www.paulaschoice.com/face-cleansers",
                "https://www.paulaschoice.com/gel-cleansers",
                "https://www.paulaschoice.com/cream-cleansers"
            ]
        }
        
        product_urls = []
        urls_to_try = category_urls.get(category, category_urls["moisturizer"])
        
        for category_url in urls_to_try:
            try:
                response = self.get_page(category_url)
                if not response or response.status_code != 200:
                    continue
                    
                soup = self.create_soup(response.text)
                if not soup:
                    continue
                
                # Look for product links in various formats
                product_links = soup.find_all('a', href=True)
                
                for link in product_links:
                    href = link.get('href', '')
                    
                    # Skip if not a product link
                    if not any(pattern in href for pattern in ['/product/', '/products/', '/item/']):
                        continue
                    
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    
                    # Only include Paula's Choice URLs
                    if 'paulaschoice.com' in href and href not in product_urls:
                        product_urls.append(href)
                        self.logger.info(f"Found product URL: {href}")
                        
                        if limit and len(product_urls) >= limit:
                            break
                
                if limit and len(product_urls) >= limit:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Error searching category {category_url}: {e}")
                continue
                
            time.sleep(self.delay)
        
        self.logger.info(f"Found {len(product_urls)} Paula's Choice product URLs")
        return product_urls[:limit] if limit else product_urls
    
    def scrape_product_details(self, product_url: str) -> Optional[Dict]:
        """Scrape detailed product information from Paula's Choice product page"""
        
        try:
            response = self.get_page(product_url)
            if not response or response.status_code != 200:
                self.logger.error(f"Failed to fetch product page: {product_url}")
                return None
            
            soup = self.create_soup(response.text)
            if not soup:
                return None
            
            # Extract product name
            product_name = None
            name_selectors = [
                'h1.product-title',
                'h1.product-name', 
                '.product-title h1',
                'h1',
                '.product-header h1'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    product_name = name_elem.get_text().strip()
                    break
            
            if not product_name:
                self.logger.warning(f"Could not find product name for {product_url}")
                return None
            
            # Clean product name
            product_name = re.sub(r'\s+', ' ', product_name).strip()
            
            # Extract price
            price = None
            price_selectors = [
                '.price',
                '.product-price',
                '.price-current',
                '[data-price]'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    # Extract price with regex
                    price_match = re.search(r'\$[\d,]+\.?\d*', price_text)
                    if price_match:
                        price = price_match.group()
                        break
            
            # Extract ingredients
            ingredients = []
            ingredient_selectors = [
                '.ingredients',
                '.product-ingredients',
                '.ingredient-list',
                '[data-ingredients]'
            ]
            
            for selector in ingredient_selectors:
                ingredient_elem = soup.select_one(selector)
                if ingredient_elem:
                    ingredient_text = ingredient_elem.get_text()
                    parsed_ingredients = self.parse_ingredients(ingredient_text)
                    if parsed_ingredients:
                        ingredients = parsed_ingredients
                        break
            
            # If no ingredients found in dedicated section, try description
            if not ingredients:
                description_selectors = [
                    '.product-description',
                    '.product-details',
                    '.description'
                ]
                
                for selector in description_selectors:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        desc_text = desc_elem.get_text()
                        # Look for ingredient patterns in description
                        if 'ingredients' in desc_text.lower():
                            parsed_ingredients = self.parse_ingredients(desc_text)
                            if parsed_ingredients:
                                ingredients = parsed_ingredients
                                break
            
            # Extract rating if available
            rating = None
            rating_selectors = [
                '.rating',
                '.star-rating',
                '[data-rating]'
            ]
            
            for selector in rating_selectors:
                rating_elem = soup.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text().strip()
                    rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                    if rating_match:
                        rating = rating_match.group(1)
                        break
            
            product_data = {
                'product_name': product_name,
                'brand': "Paula's Choice",
                'url': product_url,
                'source': "Paula's Choice",
                'price': price,
                'rating': rating,
                'ingredients': ingredients,
                'date_published': None
            }
            
            self.logger.info(f"Scraped product: {product_name} ({len(ingredients)} ingredients)")
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error scraping product {product_url}: {e}")
            return None
    
    def scrape_products(self, category: str = "moisturizer", limit: Optional[int] = None) -> List[Dict]:
        """Main scraping method"""
        self.logger.info(f"Starting Paula's Choice scraping for {category}, limit: {limit}")
        
        # Find product URLs
        product_urls = self.search_products(category, limit)
        
        if not product_urls:
            self.logger.warning("No product URLs found")
            return []
        
        scraped_products = []
        
        for i, product_url in enumerate(product_urls):
            self.logger.info(f"Scraping product {i+1}/{len(product_urls)}: {product_url}")
            
            product_data = self.scrape_product_details(product_url)
            if product_data:
                scraped_products.append(product_data)
            
            # Take a break every 10 products
            if (i + 1) % 10 == 0:
                self.logger.info(f"Processed {i + 1} products, taking a short break...")
                time.sleep(5)
            
            time.sleep(self.delay)
        
        self.logger.info(f"Successfully scraped {len(scraped_products)} products from Paula's Choice")
        return scraped_products