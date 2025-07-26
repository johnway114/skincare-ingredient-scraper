from typing import List, Dict, Optional
import re
import time
from urllib.parse import urljoin, quote
from .base_scraper import BaseScraper


class ClearForMeScraper(BaseScraper):
    """Scraper for ClearForMe ingredient safety database"""
    
    def __init__(self, delay: float = 2.0):
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://www.clearforme.com"
        
        # Add specific headers for ClearForMe
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
        """Search for products on ClearForMe"""
        
        # Search queries for ClearForMe
        search_queries = {
            "moisturizer": [
                "facial moisturizer",
                "face cream",
                "hydrating cream",
                "moisturizing cream"
            ],
            "cleanser": [
                "facial cleanser",
                "face wash",
                "cleansing cream",
                "gel cleanser"
            ]
        }
        
        product_urls = []
        queries = search_queries.get(category, search_queries["moisturizer"])
        
        for query in queries:
            try:
                # Try ClearForMe search patterns
                search_urls = [
                    f"{self.base_url}/search?q={quote(query)}",
                    f"{self.base_url}/products?search={quote(query)}",
                    f"{self.base_url}/ingredient-checker?q={quote(query)}"
                ]
                
                for search_url in search_urls:
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
                        if not any(pattern in href for pattern in ['/product/', '/products/', '/brand/', '/review']):
                            continue
                        
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            href = urljoin(self.base_url, href)
                        
                        # Only include ClearForMe URLs
                        if 'clearforme.com' in href and href not in product_urls:
                            product_urls.append(href)
                            self.logger.info(f"Found product URL: {href}")
                            
                            if limit and len(product_urls) >= limit:
                                break
                    
                    if limit and len(product_urls) >= limit:
                        break
                    
                    # Found results in this search URL, no need to try others
                    if product_urls:
                        break
                
                if limit and len(product_urls) >= limit:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Error searching for {query}: {e}")
                continue
                
            time.sleep(self.delay)
        
        # If no search results, try browsing main pages
        if not product_urls:
            main_pages = [
                f"{self.base_url}/products",
                f"{self.base_url}/brands",
                f"{self.base_url}/skincare",
                f"{self.base_url}"
            ]
            
            for page_url in main_pages:
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
                        if any(pattern in href for pattern in ['/product', '/brand']):
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
        
        self.logger.info(f"Found {len(product_urls)} ClearForMe product URLs")
        return product_urls[:limit] if limit else product_urls
    
    def scrape_product_details(self, product_url: str) -> Optional[Dict]:
        """Scrape detailed product information from ClearForMe product page"""
        
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
                'h1.product-name',
                'h1.product-title',
                '.product-header h1',
                'h1',
                '.product-name',
                '.title h1'
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
                '.brand',
                '.product-brand',
                '.brand-name',
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
            
            # Extract safety rating if available
            rating = None
            rating_selectors = [
                '.safety-rating',
                '.rating',
                '.score',
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
                '.product-ingredients',
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
            
            # If no ingredients found, try to find them in description or analysis
            if not ingredients:
                description_selectors = [
                    '.product-description',
                    '.analysis',
                    '.ingredient-analysis',
                    '.product-details'
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
                'source': 'ClearForMe',
                'price': None,
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
        self.logger.info(f"Starting ClearForMe scraping for {category}, limit: {limit}")
        
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
        
        self.logger.info(f"Successfully scraped {len(scraped_products)} products from ClearForMe")
        return scraped_products