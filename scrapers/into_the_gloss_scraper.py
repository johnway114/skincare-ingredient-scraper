from typing import List, Dict, Optional
import re
import time
from urllib.parse import urljoin, quote
from .base_scraper import BaseScraper


class IntoTheGlossScraper(BaseScraper):
    """Scraper for Into The Gloss beauty blog and product recommendations"""
    
    def __init__(self, delay: float = 2.0):
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://intothegloss.com"
        
        # Add specific headers for Into The Gloss
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
        """Search for Into The Gloss articles about skincare products"""
        
        # Known article URLs for Into The Gloss (skincare-focused articles)
        known_articles = [
            "https://intothegloss.com/2023/12/best-moisturizers-dry-skin",
            "https://intothegloss.com/2023/11/gentle-cleansers-sensitive-skin",
            "https://intothegloss.com/2023/10/luxury-skincare-worth-splurge",
            "https://intothegloss.com/2023/09/affordable-skincare-drugstore",
            "https://intothegloss.com/2023/08/korean-skincare-routine",
            "https://intothegloss.com/2023/07/french-pharmacy-skincare",
            "https://intothegloss.com/2023/06/double-cleansing-method",
            "https://intothegloss.com/2023/05/night-creams-anti-aging",
            "https://intothegloss.com/2023/04/gel-moisturizers-oily-skin",
            "https://intothegloss.com/2023/03/cream-cleansers-winter"
        ]
        
        article_urls = []
        
        # Filter known articles by category
        if category == "moisturizer":
            relevant_articles = [url for url in known_articles if any(word in url for word in ["moisturizer", "night-cream", "gel-moisturizer", "korean", "luxury", "affordable"])]
        elif category == "cleanser":
            relevant_articles = [url for url in known_articles if any(word in url for word in ["cleanser", "cleansing", "double", "cream-cleanser"])]
        else:
            relevant_articles = known_articles
        
        # Test each article URL
        for article_url in relevant_articles:
            try:
                response = self.get_page(article_url)
                if response and response.status_code == 200:
                    article_urls.append(article_url)
                    self.logger.info(f"Found working article: {article_url}")
                    
                    if limit and len(article_urls) >= limit:
                        break
                        
            except Exception as e:
                self.logger.warning(f"Could not access article {article_url}: {e}")
                continue
                
            time.sleep(self.delay)
        
        self.logger.info(f"Found {len(article_urls)} working Into The Gloss articles")
        return article_urls
    
    def scrape_article_products(self, article_url: str) -> List[Dict]:
        """Extract product recommendations from an Into The Gloss article"""
        products = []
        
        try:
            response = self.get_page(article_url)
            if not response or response.status_code != 200:
                self.logger.error(f"Failed to fetch article: {article_url}")
                return products
            
            soup = self.create_soup(response.text)
            if not soup:
                return products
            
            # Look for product recommendations in the article content
            content_div = soup.find('div', class_='entry-content') or soup.find('article') or soup.find('main')
            
            if not content_div:
                self.logger.warning(f"Could not find main content in article: {article_url}")
                return products
            
            # Extract product names and brands from text and links
            products = self._extract_products_from_content(content_div, article_url)
            
        except Exception as e:
            self.logger.error(f"Error scraping article {article_url}: {e}")
        
        return products
    
    def _extract_products_from_content(self, content_div, source_url: str) -> List[Dict]:
        """Extract product names and brands from article content"""
        products = []
        
        # First try to find product links
        product_links = content_div.find_all('a', href=True)
        for link in product_links:
            href = link.get('href', '')
            link_text = link.get_text().strip()
            
            # Skip if not a product link
            if not any(domain in href for domain in ['sephora.com', 'ulta.com', 'amazon.com', 'target.com', 'dermstore.com']):
                continue
            
            # Extract product info from link text
            product_info = self._parse_product_link_text(link_text)
            if product_info:
                product_info.update({
                    'url': source_url,
                    'source': 'Into The Gloss',
                    'price': None,
                    'rating': None,
                    'ingredients': [],
                    'date_published': None
                })
                products.append(product_info)
        
        # Also extract from text content
        text_products = self._extract_products_from_text(content_div.get_text(), source_url)
        products.extend(text_products)
        
        # Remove duplicates
        seen = set()
        unique_products = []
        for product in products:
            key = (product['product_name'], product['brand'])
            if key not in seen:
                seen.add(key)
                unique_products.append(product)
        
        return unique_products
    
    def _parse_product_link_text(self, link_text: str) -> Optional[Dict]:
        """Parse product information from link text"""
        if len(link_text) < 5:
            return None
        
        # Common patterns for product links
        patterns = [
            # "Brand Product Name" format
            r'^([A-Z][a-zA-Z\s&]+)\s+([A-Z][a-zA-Z\s\-\+\d]+(?:Cream|Cleanser|Moisturiser|Moisturizer|Lotion|Gel|Foam|Oil|Balm))$',
            # "Product Name" only (try to extract brand if possible)
            r'^([A-Z][a-zA-Z\s\-\+\d]+(?:Cream|Cleanser|Moisturiser|Moisturizer|Lotion|Gel|Foam|Oil|Balm))$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, link_text.strip())
            if match:
                if len(match.groups()) == 2:
                    brand = match.group(1).strip()
                    product_name = match.group(2).strip()
                else:
                    # Try to extract brand from product name
                    product_name = match.group(1).strip()
                    brand_match = re.match(r'^([A-Z][a-zA-Z\s&]+)', product_name)
                    brand = brand_match.group(1).strip() if brand_match else "Unknown"
                
                return {
                    'product_name': product_name,
                    'brand': brand
                }
        
        return None
    
    def _extract_products_from_text(self, text: str, source_url: str) -> List[Dict]:
        """Extract product names and brands from article text"""
        products = []
        
        # Common patterns for product mentions in Into The Gloss articles
        product_patterns = [
            # "Brand's Product Name" format
            r"([A-Z][a-zA-Z\s&]+)'s\s+([A-Z][a-zA-Z\s\-\+\d]+(?:Cream|Cleanser|Moisturiser|Moisturizer|Lotion|Gel|Foam|Oil|Balm))",
            # "Brand Product Name" format
            r'([A-Z][a-zA-Z\s&]+)\s+([A-Z][a-zA-Z\s\-\+\d]+(?:Cream|Cleanser|Moisturiser|Moisturizer|Lotion|Gel|Foam|Oil|Balm))',
            # "The Product Name from Brand" format
            r'(?:The\s+)?([A-Z][a-zA-Z\s\-\+\d]+(?:Cream|Cleanser|Moisturiser|Moisturizer|Lotion|Gel|Foam|Oil|Balm))\s+from\s+([A-Z][a-zA-Z\s&]+)',
        ]
        
        for pattern in product_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if "from" in pattern:
                    product_name = match.group(1).strip()
                    brand = match.group(2).strip()
                else:
                    brand = match.group(1).strip()
                    product_name = match.group(2).strip()
                
                # Clean up extracted text
                brand = re.sub(r'[^\w\s&\-]', '', brand).strip()
                product_name = re.sub(r'[^\w\s&\-\+\d]', '', product_name).strip()
                
                # Skip if too short or likely false positives
                if len(brand) < 2 or len(product_name) < 5:
                    continue
                
                # Skip common false positives
                false_positives = ['The Best', 'My Favorite', 'Top Pick', 'Must Have', 'Holy Grail']
                if any(fp in brand for fp in false_positives):
                    continue
                
                product_data = {
                    'product_name': product_name,
                    'brand': brand,
                    'url': source_url,
                    'source': 'Into The Gloss',
                    'price': None,
                    'rating': None,
                    'ingredients': [],
                    'date_published': None
                }
                
                products.append(product_data)
        
        return products
    
    def scrape_products(self, category: str = "moisturizer", limit: Optional[int] = None) -> List[Dict]:
        """Main scraping method"""
        self.logger.info(f"Starting Into The Gloss scraping for {category}, limit: {limit}")
        
        # Find relevant articles
        article_urls = self.search_articles(category, limit)
        
        if not article_urls:
            self.logger.warning("No working articles found")
            return []
        
        all_products = []
        
        for i, article_url in enumerate(article_urls):
            self.logger.info(f"Scraping article {i+1}/{len(article_urls)}: {article_url}")
            
            products = self.scrape_article_products(article_url)
            all_products.extend(products)
            
            if limit and len(all_products) >= limit:
                all_products = all_products[:limit]
                break
                
            time.sleep(self.delay)
        
        self.logger.info(f"Successfully scraped {len(all_products)} products from Into The Gloss")
        return all_products