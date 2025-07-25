from typing import List, Dict, Optional
import re
from urllib.parse import urljoin
from .base_scraper import BaseScraper


class INCIDecoderScraper(BaseScraper):
    """Scraper for INCIDecoder ingredient and product database"""
    
    def __init__(self, delay: float = 2.0):
        # Start with simple requests, fall back to selenium if needed
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://www.incidecoder.com"
        self.endpoints = {
            'products': '/products',
            'ingredients': '/ingredients'
        }
    
    def get_product_urls(self, limit: Optional[int] = None) -> List[str]:
        """Get list of product URLs from the products page"""
        products_url = self.base_url + self.endpoints['products']
        soup = self.get_page(products_url)
        
        if not soup:
            self.logger.error(f"Failed to fetch products page: {products_url}")
            return []
        
        product_urls = []
        
        # Look for product cards and links
        product_selectors = [
            'a[href*="/products/"]',
            '.product-card a',
            '[class*="product"] a',
            'div[data-product] a'
        ]
        
        for selector in product_selectors:
            product_links = soup.select(selector)
            if product_links:
                self.logger.info(f"Found product links using selector: {selector}")
                break
        
        # If no specific selectors work, try a broader approach
        if not product_links:
            all_links = soup.find_all('a', href=True)
            product_links = [link for link in all_links if '/products/' in link.get('href', '')]
        
        for link in product_links:
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                if full_url not in product_urls:
                    product_urls.append(full_url)
                    
                if limit and len(product_urls) >= limit:
                    break
        
        self.logger.info(f"Found {len(product_urls)} product URLs")
        return product_urls
    
    def scrape_product_details(self, product_url: str) -> Optional[Dict]:
        """Scrape details from a single INCIDecoder product page"""
        soup = self.get_page(product_url)
        
        if not soup:
            self.logger.warning(f"Failed to fetch product page: {product_url}")
            return None
        
        product_data = {
            'url': product_url,
            'source': 'INCIDecoder',
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
                'h1[class*="product-name"]',
                'h1[class*="title"]',
                '.product-title h1',
                'h1',
                '.product-name'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    product_data['product_name'] = self.clean_text(name_elem.get_text())
                    break
            
            # Extract brand
            brand_selectors = [
                '[class*="brand"]',
                '.product-brand',
                'a[href*="/brands/"]',
                'span[class*="brand"]'
            ]
            
            for selector in brand_selectors:
                brand_elem = soup.select_one(selector)
                if brand_elem:
                    product_data['brand'] = self.clean_text(brand_elem.get_text())
                    break
            
            # If brand not found, try to extract from product name or URL
            if not product_data['brand']:
                if product_data['product_name']:
                    # Many products start with brand name
                    name_words = product_data['product_name'].split()
                    if len(name_words) > 1:
                        potential_brand = name_words[0]
                        if len(potential_brand) > 2:
                            product_data['brand'] = potential_brand
                
                # Try to extract from URL
                if not product_data['brand']:
                    url_parts = product_url.split('/')
                    for part in url_parts:
                        if len(part) > 3 and not part.isdigit():
                            # Look for brand-like parts in URL
                            cleaned_part = part.replace('-', ' ').replace('_', ' ').title()
                            if any(word in cleaned_part for word in ['Skincare', 'Beauty', 'Cosmetics']):
                                continue
                            product_data['brand'] = cleaned_part
                            break
            
            # Extract ingredients - this is the main focus for INCIDecoder
            self.logger.info("Extracting ingredients from INCIDecoder")
            
            # Look for ingredient sections
            ingredient_selectors = [
                '.ingredients-list',
                '.ingredient-list',
                '[class*="ingredients"]',
                '#ingredients',
                '.product-ingredients'
            ]
            
            ingredients_found = False
            
            for selector in ingredient_selectors:
                ingredients_section = soup.select_one(selector)
                if ingredients_section:
                    # Try to find individual ingredient items
                    ingredient_items = ingredients_section.select('li, .ingredient-item, [class*="ingredient-name"]')
                    
                    if ingredient_items:
                        ingredients = []
                        for item in ingredient_items:
                            ingredient_text = self.clean_text(item.get_text())
                            if ingredient_text and len(ingredient_text) > 1:
                                # Clean up ingredient name
                                ingredient_text = re.sub(r'\s*\([^)]*\)', '', ingredient_text)  # Remove parenthetical info
                                ingredient_text = ingredient_text.strip()
                                if ingredient_text:
                                    ingredients.append(ingredient_text)
                        
                        if ingredients:
                            product_data['ingredients'] = ingredients
                            ingredients_found = True
                            break
                    else:
                        # Try to get text content and parse it
                        ingredients_text = self.clean_text(ingredients_section.get_text())
                        if ingredients_text:
                            parsed_ingredients = self.parse_ingredients(ingredients_text)
                            if len(parsed_ingredients) > 1:
                                product_data['ingredients'] = parsed_ingredients
                                ingredients_found = True
                                break
            
            # If no ingredients found with specific selectors, try broader search
            if not ingredients_found:
                # Look for ingredient links (INCIDecoder links to individual ingredients)
                ingredient_links = soup.select('a[href*="/ingredients/"]')
                if ingredient_links:
                    ingredients = []
                    for link in ingredient_links:
                        ingredient_name = self.clean_text(link.get_text())
                        if ingredient_name and len(ingredient_name) > 1:
                            ingredients.append(ingredient_name)
                    
                    if ingredients:
                        product_data['ingredients'] = ingredients[:50]  # Limit to reasonable number
                        ingredients_found = True
            
            # Final fallback - look for any text that looks like ingredients
            if not ingredients_found:
                page_text = soup.get_text()
                
                # Look for ingredient patterns
                ingredient_patterns = [
                    r'ingredients?\s*:?\s*([^.]*(?:water|aqua|glycerin|oil)[^.]*)',
                    r'contains?\s*:?\s*([^.]*(?:water|aqua|glycerin|oil)[^.]*)',
                    r'(\b(?:water|aqua),\s*[^.]*)',
                ]
                
                for pattern in ingredient_patterns:
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
            
            # Extract any rating or score information
            rating_selectors = [
                '[class*="rating"]',
                '[class*="score"]',
                '.product-rating',
                '[aria-label*="star"]'
            ]
            
            for selector in rating_selectors:
                rating_elem = soup.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text() or rating_elem.get('aria-label', '')
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        product_data['rating'] = rating_match.group(1)
                        break
            
            # Look for additional product information in meta tags or structured data
            meta_description = soup.select_one('meta[name="description"]')
            if meta_description and not product_data['ingredients']:
                desc_content = meta_description.get('content', '')
                if any(word in desc_content.lower() for word in ['ingredients', 'contains', 'water', 'glycerin']):
                    parsed_ingredients = self.parse_ingredients(desc_content)
                    if len(parsed_ingredients) > 1:
                        product_data['ingredients'] = parsed_ingredients
            
            self.logger.info(f"Scraped product: {product_data['product_name']} ({len(product_data['ingredients'])} ingredients)")
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error scraping product {product_url}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def scrape_ingredient_info(self, ingredient_name: str) -> Optional[Dict]:
        """Scrape information about a specific ingredient"""
        # Construct ingredient URL (INCIDecoder typically uses ingredient names in URLs)
        ingredient_slug = ingredient_name.lower().replace(' ', '-').replace('(', '').replace(')', '')
        ingredient_url = f"{self.base_url}/ingredients/{ingredient_slug}"
        
        soup = self.get_page(ingredient_url)
        if not soup:
            return None
        
        ingredient_data = {
            'name': ingredient_name,
            'url': ingredient_url,
            'source': 'INCIDecoder',
            'category': '',
            'function': '',
            'description': '',
            'safety_rating': ''
        }
        
        try:
            # Extract ingredient function/category
            function_selectors = [
                '.what-it-does',
                '[class*="function"]',
                '.ingredient-function',
                '[class*="category"]'
            ]
            
            for selector in function_selectors:
                function_elem = soup.select_one(selector)
                if function_elem:
                    ingredient_data['function'] = self.clean_text(function_elem.get_text())
                    break
            
            # Extract description
            desc_selectors = [
                '.description',
                '.ingredient-description',
                '[class*="desc"]',
                'p'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    desc_text = self.clean_text(desc_elem.get_text())
                    if len(desc_text) > 20:  # Reasonable description length
                        ingredient_data['description'] = desc_text[:500]  # Limit length
                        break
            
            return ingredient_data
            
        except Exception as e:
            self.logger.error(f"Error scraping ingredient {ingredient_name}: {e}")
            return None
    
    def scrape_products(self, limit: Optional[int] = None) -> List[Dict]:
        """Main method to scrape products from INCIDecoder"""
        self.logger.info(f"Starting INCIDecoder scraping, limit: {limit}")
        
        # Get product URLs
        product_urls = self.get_product_urls(limit)
        
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
            
            # Be respectful with delays
            if i % 10 == 0:  # Every 10 products, take a longer break
                self.logger.info(f"Processed {i} products, taking a short break...")
                import time
                time.sleep(5)
        
        self.logger.info(f"Successfully scraped {len(products)} products from INCIDecoder")
        return products


# Example usage function
def main():
    """Example of how to use the INCIDecoder scraper"""
    scraper = INCIDecoderScraper(delay=2.0)
    
    try:
        # Scrape 10 products as a test
        products = scraper.scrape_products(limit=10)
        
        if products:
            # Save the data
            scraper.save_data(products, 'incidecoder_products_test')
            print(f"Successfully scraped {len(products)} products!")
            
            # Print some sample data
            for product in products[:3]:  # Show first 3 products
                print(f"\nProduct: {product['product_name']}")
                print(f"Brand: {product['brand']}")
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