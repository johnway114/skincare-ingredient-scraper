from typing import List, Dict, Optional
import re
import time
from urllib.parse import urljoin, quote
from .base_scraper import BaseScraper


class CosDNAScraper(BaseScraper):
    """Scraper for CosDNA cosmetic ingredient analysis database"""
    
    def __init__(self, delay: float = 3.0):
        # Start with simple requests, may need selenium for some features
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://www.cosdna.com"
        self.search_base = "/eng/product.php"
        
    def search_products(self, query: str = "facial moisturizer", limit: Optional[int] = None) -> List[str]:
        """Search for products and get their URLs"""
        search_url = f"{self.base_url}{self.search_base}"
        
        # Try different search approaches
        search_params = [
            f"?q={quote(query)}",
            f"?search={quote(query)}",
            f"?keyword={quote(query)}"
        ]
        
        product_urls = []
        
        for param in search_params:
            full_search_url = search_url + param
            soup = self.get_page(full_search_url)
            
            if soup:
                # Look for product links
                product_selectors = [
                    'a[href*="/eng/cosmetic_"]',
                    'a[href*="/cosmetic_"]',
                    'a[href*="product"]',
                    '.product-link a',
                    '.search-result a'
                ]
                
                for selector in product_selectors:
                    links = soup.select(selector)
                    if links:
                        for link in links:
                            href = link.get('href')
                            if href:
                                full_url = urljoin(self.base_url, href)
                                if full_url not in product_urls:
                                    product_urls.append(full_url)
                                    if limit and len(product_urls) >= limit:
                                        return product_urls
                        break
                
                if product_urls:
                    break
        
        # If search doesn't work, try browsing approach
        if not product_urls:
            browse_urls = [
                "/eng/brands-products.php",
                "/eng/cosmetic.php",
                "/eng/stuff.php"
            ]
            
            for browse_url in browse_urls:
                soup = self.get_page(self.base_url + browse_url)
                if soup:
                    links = soup.select('a[href*="cosmetic"]')
                    for link in links[:limit] if limit else links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            if full_url not in product_urls:
                                product_urls.append(full_url)
                    if product_urls:
                        break
        
        self.logger.info(f"Found {len(product_urls)} product URLs from CosDNA")
        return product_urls
    
    def scrape_product_details(self, product_url: str) -> Optional[Dict]:
        """Scrape details from a single CosDNA product page"""
        soup = self.get_page(product_url)
        
        if not soup:
            self.logger.warning(f"Failed to fetch product page: {product_url}")
            return None
        
        product_data = {
            'url': product_url,
            'source': 'CosDNA',
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
                'h1',
                '.product-name',
                '[class*="title"]',
                'title'
            ]
            
            for selector in name_selectors:
                if selector == 'title':
                    name_elem = soup.find('title')
                    if name_elem:
                        title_text = name_elem.get_text()
                        # Clean up title
                        title_text = re.sub(r'\s*-\s*CosDNA.*', '', title_text)
                        title_text = re.sub(r'\s*\|\s*CosDNA.*', '', title_text)
                        product_data['product_name'] = self.clean_text(title_text)
                        break
                else:
                    name_elem = soup.select_one(selector)
                    if name_elem:
                        product_data['product_name'] = self.clean_text(name_elem.get_text())
                        break
            
            # Extract brand from product name or page content
            if product_data['product_name']:
                # Look for brand patterns in the name
                name_words = product_data['product_name'].split()
                if len(name_words) > 1:
                    potential_brand = name_words[0]
                    if len(potential_brand) > 2:
                        product_data['brand'] = potential_brand
            
            # Look for brand in specific elements
            brand_selectors = [
                '.brand',
                '[class*="brand"]',
                '.manufacturer'
            ]
            
            for selector in brand_selectors:
                brand_elem = soup.select_one(selector)
                if brand_elem:
                    product_data['brand'] = self.clean_text(brand_elem.get_text())
                    break
            
            # Extract ingredients - CosDNA's main focus
            self.logger.info("Extracting ingredients from CosDNA")
            
            # CosDNA typically shows ingredients in tables or lists
            ingredient_selectors = [
                'table.ing_table',
                '.ingredient-table',
                '.ingredients',
                'table[class*="ingredient"]',
                'tbody tr'
            ]
            
            ingredients_found = False
            
            for selector in ingredient_selectors:
                elements = soup.select(selector)
                if elements:
                    ingredients = []
                    
                    if selector.startswith('table') or 'tbody' in selector:
                        # Handle table format
                        for row in elements:
                            # Look for ingredient names in table cells
                            cells = row.select('td, th')
                            for cell in cells:
                                cell_text = self.clean_text(cell.get_text())
                                # Skip if it's obviously not an ingredient
                                if (cell_text and len(cell_text) > 2 and 
                                    not cell_text.isdigit() and
                                    not any(skip_word in cell_text.lower() for skip_word in 
                                           ['safety', 'acne', 'irritant', 'score', 'rating'])):
                                    
                                    # Check if this looks like an ingredient name
                                    if (len(cell_text) > 3 and 
                                        any(char.isalpha() for char in cell_text)):
                                        ingredients.append(cell_text)
                    else:
                        # Handle list format
                        items = elements[0].select('li, div, span')
                        for item in items:
                            item_text = self.clean_text(item.get_text())
                            if item_text and len(item_text) > 2:
                                ingredients.append(item_text)
                    
                    if ingredients:
                        # Clean and deduplicate ingredients
                        cleaned_ingredients = []
                        seen = set()
                        for ing in ingredients:
                            cleaned = self.clean_text(ing)
                            if cleaned and len(cleaned) > 2 and cleaned.lower() not in seen:
                                seen.add(cleaned.lower())
                                cleaned_ingredients.append(cleaned)
                        
                        if cleaned_ingredients:
                            product_data['ingredients'] = cleaned_ingredients
                            ingredients_found = True
                            break
            
            # If no ingredients found with specific selectors, try broader search
            if not ingredients_found:
                # Look for any text that might be ingredients
                page_text = soup.get_text()
                
                # Common ingredient patterns
                ingredient_patterns = [
                    r'ingredients?\s*:?\s*([^.]*(?:water|aqua|glycerin|oil)[^.]*)',
                    r'inci\s*:?\s*([^.]*(?:water|aqua|glycerin|oil)[^.]*)',
                    r'composition\s*:?\s*([^.]*(?:water|aqua|glycerin|oil)[^.]*)'
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
            
            # Look for ratings or scores (CosDNA has safety ratings)
            rating_selectors = [
                '.safety-score',
                '.rating',
                '[class*="score"]',
                '.acne-score',
                '.irritant-score'
            ]
            
            scores = []
            for selector in rating_selectors:
                score_elem = soup.select_one(selector)
                if score_elem:
                    score_text = score_elem.get_text()
                    score_match = re.search(r'(\d+)', score_text)
                    if score_match:
                        scores.append(score_match.group(1))
            
            if scores:
                product_data['rating'] = '/'.join(scores)
            
            # Look for any additional product information
            meta_desc = soup.select_one('meta[name="description"]')
            if meta_desc and not product_data['ingredients']:
                desc_content = meta_desc.get('content', '')
                if any(word in desc_content.lower() for word in ['ingredient', 'contains']):
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
    
    def scrape_ingredient_analysis(self, ingredient_name: str) -> Optional[Dict]:
        """Scrape CosDNA analysis for a specific ingredient"""
        # CosDNA has ingredient analysis pages
        ingredient_url = f"{self.base_url}/eng/ingredients.php?q={quote(ingredient_name)}"
        
        soup = self.get_page(ingredient_url)
        if not soup:
            return None
        
        ingredient_data = {
            'name': ingredient_name,
            'url': ingredient_url,
            'source': 'CosDNA',
            'safety_rating': '',
            'acne_rating': '',
            'irritant_rating': '',
            'description': ''
        }
        
        try:
            # Look for safety scores
            score_selectors = [
                '.safety',
                '.acne',
                '.irritant',
                '[class*="score"]'
            ]
            
            for selector in score_selectors:
                score_elem = soup.select_one(selector)
                if score_elem:
                    score_text = score_elem.get_text()
                    score_match = re.search(r'(\d+)', score_text)
                    if score_match:
                        if 'safety' in selector:
                            ingredient_data['safety_rating'] = score_match.group(1)
                        elif 'acne' in selector:
                            ingredient_data['acne_rating'] = score_match.group(1)
                        elif 'irritant' in selector:
                            ingredient_data['irritant_rating'] = score_match.group(1)
            
            return ingredient_data
            
        except Exception as e:
            self.logger.error(f"Error analyzing ingredient {ingredient_name}: {e}")
            return None
    
    def scrape_products(self, limit: Optional[int] = None, query: str = "facial moisturizer") -> List[Dict]:
        """Main method to scrape products from CosDNA"""
        self.logger.info(f"Starting CosDNA scraping with query: '{query}', limit: {limit}")
        
        # Get product URLs
        product_urls = self.search_products(query, limit)
        
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
            
            # Be respectful with delays (CosDNA can be sensitive)
            if i % 5 == 0:
                self.logger.info(f"Processed {i} products, taking a longer break...")
                time.sleep(8)
            else:
                time.sleep(self.delay)
        
        self.logger.info(f"Successfully scraped {len(products)} products from CosDNA")
        return products


# Example usage function
def main():
    """Example of how to use the CosDNA scraper"""
    scraper = CosDNAScraper(delay=3.0)
    
    try:
        # Scrape products with a specific query
        products = scraper.scrape_products(limit=5, query="facial moisturizer")
        
        if products:
            # Save the data
            scraper.save_data(products, 'cosdna_products_test')
            print(f"Successfully scraped {len(products)} products!")
            
            # Print some sample data
            for product in products[:2]:
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