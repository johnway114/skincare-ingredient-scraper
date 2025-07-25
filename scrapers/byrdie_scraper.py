from typing import List, Dict, Optional
import re
import time
from urllib.parse import urljoin, quote
from .base_scraper import BaseScraper


class ByrdieScraper(BaseScraper):
    """Scraper for Byrdie beauty content and product recommendations"""
    
    def __init__(self, delay: float = 2.0):
        # Byrdie is content-focused, should work with requests
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://www.byrdie.com"
        
        # Add specific headers for Byrdie
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
        
    def search_articles(self, category: str = "moisturizer", limit: Optional[int] = None) -> List[str]:
        """Search for Byrdie articles about skincare products"""
        
        # Try known working article URLs first (common Byrdie skincare articles)
        known_articles = [
            "https://www.byrdie.com/best-moisturizers-dry-skin",
            "https://www.byrdie.com/best-face-moisturizers", 
            "https://www.byrdie.com/best-facial-cleansers",
            "https://www.byrdie.com/best-cleansers-dry-skin",
            "https://www.byrdie.com/best-anti-aging-moisturizers",
            "https://www.byrdie.com/best-drugstore-moisturizers",
            "https://www.byrdie.com/best-gel-moisturizers",
            "https://www.byrdie.com/sensitive-skin-moisturizers"
        ]
        
        article_urls = []
        
        # Filter known articles by category
        if category == "moisturizer":
            relevant_articles = [url for url in known_articles if "moisturizer" in url]
        elif category == "cleanser":
            relevant_articles = [url for url in known_articles if "cleanser" in url or "cleaner" in url]
        else:
            relevant_articles = known_articles
        
        # Test these known URLs first
        for article_url in relevant_articles:
            if limit and len(article_urls) >= limit:
                break
                
            # Quick test to see if the article is accessible
            soup = self.get_page(article_url)
            if soup and soup.find('title'):
                article_urls.append(article_url)
                self.logger.info(f"Verified accessible article: {article_url}")
        
        # If we found some articles, return them
        if article_urls:
            return article_urls[:limit] if limit else article_urls
        
        # Fallback: Try search approach with better queries
        if category == "moisturizer":
            search_queries = [
                "facial-moisturizer",
                "best-moisturizers", 
                "skincare-moisturizer",
                "hydrating-cream"
            ]
        elif category == "cleanser":
            search_queries = [
                "facial-cleanser",
                "best-cleansers",
                "face-wash",
                "cleansing-balm"
            ]
        else:
            search_queries = [f"best-{category}", f"facial-{category}"]
        
        article_urls = []
        
        for query in search_queries:
            # Try different URL patterns Byrdie uses
            search_urls = [
                f"{self.base_url}/search?q={query}",
                f"{self.base_url}/tag/{query}",
                f"{self.base_url}/skincare/{query}",
                f"{self.base_url}/{query}"
            ]
            
            for search_url in search_urls:
                soup = self.get_page(search_url)
                
                if soup:
                    # Look for article links
                    article_selectors = [
                        'a[href*="/skincare/"]',
                        'a[href*="/best-"]',
                        'a[href*="/moisturizer"]',
                        'a[href*="/cleanser"]',
                        '.card-link',
                        '.article-link a',
                        'h2 a',
                        'h3 a'
                    ]
                    
                    for selector in article_selectors:
                        links = soup.select(selector)
                        if links:
                            self.logger.info(f"Found article links using selector: {selector}")
                            for link in links:
                                href = link.get('href')
                                if href:
                                    full_url = urljoin(self.base_url, href)
                                    # Filter for relevant skincare articles
                                    if any(keyword in full_url.lower() for keyword in 
                                          ['moisturizer', 'cleanser', 'skincare', 'best-', 'serum', 'cream']):
                                        if full_url not in article_urls:
                                            article_urls.append(full_url)
                                            if limit and len(article_urls) >= limit:
                                                return article_urls
                            break
                    
                    if article_urls:
                        break
            
            if article_urls:
                break
        
        # If no specific searches work, try browsing skincare section
        if not article_urls:
            browse_urls = [
                f"{self.base_url}/skincare",
                f"{self.base_url}/beauty",
                f"{self.base_url}/makeup"
            ]
            
            for browse_url in browse_urls:
                soup = self.get_page(browse_url)
                if soup:
                    links = soup.select('a[href*="/skincare/"], a[href*="/best-"]')
                    for link in links[:limit] if limit else links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            if full_url not in article_urls:
                                article_urls.append(full_url)
                    if article_urls:
                        break
        
        self.logger.info(f"Found {len(article_urls)} Byrdie articles")
        return article_urls
    
    def extract_products_from_article(self, article_url: str) -> List[Dict]:
        """Extract product mentions and recommendations from a Byrdie article"""
        soup = self.get_page(article_url)
        
        if not soup:
            self.logger.warning(f"Failed to fetch article: {article_url}")
            return []
        
        products = []
        
        try:
            # Get article title for context
            article_title = ""
            title_selectors = ['h1', '.article-title', 'title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    article_title = self.clean_text(title_elem.get_text())
                    break
            
            # Extract product mentions from the article content
            content_selectors = [
                '.article-content',
                '.post-content', 
                '.content',
                'main',
                '.entry-content'
            ]
            
            content_soup = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content_soup = content_elem
                    break
            
            if not content_soup:
                content_soup = soup  # Use whole page if can't find content area
            
            # Look for product names and descriptions
            # Byrdie often structures products in lists or sections
            product_sections = content_soup.select('h2, h3, .product-rec, .recommendation, li')
            
            for i, section in enumerate(product_sections):
                section_text = section.get_text()
                
                # Skip if section is too short to contain product info
                if len(section_text.strip()) < 20:
                    continue
                
                # Look for product name patterns
                product_patterns = [
                    r'([A-Z][a-zA-Z\s&]+(?:Moisturizer|Cream|Cleanser|Serum|Oil|Balm|Wash|Gel))',
                    r'([A-Z][a-zA-Z\s&]+\s+(?:Face|Facial|Skin)[\s\w]*)',
                    r'([A-Z][a-zA-Z\s&]{10,50}(?:\$[\d,]+)?)'
                ]
                
                for pattern in product_patterns:
                    matches = re.finditer(pattern, section_text)
                    for match in matches:
                        potential_product = match.group(1).strip()
                        
                        # Clean up the product name
                        potential_product = re.sub(r'\s+', ' ', potential_product)
                        
                        if len(potential_product) > 10 and len(potential_product) < 100:
                            # Extract brand (usually first word or two)
                            words = potential_product.split()
                            if len(words) >= 2:
                                potential_brand = words[0]
                                if len(words) >= 3 and len(words[1]) < 10:
                                    potential_brand = f"{words[0]} {words[1]}"
                                
                                # Look for ingredients in surrounding text
                                surrounding_text = ""
                                if i > 0:
                                    surrounding_text += product_sections[i-1].get_text()
                                surrounding_text += section_text
                                if i < len(product_sections) - 1:
                                    surrounding_text += product_sections[i+1].get_text()
                                
                                ingredients = self.extract_ingredients_from_text(surrounding_text)
                                
                                # Look for price in surrounding text
                                price = ""
                                price_match = re.search(r'\$[\d,]+(?:\.\d{2})?', surrounding_text)
                                if price_match:
                                    price = price_match.group(0)
                                
                                product_data = {
                                    'url': article_url,
                                    'source': 'Byrdie',
                                    'product_name': potential_product,
                                    'brand': potential_brand,
                                    'price': price,
                                    'rating': '',
                                    'ingredients': ingredients,
                                    'date_published': self.extract_publish_date(soup),
                                    'hazard_score': '',
                                    'article_title': article_title
                                }
                                
                                products.append(product_data)
            
            # Also look for structured product data (if Byrdie uses it)
            structured_products = content_soup.select('[data-product], .product-card, .rec-product')
            for product_elem in structured_products:
                product_name = ""
                brand = ""
                price = ""
                
                # Try to extract structured data
                name_elem = product_elem.select_one('.product-name, .title, h3, h4')
                if name_elem:
                    product_name = self.clean_text(name_elem.get_text())
                
                brand_elem = product_elem.select_one('.brand, .product-brand')
                if brand_elem:
                    brand = self.clean_text(brand_elem.get_text())
                
                price_elem = product_elem.select_one('.price, .product-price')
                if price_elem:
                    price = self.clean_text(price_elem.get_text())
                
                if product_name:
                    product_text = product_elem.get_text()
                    ingredients = self.extract_ingredients_from_text(product_text)
                    
                    product_data = {
                        'url': article_url,
                        'source': 'Byrdie',
                        'product_name': product_name,
                        'brand': brand,
                        'price': price,
                        'rating': '',
                        'ingredients': ingredients,
                        'date_published': self.extract_publish_date(soup),
                        'hazard_score': '',
                        'article_title': article_title
                    }
                    
                    products.append(product_data)
            
            # Remove duplicates based on product name
            seen_products = set()
            unique_products = []
            for product in products:
                product_key = product['product_name'].lower().strip()
                if product_key not in seen_products and len(product_key) > 5:
                    seen_products.add(product_key)
                    unique_products.append(product)
            
            self.logger.info(f"Extracted {len(unique_products)} products from article: {article_title[:50]}...")
            return unique_products
            
        except Exception as e:
            self.logger.error(f"Error extracting products from article {article_url}: {e}")
            return []
    
    def extract_ingredients_from_text(self, text: str) -> List[str]:
        """Extract ingredients mentioned in article text"""
        # Look for ingredient mentions in text
        ingredient_patterns = [
            r'(?:contains?|with|featuring|includes?)\s+([^.]*(?:acid|oil|extract|peptide|vitamin|retinol|glycerin|hyaluronic)[^.]*)',
            r'(?:ingredients?|formula)\s*:?\s*([^.]*(?:water|aqua|glycerin|oil)[^.]*)',
            r'(?:key ingredients?|active ingredients?)\s*:?\s*([^.]*)',
        ]
        
        ingredients = []
        for pattern in ingredient_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                potential_ingredients = match.group(1) if match.groups() else match.group(0)
                parsed = self.parse_ingredients(potential_ingredients)
                if len(parsed) > 0:
                    ingredients.extend(parsed)
        
        # Also look for common skincare ingredients mentioned individually
        common_ingredients = [
            'hyaluronic acid', 'retinol', 'vitamin c', 'vitamin e', 'niacinamide',
            'glycerin', 'ceramides', 'peptides', 'salicylic acid', 'glycolic acid',
            'lactic acid', 'squalane', 'jojoba oil', 'argan oil', 'rosehip oil'
        ]
        
        text_lower = text.lower()
        for ingredient in common_ingredients:
            if ingredient in text_lower:
                ingredients.append(ingredient.title())
        
        # Remove duplicates
        return list(set(ingredients))
    
    def extract_publish_date(self, soup) -> str:
        """Extract publication date from article"""
        date_selectors = [
            'time[datetime]',
            '.publish-date',
            '.article-date',
            '[data-published]',
            'meta[property="article:published_time"]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get('content') or date_elem.get_text()
                if date_text:
                    return self.clean_text(date_text)
        
        return ""
    
    def scrape_products(self, limit: Optional[int] = None, category: str = "moisturizer") -> List[Dict]:
        """Main method to scrape products from Byrdie articles"""
        self.logger.info(f"Starting Byrdie scraping for {category}, limit: {limit}")
        
        # Get article URLs
        article_urls = self.search_articles(category, limit=min(10, limit) if limit else 10)
        
        if not article_urls:
            self.logger.warning("No Byrdie articles found")
            return []
        
        # Extract products from each article
        all_products = []
        articles_processed = 0
        
        for i, url in enumerate(article_urls, 1):
            self.logger.info(f"Processing Byrdie article {i}/{len(article_urls)}")
            
            products = self.extract_products_from_article(url)
            all_products.extend(products)
            articles_processed += 1
            
            # Check if we have enough products
            if limit and len(all_products) >= limit:
                all_products = all_products[:limit]
                break
            
            time.sleep(self.delay)
        
        # Remove duplicates across articles
        seen_products = set()
        unique_products = []
        for product in all_products:
            product_key = product['product_name'].lower().strip()
            if product_key not in seen_products:
                seen_products.add(product_key)
                unique_products.append(product)
        
        self.logger.info(f"Successfully scraped {len(unique_products)} unique products from {articles_processed} Byrdie articles")
        return unique_products


# Example usage function
def main():
    """Example of how to use the Byrdie scraper"""
    scraper = ByrdieScraper(delay=2.0)
    
    try:
        # Scrape products from Byrdie articles
        products = scraper.scrape_products(limit=10, category="moisturizer")
        
        if products:
            # Save the data
            scraper.save_data(products, 'byrdie_products_test')
            print(f"Successfully scraped {len(products)} products!")
            
            # Print some sample data
            for product in products[:3]:
                print(f"\nProduct: {product['product_name']}")
                print(f"Brand: {product['brand']}")
                print(f"Price: {product['price']}")
                print(f"Ingredients: {len(product['ingredients'])} found")
                print(f"Article: {product['article_title'][:50]}...")
                if product['ingredients']:
                    print(f"Ingredients: {product['ingredients'][:3]}")
        else:
            print("No products were scraped successfully")
            
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()