#!/usr/bin/env python3
"""
Test script for CosDNA scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.cosdna_scraper import CosDNAScraper


def test_cosdna_scraper():
    """Test the CosDNA scraper functionality"""
    print("Testing CosDNA scraper...")
    
    scraper = CosDNAScraper(delay=3.0)
    
    try:
        # Test with a small limit first
        print("\nTesting with 3 products...")
        products = scraper.scrape_products(limit=3, query="facial moisturizer")
        
        if products:
            print(f"\n✓ Successfully scraped {len(products)} products!")
            
            # Save test results
            scraper.save_data(products, 'cosdna_test_results')
            print("✓ Data saved successfully")
            
            # Display sample results
            for i, product in enumerate(products, 1):
                print(f"\n--- Product {i} ---")
                print(f"Name: {product['product_name']}")
                print(f"Brand: {product['brand']}")
                print(f"URL: {product['url']}")
                print(f"Rating: {product['rating']}")
                print(f"Ingredients found: {len(product['ingredients'])}")
                
                if product['ingredients']:
                    print(f"First 5 ingredients: {product['ingredients'][:5]}")
                else:
                    print("No ingredients extracted")
            
            # Test ingredient analysis feature
            print("\n\nTesting ingredient analysis...")
            if products and products[0]['ingredients']:
                test_ingredient = products[0]['ingredients'][0]
                print(f"Analyzing ingredient: {test_ingredient}")
                
                ingredient_info = scraper.scrape_ingredient_analysis(test_ingredient)
                if ingredient_info:
                    print(f"✓ Retrieved analysis for {test_ingredient}")
                    print(f"Safety rating: {ingredient_info.get('safety_rating', 'N/A')}")
                    print(f"Acne rating: {ingredient_info.get('acne_rating', 'N/A')}")
                    print(f"Irritant rating: {ingredient_info.get('irritant_rating', 'N/A')}")
                else:
                    print(f"! No analysis found for {test_ingredient}")
            
            print(f"\n✓ CosDNA scraper test completed successfully!")
            print(f"✓ Average ingredients per product: {sum(len(p['ingredients']) for p in products) / len(products):.1f}")
            
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


def test_search_functionality():
    """Test the search functionality separately"""
    print("\n\nTesting search functionality...")
    
    scraper = CosDNAScraper()
    
    try:
        # Test search
        urls = scraper.search_products("facial cleanser", limit=5)
        
        if urls:
            print(f"✓ Search found {len(urls)} product URLs")
            for i, url in enumerate(urls[:3], 1):
                print(f"  {i}. {url}")
        else:
            print("! No URLs found from search")
            
    except Exception as e:
        print(f"✗ Search test failed: {e}")
    finally:
        scraper.close()


if __name__ == "__main__":
    print("=" * 50)
    print("CosDNA Scraper Test Suite")
    print("=" * 50)
    
    # Run main test
    success = test_cosdna_scraper()
    
    # Run search test
    test_search_functionality()
    
    if success:
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        print("CosDNA scraper is ready for use.")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("✗ Some tests failed. Check the output above.")
        print("=" * 50)
        sys.exit(1)