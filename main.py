#!/usr/bin/env python3
"""
Main script for running skincare ingredient scrapers
"""

import argparse
import sys
from scrapers.ewg_scraper import EWGScraper
from scrapers.sephora_scraper import SephoraScraper
from scrapers.incidecoder_scraper import INCIDecoderScraper
from scrapers.cosdna_scraper import CosDNAScraper
from scrapers.amazon_scraper import AmazonScraper
from scrapers.byrdie_scraper import ByrdieScraper


def main():
    parser = argparse.ArgumentParser(description='Skincare ingredient scraper')
    parser.add_argument('scraper', choices=['ewg', 'sephora', 'incidecoder', 'cosdna', 'amazon', 'byrdie'], help='Which scraper to run')
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
    elif args.scraper == 'cosdna':
        scraper = CosDNAScraper(delay=max(args.delay, 3.0))  # Minimum 3s delay for CosDNA
        scraper_name = 'CosDNA'
    elif args.scraper == 'amazon':
        scraper = AmazonScraper(delay=max(args.delay, 5.0))  # Minimum 5s delay for Amazon
        scraper_name = 'Amazon'
    elif args.scraper == 'byrdie':
        scraper = ByrdieScraper(delay=args.delay)
        scraper_name = 'Byrdie'
    
    try:
        if args.scraper == 'incidecoder':
            print(f"Starting {scraper_name} scraper (limit: {args.limit})")
            print("Note: INCIDecoder focuses on ingredient analysis, category filtering not supported")
            products = scraper.scrape_products(limit=args.limit)
        elif args.scraper == 'cosdna':
            print(f"Starting {scraper_name} scraper (limit: {args.limit})")
            print("Note: CosDNA uses search queries, will search for facial products")
            query = f"facial {args.category}" if args.category else "facial moisturizer"
            products = scraper.scrape_products(limit=args.limit, query=query)
        else:
            print(f"Starting {scraper_name} scraper for {args.category} (limit: {args.limit})")
            if args.scraper == 'sephora':
                print("Note: Sephora scraping uses browser automation and may take longer")
            elif args.scraper == 'amazon':
                print("Note: Amazon scraping uses browser automation and very slow delays due to anti-bot measures")
                print("Warning: Amazon may block requests - use small limits and expect some failures")
            elif args.scraper == 'byrdie':
                print("Note: Byrdie scraper extracts products from beauty articles and reviews")
            products = scraper.scrape_products(limit=args.limit, category=args.category)
        
        if products:
            if args.scraper == 'incidecoder':
                output_name = args.output or f'{args.scraper}_{len(products)}_products'
            elif args.scraper == 'cosdna':
                query_safe = query.replace(' ', '_') if args.scraper == 'cosdna' else args.category
                output_name = args.output or f'{args.scraper}_{query_safe}_{len(products)}_products'
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