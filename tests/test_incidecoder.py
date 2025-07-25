#!/usr/bin/env python3
"""
Test script for INCIDecoder scraper
"""

import sys
import os

# Add the project root to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.incidecoder_scraper import INCIDecoderScraper

def test_incidecoder_scraper():
    """Test the INCIDecoder scraper with a small sample"""
    print("🧪 Testing INCIDecoder Scraper...")
    print("=" * 50)
    
    # Create scraper instance
    scraper = INCIDecoderScraper(delay=2.0)
    
    try:
        print("📋 Step 1: Testing product URL collection...")
        
        # Try to get some product URLs
        product_urls = scraper.get_product_urls(limit=5)
        
        if product_urls:
            print(f"✅ Successfully found {len(product_urls)} product URLs")
            print("Sample URLs:")
            for i, url in enumerate(product_urls[:3], 1):
                print(f"  {i}. {url}")
        else:
            print("❌ No product URLs found")
            return False
        
        print("\n🔍 Step 2: Testing individual product scraping...")
        
        # Try to scrape just the first product
        if product_urls:
            test_url = product_urls[0]
            print(f"Testing with: {test_url}")
            
            product_data = scraper.scrape_product_details(test_url)
            
            if product_data:
                print("✅ Successfully scraped product data!")
                print(f"Product Name: {product_data['product_name']}")
                print(f"Brand: {product_data['brand']}")
                print(f"Rating: {product_data['rating']}")
                print(f"Number of ingredients: {len(product_data['ingredients'])}")
                
                if product_data['ingredients']:
                    print("First 5 ingredients:")
                    for i, ingredient in enumerate(product_data['ingredients'][:5], 1):
                        print(f"  {i}. {ingredient}")
                else:
                    print("⚠️  No ingredients found - this might indicate parsing issues")
                
                print(f"Source: {product_data['source']}")
                
            else:
                print("❌ Failed to scrape product data")
                return False
        
        print("\n💾 Step 3: Testing full scraping and data saving...")
        
        # Try to scrape 3 products
        products = scraper.scrape_products(limit=3)
        
        if products:
            print(f"✅ Successfully scraped {len(products)} products!")
            
            # Save the test data
            scraper.save_data(products, 'incidecoder_test_results')
            print("✅ Data saved to incidecoder_test_results.csv and incidecoder_test_results.json")
            
            # Show summary statistics
            total_ingredients = sum(len(p['ingredients']) for p in products)
            products_with_ingredients = sum(1 for p in products if p['ingredients'])
            products_with_brands = sum(1 for p in products if p['brand'])
            
            print(f"\n📊 Summary:")
            print(f"  • Total products scraped: {len(products)}")
            print(f"  • Products with brands: {products_with_brands}")
            print(f"  • Products with ingredients: {products_with_ingredients}")
            print(f"  • Total ingredients found: {total_ingredients}")
            if products:
                print(f"  • Average ingredients per product: {total_ingredients/len(products):.1f}")
            
            return True
        else:
            print("❌ No products were successfully scraped")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Always clean up
        scraper.close()
        print("\n🧹 Cleaned up scraper resources")

def test_ingredient_lookup():
    """Test the ingredient lookup functionality"""
    print("\n🧪 Testing Ingredient Lookup...")
    print("=" * 30)
    
    scraper = INCIDecoderScraper(delay=1.0)
    
    try:
        # Test looking up a common ingredient
        test_ingredients = ['glycerin', 'hyaluronic acid', 'vitamin c']
        
        for ingredient in test_ingredients:
            print(f"Looking up: {ingredient}")
            ingredient_data = scraper.scrape_ingredient_info(ingredient)
            
            if ingredient_data:
                print(f"✅ Found data for {ingredient}")
                print(f"  Function: {ingredient_data['function']}")
                print(f"  Description: {ingredient_data['description'][:100]}..." if ingredient_data['description'] else "  No description")
            else:
                print(f"❌ No data found for {ingredient}")
            print()
            
    except Exception as e:
        print(f"❌ Error during ingredient testing: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    success = test_incidecoder_scraper()
    
    if success:
        print("\n🎉 INCIDecoder scraper test completed successfully!")
        print("You can check the results in:")
        print("  • data/incidecoder_test_results.csv")
        print("  • data/incidecoder_test_results.json")
        print("  • logs/INCIDecoderScraper.log")
        
        # Test ingredient lookup functionality
        test_ingredient_lookup()
        
    else:
        print("\n💥 INCIDecoder scraper test failed!")
        print("Check the logs/INCIDecoderScraper.log file for more details")
    
    print("\n" + "=" * 50)