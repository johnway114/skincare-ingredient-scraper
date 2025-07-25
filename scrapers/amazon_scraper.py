from typing import List, Dict, Optional
import re
import time
import random
from urllib.parse import urljoin, quote_plus
from .base_scraper import BaseScraper


class AmazonScraper(BaseScraper):
    """Scraper for Amazon skincare products"""
    
    def __init__(self, delay: float = 5.0):
        # Amazon requires Selenium due to heavy JavaScript and anti-bot measures
        super().__init__(delay=delay, use_selenium=True)
        self.base_url = "https://www.amazon.com"
        self.search_base = "/s"
        
        # Amazon-specific headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def search_products(self, category: str = "moisturizer", limit: Optional[int] = None) -> List[str]:
        """Search for skincare products on Amazon"""
        
        # Build search query
        if category == "moisturizer":
            query = "facial moisturizer skincare"
        elif category == "cleanser":
            query = "facial cleanser skincare"
        else:
            query = f"facial {category} skincare"
        
        # Amazon search URL with filters for skincare department
        search_params = {
            'k': query,
            'rh': 'n:3760911',  # Beauty & Personal Care department
            'ref': 'sr_nr_n_1'
        }
        
        search_url = f"{self.base_url}{self.search_base}?" + "&".join([f"{k}={quote_plus(str(v))}" for k, v in search_params.items()])
        
        self.logger.info(f"Searching Amazon for: {query}")
        
        if self.use_selenium and self.driver:
            self.driver.get(search_url)
            
            # Handle potential captcha or blocking
            page_source = self.driver.page_source
            if "captcha" in page_source.lower() or "robot" in page_source.lower():
                self.logger.warning("Amazon detected automation - captcha or robot check encountered")
                return []
            
            # Wait for page to load and get soup
            time.sleep(3 + random.uniform(1, 3))
            soup = self.get_page_from_driver()
        else:
            soup = self.get_page(search_url)
        
        if not soup:
            self.logger.warning("Failed to get search results page")
            return []
        
        product_urls = []
        
        # Amazon product link selectors (they change frequently)
        product_selectors = [
            'h2.a-size-mini a',
            'h2 a.a-link-normal',
            '.s-result-item h3 a',
            '.s-result-item .a-link-normal',
            'a[href*="/dp/"]',
            'a[href*="/gp/product/"]'
        ]
        
        for selector in product_selectors:
            links = soup.select(selector)
            if links:
                self.logger.info(f"Found product links using selector: {selector}")
                for link in links:
                    href = link.get('href')
                    if href:
                        # Clean up Amazon URLs
                        if href.startswith('/'):
                            full_url = self.base_url + href
                        else:
                            full_url = href
                        
                        # Extract just the product part (remove tracking parameters)
                        if '/dp/' in full_url:
                            product_id = re.search(r'/dp/([A-Z0-9]+)', full_url)
                            if product_id:
                                clean_url = f"{self.base_url}/dp/{product_id.group(1)}"
                                if clean_url not in product_urls:
                                    product_urls.append(clean_url)
                                    if limit and len(product_urls) >= limit:
                                        return product_urls
                break
        
        # Try next page if we need more results
        if limit and len(product_urls) < limit:
            next_page_selectors = [
                'a[aria-label="Go to next page"]',
                '.a-pagination .a-last a',
                'a:contains("Next")'
            ]
            
            for selector in next_page_selectors:
                next_link = soup.select_one(selector)
                if next_link:
                    next_href = next_link.get('href')
                    if next_href:
                        next_url = urljoin(self.base_url, next_href)
                        # Recursively get more products from next page
                        time.sleep(5 + random.uniform(2, 4))  # Longer delay between pages
                        
                        if self.use_selenium and self.driver:
                            self.driver.get(next_url)
                            time.sleep(3 + random.uniform(1, 3))
                            next_soup = self.get_page_from_driver()
                        else:
                            next_soup = self.get_page(next_url)
                        
                        if next_soup:
                            # Reuse the same logic for next page
                            for selector in product_selectors:
                                links = next_soup.select(selector)
                                if links:
                                    for link in links:
                                        href = link.get('href')
                                        if href:
                                            if href.startswith('/'):
                                                full_url = self.base_url + href
                                            else:
                                                full_url = href
                                            
                                            if '/dp/' in full_url:
                                                product_id = re.search(r'/dp/([A-Z0-9]+)', full_url)
                                                if product_id:
                                                    clean_url = f"{self.base_url}/dp/{product_id.group(1)}"
                                                    if clean_url not in product_urls:
                                                        product_urls.append(clean_url)
                                                        if limit and len(product_urls) >= limit:
                                                            return product_urls
                                    break
                        break
        
        self.logger.info(f"Found {len(product_urls)} product URLs from Amazon")
        return product_urls
    
    def scrape_product_details(self, product_url: str) -> Optional[Dict]:
        """Scrape details from a single Amazon product page"""
        
        # Use selenium for Amazon as they heavily use JavaScript
        if self.use_selenium and self.driver:
            self.driver.get(product_url)
            
            # Check for blocking
            page_source = self.driver.page_source
            if "captcha" in page_source.lower() or "robot" in page_source.lower():
                self.logger.warning(f"Amazon blocked access to {product_url}")
                return None
            
            # Wait for page to load
            time.sleep(3 + random.uniform(1, 3))
            soup = self.get_page_from_driver()
        else:
            soup = self.get_page(product_url)
        
        if not soup:
            self.logger.warning(f"Failed to fetch product page: {product_url}")
            return None
        
        product_data = {
            'url': product_url,
            'source': 'Amazon',
            'product_name': '',
            'brand': '',
            'price': '',
            'rating': '',
            'ingredients': [],
            'date_published': '',
            'hazard_score': ''
        }
        
        try:
            # Extract product name
            name_selectors = [
                '#productTitle',
                '.product-title',
                'h1.a-size-large',
                'h1 span'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    product_data['product_name'] = self.clean_text(name_elem.get_text())
                    break
            
            # Extract brand
            brand_selectors = [
                '#bylineInfo',
                '.a-link-normal#bylineInfo',
                '.po-brand .po-break-word',
                'tr:contains("Brand") td',
                'a[data-attribute="brand"]'
            ]
            
            for selector in brand_selectors:
                if 'contains' in selector:
                    # Skip CSS selectors with :contains for now
                    continue
                brand_elem = soup.select_one(selector)
                if brand_elem:
                    brand_text = brand_elem.get_text()
                    # Clean brand text (Amazon often has "Visit the X Store" format)
                    brand_text = re.sub(r'Visit the (.+) Store', r'\\1', brand_text)
                    brand_text = re.sub(r'Brand: (.+)', r'\\1', brand_text)
                    product_data['brand'] = self.clean_text(brand_text)
                    break
            
            # Extract price
            price_selectors = [
                '.a-price .a-offscreen',
                '#price_inside_buybox',
                '.a-price-whole',
                '.a-price.a-text-price.a-size-medium.apexPriceToPay',
                '.a-offscreen'
            ]
            
            for selector in price_selectors:
                price_elems = soup.select(selector)
                for price_elem in price_elems:
                    price_text = price_elem.get_text()
                    if '$' in price_text:
                        product_data['price'] = self.clean_text(price_text)
                        break
                if product_data['price']:
                    break
            
            # Extract rating
            rating_selectors = [
                '[data-hook="average-star-rating"] .a-icon-alt',
                '.a-icon-alt',
                '[aria-label*="stars"]'
            ]
            
            for selector in rating_selectors:
                rating_elem = soup.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text() or rating_elem.get('aria-label', '')
                    rating_match = re.search(r'(\\d+\\.?\\d*)', rating_text)
                    if rating_match:
                        product_data['rating'] = rating_match.group(1)
                        break
            
            # Extract ingredients - this is the challenging part for Amazon
            self.logger.info("Extracting ingredients from Amazon product")
            
            # Look in product details, features, and description
            ingredient_sections = [
                '#feature-bullets',
                '#productDetails_feature_div',
                '#aplus',
                '#productDescription',
                '#important-information',
                '.a-unordered-list.a-vertical.a-spacing-mini'
            ]
            
            ingredients_found = False
            
            for section_selector in ingredient_sections:
                section = soup.select_one(section_selector)
                if section:
                    section_text = section.get_text()
                    
                    # Look for ingredient keywords
                    ingredient_patterns = [
                        r'ingredients?\\s*:?\\s*([^.]*(?:water|aqua|glycerin|oil|acid)[^.]*)',
                        r'inci\\s*:?\\s*([^.]*(?:water|aqua|glycerin|oil|acid)[^.]*)',
                        r'active ingredients?\\s*:?\\s*([^.]*(?:water|aqua|glycerin|oil|acid)[^.]*)',
                        r'full ingredients?\\s*:?\\s*([^.]*(?:water|aqua|glycerin|oil|acid)[^.]*)'
                    ]
                    
                    for pattern in ingredient_patterns:
                        matches = re.finditer(pattern, section_text, re.IGNORECASE)
                        for match in matches:
                            potential_ingredients = match.group(1) if match.groups() else match.group(0)
                            parsed_ingredients = self.parse_ingredients(potential_ingredients)
                            if len(parsed_ingredients) > 3:
                                product_data['ingredients'] = parsed_ingredients
                                ingredients_found = True
                                break
                        if ingredients_found:
                            break
                    if ingredients_found:
                        break
            
            # If no ingredients found, try looking in any text on the page
            if not ingredients_found:
                page_text = soup.get_text()
                
                # More aggressive search in full page text
                broad_patterns = [
                    r'(?:ingredients?|inci|contains?)\\s*:?\\s*([^.]{50,500}(?:water|aqua|glycerin|dimethicone|oil|alcohol)[^.]{0,200})',
                ]
                
                for pattern in broad_patterns:
                    matches = re.finditer(pattern, page_text, re.IGNORECASE)
                    for match in matches:
                        potential_ingredients = match.group(1) if match.groups() else match.group(0)
                        parsed_ingredients = self.parse_ingredients(potential_ingredients)
                        if len(parsed_ingredients) > 2:
                            product_data['ingredients'] = parsed_ingredients
                            ingredients_found = True
                            break
                    if ingredients_found:
                        break
            
            self.logger.info(f"Scraped Amazon product: {product_data['product_name']} ({len(product_data['ingredients'])} ingredients)")
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error scraping Amazon product {product_url}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def scrape_products(self, limit: Optional[int] = None, category: str = "moisturizer") -> List[Dict]:
        """Main method to scrape products from Amazon"""
        self.logger.info(f"Starting Amazon scraping for {category}, limit: {limit}")
        
        # Get product URLs
        product_urls = self.search_products(category, limit)
        
        if not product_urls:
            self.logger.warning("No product URLs found on Amazon")
            return []
        
        # Scrape each product with significant delays (Amazon is very sensitive)
        products = []
        for i, url in enumerate(product_urls, 1):
            self.logger.info(f"Scraping Amazon product {i}/{len(product_urls)}")
            
            product_data = self.scrape_product_details(url)
            if product_data:
                products.append(product_data)
            
            # Very conservative delays for Amazon
            if i % 3 == 0:
                self.logger.info(f"Processed {i} products, taking a longer break...")
                time.sleep(15 + random.uniform(5, 10))
            else:
                time.sleep(self.delay + random.uniform(2, 5))
        
        self.logger.info(f"Successfully scraped {len(products)} products from Amazon")
        return products


# Example usage function
def main():
    """Example of how to use the Amazon scraper"""
    scraper = AmazonScraper(delay=5.0)
    
    try:
        # Scrape products - start with a very small limit due to Amazon's restrictions
        products = scraper.scrape_products(limit=3, category="moisturizer")
        
        if products:
            # Save the data
            scraper.save_data(products, 'amazon_products_test')
            print(f"Successfully scraped {len(products)} products!")
            
            # Print some sample data
            for product in products[:2]:
                print(f"\\nProduct: {product['product_name']}")
                print(f"Brand: {product['brand']}")
                print(f"Price: {product['price']}")
                print(f"Rating: {product['rating']}")
                print(f"Ingredients: {len(product['ingredients'])} found")
                if product['ingredients']:
                    print(f"First 5 ingredients: {product['ingredients'][:5]}")
        else:
            print("No products were scraped successfully")
            
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()