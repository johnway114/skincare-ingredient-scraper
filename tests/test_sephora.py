#!/usr/bin/env python3
"""
Test script for Sephora scraper
"""

import sys
import os

# Add the project root to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.sephora_scraper import SephoraScraper

def test_sephora_scraper():
    """Test the Sephora scraper with a small sample"""
    print("🧪 Testing Sephora Scraper...")
    print("=" * 50)
    print("⚠️  Note: This test uses browser automation and may take several minutes")
    
    # Create scraper instance with longer delays for Sephora
    scraper = SephoraScraper(delay=4.0)
    
    try:
        print("📋 Step 1: Testing product URL collection...")
        
        # Try to get some product URLs
        product_urls = scraper.get_product_urls(category='moisturizer', limit=3)
        
        if product_urls:
            print(f"✅ Successfully found {len(product_urls)} product URLs")
            print("Sample URLs:")
            for i, url in enumerate(product_urls[:2], 1):
                print(f"  {i}. {url}")
        else:
            print("❌ No product URLs found - this might indicate blocking or site changes")
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
                print(f"Price: {product_data['price']}")
                print(f"Rating: {product_data['rating']}")
                print(f"Number of ingredients: {len(product_data['ingredients'])}")
                
                if product_data['ingredients']:
                    print("First 3 ingredients:")
                    for i, ingredient in enumerate(product_data['ingredients'][:3], 1):
                        print(f"  {i}. {ingredient}")
                else:
                    print("⚠️  No ingredients found - this is expected for Sephora due to dynamic content")
                
                print(f"Source: {product_data['source']}")
                print(f"URL: {product_data['url']}")
                
            else:
                print("❌ Failed to scrape product data")
                return False
        
        print("\n💾 Step 3: Testing small batch scraping...")
        
        # Try to scrape 2 products
        products = scraper.scrape_products(limit=2, category='moisturizer')
        
        if products:
            print(f"✅ Successfully scraped {len(products)} products!")
            
            # Save the test data
            scraper.save_data(products, 'sephora_test_results')
            print("✅ Data saved to sephora_test_results.csv and sephora_test_results.json")
            
            # Show summary statistics
            total_ingredients = sum(len(p['ingredients']) for p in products)
            products_with_ingredients = sum(1 for p in products if p['ingredients'])
            products_with_prices = sum(1 for p in products if p['price'])
            
            print(f"\n📊 Summary:")
            print(f"  • Total products scraped: {len(products)}")
            print(f"  • Products with prices: {products_with_prices}")
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

if __name__ == "__main__":
    success = test_sephora_scraper()
    
    if success:
        print("\n🎉 Sephora scraper test completed successfully!")
        print("You can check the results in:")
        print("  • data/sephora_test_results.csv")
        print("  • data/sephora_test_results.json")
        print("  • logs/SephoraScraper.log")
    else:
        print("\n💥 Sephora scraper test failed!")
        print("This may be due to:")
        print("  • Sephora's anti-bot measures")
        print("  • Site structure changes")
        print("  • Network issues")
        print("Check the logs/SephoraScraper.log file for more details")
    
    print("\n" + "=" * 50)