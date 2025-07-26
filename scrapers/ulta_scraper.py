from typing import List, Dict, Optional
import re
import time
from urllib.parse import urljoin, quote
from .base_scraper import BaseScraper


class UltaScraper(BaseScraper):
    """Scraper for Ulta Beauty products"""
    
    def __init__(self, delay: float = 4.0):
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://www.ulta.com"
        
        # Add specific headers for Ulta
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
        """Search for products on Ulta"""
        
        # Search queries for Ulta
        search_queries = {
            "moisturizer": [
                "facial moisturizer",
                "face cream",
                "hydrating cream",
                "night moisturizer",
                "day moisturizer"
            ],
            "cleanser": [
                "facial cleanser",
                "face wash",
                "cleansing cream",
                "gel cleanser",
                "foam cleanser"
            ]
        }
        
        product_urls = []
        queries = search_queries.get(category, search_queries["moisturizer"])
        
        for query in queries:
            try:
                # Ulta search URL pattern
                search_url = f"{self.base_url}/skin-care?N=1z141ez&Ntt={quote(query)}"
                
                response = self.get_page(search_url)
                if not response or response.status_code != 200:
                    # Try alternative search URL
                    search_url = f"{self.base_url}/beauty/products?keywords={quote(query)}"
                    response = self.get_page(search_url)
                    
                if not response or response.status_code != 200:
                    continue
                    
                soup = self.create_soup(response.text)
                if not soup:
                    continue
                
                # Look for product links
                product_links = soup.find_all('a', href=True)
                
                for link in product_links:
                    href = link.get('href', '')
                    
                    # Skip if not a product link
                    if not any(pattern in href for pattern in ['/product/', '/p/', 'productId']):
                        continue
                    
                    # Skip non-product pages
                    if any(skip in href for skip in ['/brand/', '/category/', '/search', '/account']):
                        continue
                    
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    
                    # Only include Ulta URLs
                    if 'ulta.com' in href and href not in product_urls:
                        product_urls.append(href)
                        self.logger.info(f"Found product URL: {href}")
                        
                        if limit and len(product_urls) >= limit:
                            break
                
                if limit and len(product_urls) >= limit:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Error searching for {query}: {e}")
                continue
                
            time.sleep(self.delay)
        
        # If no search results, try browsing category pages
        if not product_urls:
            category_pages = [
                f"{self.base_url}/skin-care/moisturizers",
                f"{self.base_url}/skin-care/cleansers",
                f"{self.base_url}/skin-care",
                f"{self.base_url}/beauty/skin-care"
            ]
            
            for page_url in category_pages:
                try:
                    response = self.get_page(page_url)
                    if not response or response.status_code != 200:
                        continue
                    
                    soup = self.create_soup(response.text)
                    if not soup:
                        continue
                    
                    # Look for product links
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if '/product/' in href or '/p/' in href or 'productId' in href:
                            if href.startswith('/'):
                                href = urljoin(self.base_url, href)
                            if href not in product_urls:
                                product_urls.append(href)
                                if limit and len(product_urls) >= limit:
                                    break
                    
                    if limit and len(product_urls) >= limit:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error browsing {page_url}: {e}")
                    continue
                
                time.sleep(self.delay)
        
        self.logger.info(f"Found {len(product_urls)} Ulta product URLs")
        return product_urls[:limit] if limit else product_urls
    
    def scrape_product_details(self, product_url: str) -> Optional[Dict]:
        """Scrape detailed product information from Ulta product page"""
        
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
                'h1.prod-title',
                'h1.product-title',
                '.product-header h1',
                'h1',
                '.prod-title',
                '.product-name'
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
            
            # Extract brand
            brand = None
            brand_selectors = [
                '.prod-brand',
                '.product-brand',
                '.brand',
                '[data-brand]'
            ]
            
            for selector in brand_selectors:
                brand_elem = soup.select_one(selector)
                if brand_elem:
                    brand = brand_elem.get_text().strip()
                    break
            
            # Try to extract brand from product name if not found
            if not brand:
                # Common pattern: "Brand Name Product Name"
                words = product_name.split()
                if len(words) >= 2:
                    brand = words[0]
            
            # Extract price
            price = None
            price_selectors = [
                '.prod-price',
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
            
            # Extract rating
            rating = None
            rating_selectors = [
                '.prod-rating',
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
            
            # Extract ingredients
            ingredients = []
            ingredient_selectors = [
                '.ingredients',
                '.ingredient-list',
                '.prod-ingredients',
                '.ingredients-section',
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
            
            # If no ingredients found, try product description/details
            if not ingredients:
                description_selectors = [
                    '.prod-description',
                    '.product-description',
                    '.description',
                    '.prod-details'
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
            
            product_data = {
                'product_name': product_name,
                'brand': brand or "Unknown",
                'url': product_url,
                'source': 'Ulta Beauty',
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
        self.logger.info(f"Starting Ulta scraping for {category}, limit: {limit}")
        
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
        
        self.logger.info(f"Successfully scraped {len(scraped_products)} products from Ulta")
        return scraped_products