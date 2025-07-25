#!/usr/bin/env python3
"""
Test script for EWG scraper
"""

import sys
import os

# Add the project root to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.ewg_scraper import EWGScraper

def test_ewg_scraper():
    """Test the EWG scraper with a small sample"""
    print("🧪 Testing EWG Scraper...")
    print("=" * 50)
    
    # Create scraper instance with a 3-second delay to be extra polite
    scraper = EWGScraper(delay=3.0)
    
    try:
        print("📋 Step 1: Testing product URL collection...")
        
        # First, let's just try to get some product URLs without scraping them
        product_urls = scraper.get_product_urls(category='moisturizer', limit=5)
        
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
                print(f"Rating/Score: {product_data['rating']}")
                print(f"Hazard Score: {product_data['hazard_score']}")
                print(f"Number of ingredients: {len(product_data['ingredients'])}")
                
                if product_data['ingredients']:
                    print("First 5 ingredients:")
                    for i, ingredient in enumerate(product_data['ingredients'][:5], 1):
                        print(f"  {i}. {ingredient}")
                else:
                    print("⚠️  No ingredients found - this might indicate a parsing issue")
                
                print(f"Source: {product_data['source']}")
                print(f"URL: {product_data['url']}")
                
            else:
                print("❌ Failed to scrape product data")
                return False
        
        print("\n💾 Step 3: Testing full scraping and data saving...")
        
        # Now try to scrape 3 products and save the data
        products = scraper.scrape_products(limit=3, category='moisturizer')
        
        if products:
            print(f"✅ Successfully scraped {len(products)} products!")
            
            # Save the test data
            scraper.save_data(products, 'ewg_test_results')
            print("✅ Data saved to ewg_test_results.csv and ewg_test_results.json")
            
            # Show summary statistics
            total_ingredients = sum(len(p['ingredients']) for p in products)
            products_with_ingredients = sum(1 for p in products if p['ingredients'])
            
            print(f"\n📊 Summary:")
            print(f"  • Total products scraped: {len(products)}")
            print(f"  • Products with ingredients: {products_with_ingredients}")
            print(f"  • Total ingredients found: {total_ingredients}")
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

if __name__ == "__main__":
    success = test_ewg_scraper()
    
    if success:
        print("\n🎉 EWG scraper test completed successfully!")
        print("You can check the results in:")
        print("  • data/ewg_test_results.csv")
        print("  • data/ewg_test_results.json")
        print("  • logs/EWGScraper.log")
    else:
        print("\n💥 EWG scraper test failed!")
        print("Check the logs/EWGScraper.log file for more details")
    
    print("\n" + "=" * 50)