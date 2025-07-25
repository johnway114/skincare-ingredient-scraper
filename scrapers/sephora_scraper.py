from typing import List, Dict, Optional
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_scraper import BaseScraper


class SephoraScraper(BaseScraper):
    """Scraper for Sephora website - requires Selenium due to heavy JavaScript"""
    
    def __init__(self, delay: float = 3.0):
        # Sephora requires Selenium due to heavy JavaScript and anti-bot measures
        super().__init__(delay=delay, use_selenium=True)
        self.base_url = "https://www.sephora.com"
        self.category_urls = {
            'moisturizer': '/shop/facial-moisturizer',
            'cleanser': '/shop/face-wash-facial-cleanser'
        }
    
    def get_product_urls(self, category: str = 'moisturizer', limit: Optional[int] = None) -> List[str]:
        """Get list of product URLs from a category page"""
        if category not in self.category_urls:
            self.logger.error(f"Unknown category: {category}")
            return []
        
        category_url = self.base_url + self.category_urls[category]
        self.logger.info(f"Fetching category page: {category_url}")
        
        # Use Selenium to handle JavaScript
        if not self.driver:
            self.setup_selenium()
        
        try:
            self.driver.get(category_url)
            
            # Check if we're blocked or redirected
            current_url = self.driver.current_url
            page_title = self.driver.title.lower()
            
            if 'blocked' in page_title or 'access denied' in page_title or 'captcha' in page_title:
                self.logger.error("Detected blocking/captcha page")
                return []
            
            # Wait for products to load
            wait = WebDriverWait(self.driver, 20)
            
            # Try different selectors that Sephora might use
            product_selectors = [
                'a[data-comp="ProductTile StyledComponent"]',
                'a[data-testid="product-tile"]',
                'a[href*="/product/"]',
                '.css-product-tile a',
                '[data-comp*="ProductTile"] a'
            ]
            
            products_found = False
            product_links = []
            
            for selector in product_selectors:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        self.logger.info(f"Found products using selector: {selector}")
                        for element in elements:
                            href = element.get_attribute('href')
                            if href and '/product/' in href:
                                product_links.append(href)
                                if limit and len(product_links) >= limit:
                                    break
                        products_found = True
                        break
                        
                except TimeoutException:
                    continue
            
            if not products_found:
                # Try scrolling to load more products
                self.logger.info("Attempting to scroll and load products")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                # Try a more general approach
                all_links = self.driver.find_elements(By.TAG_NAME, 'a')
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and '/product/' in href and 'sephora.com' in href:
                        product_links.append(href)
                        if limit and len(product_links) >= limit:
                            break
            
            # Remove duplicates while preserving order
            seen = set()
            unique_links = []
            for link in product_links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            
            self.logger.info(f"Found {len(unique_links)} unique product URLs in {category}")
            return unique_links[:limit] if limit else unique_links
            
        except Exception as e:
            self.logger.error(f"Error fetching product URLs: {e}")
            return []
    
    def scrape_product_details(self, product_url: str) -> Optional[Dict]:
        """Scrape details from a single Sephora product page"""
        if not self.driver:
            self.setup_selenium()
        
        product_data = {
            'url': product_url,
            'source': 'Sephora',
            'product_name': '',
            'brand': '',
            'price': '',
            'rating': '',
            'ingredients': [],
            'date_published': '',
            'hazard_score': ''
        }
        
        try:
            self.logger.info(f"Scraping product: {product_url}")
            self.driver.get(product_url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 15)
            time.sleep(self.delay)
            
            # Extract product name
            name_selectors = [
                'h1[data-testid="product-name"]',
                'h1.css-product-name',
                'h1[class*="ProductDisplayName"]',
                'h1',
                '.product-name h1'
            ]
            
            for selector in name_selectors:
                try:
                    name_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    product_data['product_name'] = self.clean_text(name_element.text)
                    break
                except TimeoutException:
                    continue
            
            # Extract brand
            brand_selectors = [
                '[data-testid="brand-name"]',
                'a[data-testid="brand-name"]',
                '.css-brand-name',
                '[class*="BrandName"]'
            ]
            
            for selector in brand_selectors:
                try:
                    brand_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    product_data['brand'] = self.clean_text(brand_element.text)
                    break
                except NoSuchElementException:
                    continue
            
            # If brand not found, try to extract from product name
            if not product_data['brand'] and product_data['product_name']:
                # Many Sephora products start with brand name
                name_words = product_data['product_name'].split()
                if len(name_words) > 1:
                    potential_brand = name_words[0]
                    if len(potential_brand) > 2:
                        product_data['brand'] = potential_brand
            
            # Extract price
            price_selectors = [
                '[data-testid="price"]',
                '.css-price',
                '[class*="Price"]',
                '.price'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = self.clean_text(price_element.text)
                    # Extract price from text like "$25.00" or "$15.00 - $45.00"
                    price_match = re.search(r'\$[\d,]+\.?\d*', price_text)
                    if price_match:
                        product_data['price'] = price_match.group(0)
                        break
                except NoSuchElementException:
                    continue
            
            # Extract rating
            rating_selectors = [
                '[data-testid="rating"]',
                '.css-rating',
                '[aria-label*="star"]',
                '[class*="Rating"]'
            ]
            
            for selector in rating_selectors:
                try:
                    rating_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_element.get_attribute('aria-label') or rating_element.text
                    rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of|\/|stars?)', rating_text, re.I)
                    if rating_match:
                        product_data['rating'] = f"{rating_match.group(1)}/5"
                        break
                except NoSuchElementException:
                    continue
            
            # Extract ingredients - this is the most important part
            self.logger.info("Attempting to find ingredients")
            
            # Try to find and click ingredients tab/section
            ingredient_triggers = [
                '[data-testid="ingredients-tab"]',
                'button[aria-label*="ingredients"]',
                'button:contains("Ingredients")',
                '[data-testid="toggle-ingredients"]',
                'a[href*="#ingredients"]'
            ]
            
            ingredients_section_found = False
            
            for trigger_selector in ingredient_triggers:
                try:
                    if ':contains(' in trigger_selector:
                        # Handle text-based selector
                        elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), 'Ingredients')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, trigger_selector)
                    
                    if elements:
                        element = elements[0]
                        self.driver.execute_script("arguments[0].click();", element)
                        time.sleep(2)
                        ingredients_section_found = True
                        break
                        
                except Exception as e:
                    self.logger.debug(f"Could not click ingredient trigger {trigger_selector}: {e}")
                    continue
            
            # Look for ingredients content
            ingredient_selectors = [
                '[data-testid="ingredients-content"]',
                '.css-ingredients',
                '[class*="Ingredients"]',
                '#ingredients',
                '.ingredients-list'
            ]
            
            for selector in ingredient_selectors:
                try:
                    ingredients_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    ingredients_text = self.clean_text(ingredients_element.text)
                    
                    if ingredients_text and len(ingredients_text) > 20:
                        parsed_ingredients = self.parse_ingredients(ingredients_text)
                        if parsed_ingredients:
                            product_data['ingredients'] = parsed_ingredients
                            break
                            
                except NoSuchElementException:
                    continue
            
            # If no ingredients found with specific selectors, try broader search
            if not product_data['ingredients']:
                self.logger.info("Trying broader search for ingredients")
                
                # Look for any text that might contain ingredients
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                
                # Look for ingredient patterns in page text
                ingredient_patterns = [
                    r'ingredients?\s*:?\s*([^.]*(?:water|aqua|glycerin|oil)[^.]*)',
                    r'full\s+ingredient\s+list\s*:?\s*([^.]*)',
                    r'(\b(?:water|aqua),\s*[^.]*)',
                ]
                
                for pattern in ingredient_patterns:
                    matches = re.finditer(pattern, page_text, re.IGNORECASE)
                    for match in matches:
                        potential_ingredients = match.group(1) if match.groups() else match.group(0)
                        parsed_ingredients = self.parse_ingredients(potential_ingredients)
                        if len(parsed_ingredients) > 3:
                            product_data['ingredients'] = parsed_ingredients
                            break
                    if product_data['ingredients']:
                        break
            
            self.logger.info(f"Scraped product: {product_data['product_name']} ({len(product_data['ingredients'])} ingredients)")
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error scraping product {product_url}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def scrape_products(self, limit: Optional[int] = None, category: str = 'moisturizer') -> List[Dict]:
        """Main method to scrape products from Sephora"""
        self.logger.info(f"Starting Sephora scraping for {category} category, limit: {limit}")
        
        # Get product URLs
        product_urls = self.get_product_urls(category, limit)
        
        if not product_urls:
            self.logger.warning("No product URLs found")
            return []
        
        # Scrape each product
        products = []
        for i, url in enumerate(product_urls, 1):
            self.logger.info(f"Scraping product {i}/{len(product_urls)}")
            
            product_data = self.scrape_product_details(url)
            if product_data:
                products.append(product_data)
            
            # Be extra respectful with Sephora
            if i % 5 == 0:  # Every 5 products, take a longer break
                self.logger.info(f"Processed {i} products, taking a longer break...")
                time.sleep(10)
            else:
                time.sleep(self.delay)
        
        self.logger.info(f"Successfully scraped {len(products)} products from Sephora")
        return products


# Example usage function
def main():
    """Example of how to use the Sephora scraper"""
    scraper = SephoraScraper(delay=3.0)
    
    try:
        # Scrape 5 moisturizers as a test (small number due to complexity)
        products = scraper.scrape_products(limit=5, category='moisturizer')
        
        if products:
            # Save the data
            scraper.save_data(products, 'sephora_moisturizers_test')
            print(f"Successfully scraped {len(products)} products!")
            
            # Print some sample data
            for product in products[:2]:  # Show first 2 products
                print(f"\nProduct: {product['product_name']}")
                print(f"Brand: {product['brand']}")
                print(f"Price: {product['price']}")
                print(f"Rating: {product['rating']}")
                print(f"Ingredients: {len(product['ingredients'])} found")
                if product['ingredients']:
                    print(f"First 3 ingredients: {product['ingredients'][:3]}")
        else:
            print("No products were scraped successfully")
            
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()