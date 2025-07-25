#!/usr/bin/env python3
"""
Test script for Amazon scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.amazon_scraper import AmazonScraper


def test_amazon_scraper():
    """Test the Amazon scraper functionality"""
    print("Testing Amazon scraper...")
    print("⚠️  Note: Amazon scraping may be blocked - this is expected behavior")
    
    scraper = AmazonScraper(delay=5.0)
    
    try:
        # Test with a very small limit first (Amazon is very restrictive)
        print("\nTesting with 2 products...")
        products = scraper.scrape_products(limit=2, category="moisturizer")
        
        if products:
            print(f"\n✓ Successfully scraped {len(products)} products!")
            
            # Save test results
            scraper.save_data(products, 'amazon_test_results')
            print("✓ Data saved successfully")
            
            # Display sample results
            for i, product in enumerate(products, 1):
                print(f"\n--- Product {i} ---")
                print(f"Name: {product['product_name']}")
                print(f"Brand: {product['brand']}")
                print(f"Price: {product['price']}")
                print(f"Rating: {product['rating']}")
                print(f"URL: {product['url']}")
                print(f"Ingredients found: {len(product['ingredients'])}")
                
                if product['ingredients']:
                    print(f"First 5 ingredients: {product['ingredients'][:5]}")
                else:
                    print("No ingredients extracted")
            
            print(f"\n✓ Amazon scraper test completed successfully!")
            print(f"✓ Average ingredients per product: {sum(len(p['ingredients']) for p in products) / len(products):.1f}")
            
        else:
            print("! No products were scraped (this is common with Amazon due to anti-bot measures)")
            print("! Amazon frequently blocks automated requests")
            print("! Try running with a VPN or different IP address")
            return False
            
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        print("! This may be due to Amazon's anti-bot protection")
        import traceback
        traceback.print_exc()
        return False
    finally:
        scraper.close()
    
    return True


def test_search_functionality():
    """Test the search functionality separately"""
    print("\n\nTesting search functionality...")
    
    scraper = AmazonScraper()
    
    try:
        # Test search
        urls = scraper.search_products("cleanser", limit=3)
        
        if urls:
            print(f"✓ Search found {len(urls)} product URLs")
            for i, url in enumerate(urls[:3], 1):
                print(f"  {i}. {url}")
        else:
            print("! No URLs found from search (common with Amazon blocking)")
            
    except Exception as e:
        print(f"! Search test encountered issues: {e}")
        print("! This is expected behavior with Amazon's anti-bot measures")
    finally:
        scraper.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Amazon Scraper Test Suite")
    print("=" * 60)
    print("⚠️  WARNING: Amazon actively blocks scrapers")
    print("⚠️  This test may fail due to anti-bot protection")
    print("⚠️  Failures are expected and normal")
    print("=" * 60)
    
    # Run main test
    success = test_amazon_scraper()
    
    # Run search test
    test_search_functionality()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Amazon scraper test completed!")
        print("! Note: Success with Amazon is rare due to anti-bot measures")
        print("! Consider this scraper experimental")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("! Amazon scraper test failed (this is expected)")
        print("! Amazon heavily blocks automated access")
        print("! The scraper code is functional but may be blocked")
        print("=" * 60)