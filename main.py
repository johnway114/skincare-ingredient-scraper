#!/usr/bin/env python3
"""
Main script for running skincare ingredient scrapers
"""

import argparse
import sys
from scrapers.ewg_scraper import EWGScraper
from scrapers.sephora_scraper import SephoraScraper
from scrapers.incidecoder_scraper import INCIDecoderScraper


def main():
    parser = argparse.ArgumentParser(description='Skincare ingredient scraper')
    parser.add_argument('scraper', choices=['ewg', 'sephora', 'incidecoder'], help='Which scraper to run')
    parser.add_argument('--limit', type=int, default=10, help='Number of products to scrape')
    parser.add_argument('--category', default='moisturizer', choices=['moisturizer', 'cleanser'], 
                       help='Product category to scrape')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests in seconds')
    parser.add_argument('--output', default=None, help='Output filename (without extension)')
    
    args = parser.parse_args()
    
    if args.scraper == 'ewg':
        scraper = EWGScraper(delay=args.delay)
        scraper_name = 'EWG'
    elif args.scraper == 'sephora':
        scraper = SephoraScraper(delay=max(args.delay, 3.0))  # Minimum 3s delay for Sephora
        scraper_name = 'Sephora'
    elif args.scraper == 'incidecoder':
        scraper = INCIDecoderScraper(delay=args.delay)
        scraper_name = 'INCIDecoder'
    
    try:
        if args.scraper == 'incidecoder':
            print(f"Starting {scraper_name} scraper (limit: {args.limit})")
            print("Note: INCIDecoder focuses on ingredient analysis, category filtering not supported")
            products = scraper.scrape_products(limit=args.limit)
        else:
            print(f"Starting {scraper_name} scraper for {args.category} (limit: {args.limit})")
            if args.scraper == 'sephora':
                print("Note: Sephora scraping uses browser automation and may take longer")
            products = scraper.scrape_products(limit=args.limit, category=args.category)
        
        if products:
            if args.scraper == 'incidecoder':
                output_name = args.output or f'{args.scraper}_{len(products)}_products'
            else:
                output_name = args.output or f'{args.scraper}_{args.category}_{len(products)}_products'
            scraper.save_data(products, output_name)
            print(f"Successfully scraped {len(products)} products")
            print(f"Data saved to: data/{output_name}.csv and data/{output_name}.json")
        else:
            print("No products were scraped")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during scraping: {e}")
        sys.exit(1)
    finally:
        scraper.close()


if __name__ == "__main__":
    main()