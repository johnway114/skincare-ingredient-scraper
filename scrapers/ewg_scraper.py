from typing import List, Dict, Optional
import re
from urllib.parse import urljoin
from .base_scraper import BaseScraper


class EWGScraper(BaseScraper):
    """Scraper for EWG Skin Deep database"""
    
    def __init__(self, delay: float = 2.0):
        # EWG is mostly static HTML, so we don't need selenium
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://www.ewg.org"
        self.category_urls = {
            'moisturizer': '/skindeep/browse/category/facial_moisturizer/',
            'cleanser': '/skindeep/browse/category/facial_cleanser/'
        }
    
    def get_product_urls(self, category: str = 'moisturizer', limit: Optional[int] = None) -> List[str]:
        """Get list of product URLs from a category page"""
        if category not in self.category_urls:
            self.logger.error(f"Unknown category: {category}")
            return []
        
        category_url = self.base_url + self.category_urls[category]
        soup = self.get_page(category_url)
        
        if not soup:
            self.logger.error(f"Failed to fetch category page: {category_url}")
            return []
        
        product_urls = []
        
        # Look for product links - these typically have /skindeep/products/ in URL
        product_links = soup.find_all('a', href=re.compile(r'/skindeep/products/'))
        
        for link in product_links:
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                if full_url not in product_urls:
                    product_urls.append(full_url)
                    
                if limit and len(product_urls) >= limit:
                    break
        
        self.logger.info(f"Found {len(product_urls)} product URLs in {category}")
        return product_urls
    
    def scrape_product_details(self, product_url: str) -> Optional[Dict]:
        """Scrape details from a single product page"""
        soup = self.get_page(product_url)
        
        if not soup:
            self.logger.warning(f"Failed to fetch product page: {product_url}")
            return None
        
        product_data = {
            'url': product_url,
            'source': 'EWG Skin Deep',
            'product_name': '',
            'brand': '',
            'price': '',
            'rating': '',
            'ingredients': [],
            'date_published': '',
            'hazard_score': ''
        }
        
        try:
            # Debug: Let's see what we actually have in the HTML
            self.logger.debug(f"Page title: {soup.title.string if soup.title else 'No title'}")
            
            # Extract product name - try multiple approaches
            name_elem = (soup.find('h1') or 
                        soup.find('title') or
                        soup.find('h2'))
            
            if name_elem:
                name_text = self.clean_text(name_elem.get_text())
                
                # Clean up the title if it came from <title> tag
                if 'EWG Skin Deep' in name_text:
                    name_text = name_text.replace('EWG Skin Deep', '').replace('|', '').strip()
                
                # Clean up common artifacts in product names
                name_text = re.sub(r'^®\s*', '', name_text)  # Remove leading ®
                name_text = re.sub(r'\s+Rating$', '', name_text)  # Remove trailing "Rating"
                name_text = re.sub(r'\s+Product$', '', name_text)  # Remove trailing "Product"
                name_text = re.sub(r'\s*-\s*EWG.*$', '', name_text)  # Remove EWG suffixes
                
                # Clean up extra whitespace
                name_text = re.sub(r'\s+', ' ', name_text).strip()
                
                product_data['product_name'] = name_text
            
            # Extract brand - try multiple approaches
            brand_found = False
            
            # Method 1: Look for brand links
            brand_elem = soup.find('a', href=re.compile(r'/skindeep/browse/brand/'))
            if brand_elem:
                brand_text = self.clean_text(brand_elem.get_text())
                if brand_text and len(brand_text) > 1:
                    product_data['brand'] = brand_text
                    brand_found = True
            
            # Method 2: Look in breadcrumbs (but skip category breadcrumbs)
            if not brand_found:
                breadcrumb_elems = soup.find_all('a', href=re.compile(r'/skindeep/browse/'))
                for elem in breadcrumb_elems:
                    text = self.clean_text(elem.get_text())
                    href = elem.get('href', '')
                    # Skip category breadcrumbs - they have /category/ in URL or are common categories
                    if (text and len(text) > 2 and 
                        '/category/' not in href and  # Skip category URLs
                        not any(word in text.lower() for word in 
                               ['browse', 'category', 'facial', 'moisturizer', 'cleanser', 'face', 'anti', 'aging', 
                                'cream', 'bb', 'cc', 'around', 'eye', 'remover', 'mask', 'oil', 'treatment'])):
                        product_data['brand'] = text
                        brand_found = True
                        break
            
            # Method 3: Look for "More from [Brand]" sections
            if not brand_found:
                # Look in all text content for "More from" patterns
                all_text = soup.get_text()
                more_from_match = re.search(r'More from ([A-Za-z\s&\.]{3,30})', all_text, re.I)
                
                if more_from_match:
                    potential_brand = more_from_match.group(1).strip()
                    # Clean up the brand name
                    potential_brand = re.sub(r'\s+', ' ', potential_brand)  # Multiple spaces to single
                    
                    if (potential_brand and len(potential_brand) > 2 and
                        not any(word in potential_brand.lower() for word in 
                               ['product', 'company', 'brand', 'products', 'more'])):
                        product_data['brand'] = potential_brand
                        brand_found = True
            
            # Method 4: Extract from product name
            if not brand_found and product_data['product_name']:
                name_words = product_data['product_name'].split()
                
                # For products like "Be Natural Organics Squalane Serum Light"
                # The brand is often the first few capitalized words before product type words
                potential_brand_parts = []
                
                for i, word in enumerate(name_words):
                    # Skip common non-brand words at the beginning
                    if word.lower() in ['the', 'a', 'an']:
                        continue
                    
                    # Check if this could be part of a brand name
                    if (len(word) > 1 and 
                        word.istitle() and  # Capitalized
                        not word.lower() in ['face', 'facial', 'skin', 'cream', 'lotion', 'serum', 'oil', 'treatment', 'light', 'dark', 'day', 'night']):
                        
                        # Common brand words that can be part of brand names
                        if word.lower() in ['natural', 'organic', 'pure', 'botanics', 'labs', 'cosmetics', 'beauty']:
                            potential_brand_parts.append(word)
                        # Regular brand words (not descriptive)
                        elif not word.lower() in ['100%', '&', 'and']:
                            potential_brand_parts.append(word)
                    else:
                        # Hit a product descriptor, stop building brand name
                        break
                
                # Build brand name from collected parts
                if potential_brand_parts:
                    # Take up to 3 words for brand name
                    brand_words = potential_brand_parts[:3]
                    if len(brand_words) >= 1:
                        product_data['brand'] = ' '.join(brand_words)
                        brand_found = True
            
            # Method 5: Extract from URL as last resort
            if not brand_found:
                # Sometimes brand is in the URL path
                url_parts = product_url.split('/')
                for part in url_parts:
                    if '_' in part and len(part) > 4:
                        # URL parts often use underscores, convert to brand name
                        potential_brand = part.replace('_', ' ').title()
                        # Filter out obvious non-brands
                        if not any(word in potential_brand.lower() for word in 
                                  ['products', 'skindeep', 'facial', 'moisturizer', 'cleanser']):
                            words = potential_brand.split()
                            if len(words) >= 1 and len(words[0]) > 2:
                                product_data['brand'] = words[0] if len(words) == 1 else f"{words[0]} {words[1]}"
                                break
            
            # Extract EWG hazard score - look for score indicators
            # Try multiple selectors for scoring
            score_selectors = [
                'div[class*="score"]',
                'span[class*="score"]',
                'div[class*="rating"]',
                'span[class*="rating"]'
            ]
            
            for selector in score_selectors:
                score_elems = soup.select(selector)
                for elem in score_elems:
                    score_text = self.clean_text(elem.get_text())
                    score_match = re.search(r'(\d+)', score_text)
                    if score_match:
                        product_data['hazard_score'] = score_match.group(1)
                        product_data['rating'] = f"{score_match.group(1)}/10"
                        break
                if product_data['hazard_score']:
                    break
            
            # Extract ingredients - this is the most important part!
            # Try multiple approaches since EWG structure varies
            
            # Method 1: Look for ingredient-specific sections
            ingredient_sections = [
                soup.find('div', class_=re.compile(r'ingredient', re.I)),
                soup.find('section', id=re.compile(r'ingredient', re.I)),
                soup.find('div', id=re.compile(r'ingredient', re.I))
            ]
            
            ingredients_found = False
            for section in ingredient_sections:
                if section and not ingredients_found:
                    # Look for lists first
                    ingredient_lists = section.find_all(['ul', 'ol'])
                    for ing_list in ingredient_lists:
                        list_items = ing_list.find_all('li')
                        if list_items:
                            ingredients = []
                            for li in list_items:
                                ing_text = self.clean_text(li.get_text())
                                if ing_text and len(ing_text) > 2:
                                    ingredients.append(ing_text)
                            if ingredients:
                                product_data['ingredients'] = ingredients
                                ingredients_found = True
                                break
                    
                    # If no lists, look for text content
                    if not ingredients_found:
                        section_text = self.clean_text(section.get_text())
                        if section_text and any(word in section_text.lower() for word in ['water', 'aqua', 'glycerin', 'oil', 'acid']):
                            parsed_ingredients = self.parse_ingredients(section_text)
                            if len(parsed_ingredients) > 1:
                                product_data['ingredients'] = parsed_ingredients
                                ingredients_found = True
            
            # Method 2: Search entire page for ingredient patterns
            if not ingredients_found:
                all_text = soup.get_text()
                
                # Look for ingredient list patterns
                ingredient_patterns = [
                    r'ingredient[s]?\s*(?:list)?[:\-]\s*([^.]*(?:water|aqua|glycerin|oil)[^.]*)',
                    r'contains?[:\-]\s*([^.]*(?:water|aqua|glycerin|oil)[^.]*)',
                    r'((?:water|aqua),\s*[^.]*)',  # Starting with water/aqua
                ]
                
                for pattern in ingredient_patterns:
                    matches = re.finditer(pattern, all_text, re.IGNORECASE)
                    for match in matches:
                        potential_ingredients_text = match.group(1) if match.groups() else match.group(0)
                        parsed_ingredients = self.parse_ingredients(potential_ingredients_text)
                        if len(parsed_ingredients) > 2:  # Only use if we found multiple ingredients
                            product_data['ingredients'] = parsed_ingredients
                            ingredients_found = True
                            break
                    if ingredients_found:
                        break
            
            # Method 3: Look for any div/p containing common ingredient words
            if not ingredients_found:
                all_divs_and_ps = soup.find_all(['div', 'p'])
                for elem in all_divs_and_ps:
                    text = self.clean_text(elem.get_text())
                    # Check if this looks like an ingredient list
                    if (len(text) > 20 and  # Reasonable length
                        text.count(',') > 2 and  # Multiple commas suggest list
                        any(word in text.lower() for word in ['water', 'aqua', 'glycerin', 'oil']) and
                        not any(bad_word in text.lower() for bad_word in ['review', 'about', 'company', 'description'])):
                        
                        parsed_ingredients = self.parse_ingredients(text)
                        if len(parsed_ingredients) > 3:  # Good ingredient list
                            product_data['ingredients'] = parsed_ingredients
                            break
            
            self.logger.info(f"Scraped product: {product_data['product_name']} ({len(product_data['ingredients'])} ingredients)")
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error scraping product {product_url}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def scrape_products(self, limit: Optional[int] = None, category: str = 'moisturizer') -> List[Dict]:
        """Main method to scrape products from EWG Skin Deep"""
        self.logger.info(f"Starting EWG scraping for {category} category, limit: {limit}")
        
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
            
            # Be respectful with delays
            if i % 10 == 0:  # Every 10 products, take a longer break
                self.logger.info(f"Processed {i} products, taking a short break...")
                import time
                time.sleep(5)
        
        self.logger.info(f"Successfully scraped {len(products)} products from EWG")
        return products


# Example usage function
def main():
    """Example of how to use the EWG scraper"""
    scraper = EWGScraper(delay=2.0)
    
    try:
        # Scrape 20 moisturizers as a test
        products = scraper.scrape_products(limit=20, category='moisturizer')
        
        if products:
            # Save the data
            scraper.save_data(products, 'ewg_moisturizers_test')
            print(f"Successfully scraped {len(products)} products!")
            
            # Print some sample data
            for product in products[:3]:  # Show first 3 products
                print(f"\nProduct: {product['product_name']}")
                print(f"Brand: {product['brand']}")
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