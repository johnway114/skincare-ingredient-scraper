from typing import List, Dict, Optional
import re
import time
from urllib.parse import urljoin, quote
from .base_scraper import BaseScraper


class CarolineHironsScraper(BaseScraper):
    """Scraper for Caroline Hirons beauty blog and product recommendations"""
    
    def __init__(self, delay: float = 2.0):
        super().__init__(delay=delay, use_selenium=False)
        self.base_url = "https://www.carolinehirons.com"
        
        # Add specific headers for Caroline Hirons
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
        """Search for Caroline Hirons articles about skincare products"""
        
        # Known article URLs for Caroline Hirons (common skincare articles)
        known_articles = [
            "https://www.carolinehirons.com/2023/07/the-best-cleansers.html",
            "https://www.carolinehirons.com/2023/05/the-best-moisturisers.html",
            "https://www.carolinehirons.com/2022/12/winter-skincare-essentials.html",
            "https://www.carolinehirons.com/2023/03/sensitive-skin-guide.html",
            "https://www.carolinehirons.com/2022/10/dry-skin-solutions.html",
            "https://www.carolinehirons.com/2023/06/luxury-skincare-worth-the-splurge.html",
            "https://www.carolinehirons.com/2023/01/budget-skincare-gems.html",
            "https://www.carolinehirons.com/2022/09/double-cleansing-guide.html"
        ]
        
        article_urls = []
        
        # Filter known articles by category
        if category == "moisturizer":
            relevant_articles = [url for url in known_articles if any(word in url for word in ["moisturis", "winter", "dry", "luxury", "budget"])]
        elif category == "cleanser":
            relevant_articles = [url for url in known_articles if any(word in url for word in ["cleanser", "cleansing", "double"])]
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
        
        self.logger.info(f"Found {len(article_urls)} working Caroline Hirons articles")
        return article_urls
    
    def scrape_article_products(self, article_url: str) -> List[Dict]:
        """Extract product recommendations from a Caroline Hirons article"""
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
            content_div = soup.find('div', class_='post-content') or soup.find('article') or soup.find('main')
            
            if not content_div:
                self.logger.warning(f"Could not find main content in article: {article_url}")
                return products
            
            # Extract product names and brands from text
            products = self._extract_products_from_text(content_div.get_text(), article_url)
            
        except Exception as e:
            self.logger.error(f"Error scraping article {article_url}: {e}")
        
        return products
    
    def _extract_products_from_text(self, text: str, source_url: str) -> List[Dict]:
        """Extract product names and brands from article text"""
        products = []
        
        # Common patterns for product mentions in Caroline Hirons articles
        product_patterns = [
            # "Brand Product Name" format
            r'([A-Z][a-zA-Z\s&]+)\s+([A-Z][a-zA-Z\s\-\+\d]+(?:Cream|Cleanser|Moisturiser|Moisturizer|Lotion|Gel|Foam|Oil|Balm))',
            # "Product Name by Brand" format  
            r'([A-Z][a-zA-Z\s\-\+\d]+(?:Cream|Cleanser|Moisturiser|Moisturizer|Lotion|Gel|Foam|Oil|Balm))\s+by\s+([A-Z][a-zA-Z\s&]+)',
        ]
        
        for pattern in product_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if "by" in pattern:
                    product_name = match.group(1).strip()
                    brand = match.group(2).strip()
                else:
                    brand = match.group(1).strip()
                    product_name = match.group(2).strip()
                
                # Clean up extracted text
                brand = re.sub(r'[^\w\s&\-]', '', brand).strip()
                product_name = re.sub(r'[^\w\s&\-\+\d]', '', product_name).strip()
                
                # Skip if too short or likely false positives
                if len(brand) < 3 or len(product_name) < 5:
                    continue
                
                # Skip common false positives
                false_positives = ['The Best', 'My Top', 'Great For', 'Perfect For', 'Love This']
                if any(fp in brand for fp in false_positives):
                    continue
                
                product_data = {
                    'product_name': product_name,
                    'brand': brand,
                    'url': source_url,
                    'source': 'Caroline Hirons',
                    'price': None,
                    'rating': None,
                    'ingredients': [],
                    'date_published': None
                }
                
                products.append(product_data)
        
        return products
    
    def scrape_products(self, category: str = "moisturizer", limit: Optional[int] = None) -> List[Dict]:
        """Main scraping method"""
        self.logger.info(f"Starting Caroline Hirons scraping for {category}, limit: {limit}")
        
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
        
        self.logger.info(f"Successfully scraped {len(all_products)} products from Caroline Hirons")
        return all_products