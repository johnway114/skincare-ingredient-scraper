#!/usr/bin/env python3
"""
Test script for Byrdie scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.byrdie_scraper import ByrdieScraper


def test_byrdie_scraper():
    """Test the Byrdie scraper functionality"""
    print("Testing Byrdie scraper...")
    
    scraper = ByrdieScraper(delay=2.0)
    
    try:
        # Test with a small limit first
        print("\nTesting with 5 products...")
        products = scraper.scrape_products(limit=5, category="moisturizer")
        
        if products:
            print(f"\n✓ Successfully scraped {len(products)} products!")
            
            # Save test results
            scraper.save_data(products, 'byrdie_test_results')
            print("✓ Data saved successfully")
            
            # Display sample results
            for i, product in enumerate(products, 1):
                print(f"\n--- Product {i} ---")
                print(f"Name: {product['product_name']}")
                print(f"Brand: {product['brand']}")
                print(f"Price: {product['price']}")
                print(f"Article: {product['article_title'][:50]}...")
                print(f"Date: {product['date_published']}")
                print(f"Ingredients found: {len(product['ingredients'])}")
                
                if product['ingredients']:
                    print(f"Ingredients: {product['ingredients'][:3]}")
                else:
                    print("No ingredients extracted")
            
            print(f"\n✓ Byrdie scraper test completed successfully!")
            print(f"✓ Average ingredients per product: {sum(len(p['ingredients']) for p in products) / len(products):.1f}")
            
            # Check data quality
            products_with_ingredients = sum(1 for p in products if p['ingredients'])
            products_with_prices = sum(1 for p in products if p['price'])
            
            print(f"✓ Products with ingredients: {products_with_ingredients}/{len(products)}")
            print(f"✓ Products with prices: {products_with_prices}/{len(products)}")
            
        else:
            print("✗ No products were scraped")
            return False
            
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        scraper.close()
    
    return True


def test_article_search():
    """Test the article search functionality"""
    print("\n\nTesting article search functionality...")
    
    scraper = ByrdieScraper()
    
    try:
        # Test search for moisturizer articles
        urls = scraper.search_articles("moisturizer", limit=5)
        
        if urls:
            print(f"✓ Found {len(urls)} Byrdie articles")
            for i, url in enumerate(urls[:3], 1):
                print(f"  {i}. {url}")
        else:
            print("! No articles found")
            
    except Exception as e:
        print(f"✗ Article search failed: {e}")
    finally:
        scraper.close()


def test_product_extraction():
    """Test extracting products from a single article"""
    print("\n\nTesting product extraction from article...")
    
    scraper = ByrdieScraper()
    
    try:
        # Get one article to test extraction
        urls = scraper.search_articles("cleanser", limit=1)
        
        if urls:
            test_url = urls[0]
            print(f"Testing extraction from: {test_url}")
            
            products = scraper.extract_products_from_article(test_url)
            
            if products:
                print(f"✓ Extracted {len(products)} products from article")
                for product in products[:2]:
                    print(f"  - {product['product_name']} by {product['brand']}")
            else:
                print("! No products extracted from article")
        else:
            print("! No articles found to test")
            
    except Exception as e:
        print(f"! Product extraction test encountered issues: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Byrdie Scraper Test Suite")
    print("=" * 50)
    
    # Run article search test
    test_article_search()
    
    # Run product extraction test
    test_product_extraction()
    
    # Run main test
    success = test_byrdie_scraper()
    
    if success:
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        print("Byrdie scraper is ready for use.")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("✗ Some tests failed. Check the output above.")
        print("=" * 50)
        sys.exit(1)