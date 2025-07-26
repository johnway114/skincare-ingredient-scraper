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
from scrapers.caroline_hirons_scraper import CarolineHironsScraper
from scrapers.into_the_gloss_scraper import IntoTheGlossScraper
from scrapers.paulas_choice_scraper import PaulasChoiceScraper
from scrapers.skinsort_scraper import SkinSortScraper
from scrapers.dermstore_scraper import DermstoreScraper
from scrapers.ulta_scraper import UltaScraper
from scrapers.clearforme_scraper import ClearForMeScraper
from scrapers.cosing_scraper import CosIngScraper
from scrapers.specialchem_scraper import SpecialChemScraper
from scrapers.pcpc_incipedia_scraper import PCPCINCIpediaScraper
from scrapers.skin_signal_scraper import SkinSignalScraper
from scrapers.bluemercury_scraper import BluemercuryScraper
from scrapers.beauty_pie_scraper import BeautyPieScraper
from scrapers.cult_beauty_scraper import CultBeautyScraper
from scrapers.nykaa_scraper import NykaaScraper
from scrapers.la_prairie_scraper import LaPrairieScraper
from scrapers.elemis_scraper import ElemisScraper
from scrapers.ogee_scraper import OgeeScraper


def main():
    parser = argparse.ArgumentParser(description='Skincare ingredient scraper')
    parser.add_argument('scraper', choices=['ewg', 'sephora', 'incidecoder', 'cosdna', 'amazon', 'byrdie', 'caroline_hirons', 'into_the_gloss', 'paulas_choice', 'skinsort', 'dermstore', 'ulta', 'clearforme', 'cosing', 'specialchem', 'pcpc_incipedia', 'skin_signal', 'bluemercury', 'beauty_pie', 'cult_beauty', 'nykaa', 'la_prairie', 'elemis', 'ogee'], help='Which scraper to run')
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
    elif args.scraper == 'caroline_hirons':
        scraper = CarolineHironsScraper(delay=args.delay)
        scraper_name = 'Caroline Hirons'
    elif args.scraper == 'into_the_gloss':
        scraper = IntoTheGlossScraper(delay=args.delay)
        scraper_name = 'Into The Gloss'
    elif args.scraper == 'paulas_choice':
        scraper = PaulasChoiceScraper(delay=max(args.delay, 3.0))
        scraper_name = "Paula's Choice"
    elif args.scraper == 'skinsort':
        scraper = SkinSortScraper(delay=args.delay)
        scraper_name = 'SkinSort'
    elif args.scraper == 'dermstore':
        scraper = DermstoreScraper(delay=max(args.delay, 3.0))
        scraper_name = 'Dermstore'
    elif args.scraper == 'ulta':
        scraper = UltaScraper(delay=max(args.delay, 4.0))
        scraper_name = 'Ulta Beauty'
    elif args.scraper == 'clearforme':
        scraper = ClearForMeScraper(delay=args.delay)
        scraper_name = 'ClearForMe'
    elif args.scraper == 'cosing':
        scraper = CosIngScraper(delay=max(args.delay, 4.0))
        scraper_name = 'CosIng'
    elif args.scraper == 'specialchem':
        scraper = SpecialChemScraper(delay=args.delay)
        scraper_name = 'SpecialChem'
    elif args.scraper == 'pcpc_incipedia':
        scraper = PCPCINCIpediaScraper(delay=args.delay)
        scraper_name = 'PCPC INCIpedia'
    elif args.scraper == 'skin_signal':
        scraper = SkinSignalScraper(delay=args.delay)
        scraper_name = 'Skin Signal'
    elif args.scraper == 'bluemercury':
        scraper = BluemercuryScraper(delay=max(args.delay, 4.0))
        scraper_name = 'Bluemercury'
    elif args.scraper == 'beauty_pie':
        scraper = BeautyPieScraper(delay=max(args.delay, 4.0))
        scraper_name = 'Beauty Pie'
    elif args.scraper == 'cult_beauty':
        scraper = CultBeautyScraper(delay=max(args.delay, 4.0))
        scraper_name = 'Cult Beauty'
    elif args.scraper == 'nykaa':
        scraper = NykaaScraper(delay=max(args.delay, 4.0))
        scraper_name = 'Nykaa'
    elif args.scraper == 'la_prairie':
        scraper = LaPrairieScraper(delay=max(args.delay, 4.0))
        scraper_name = 'La Prairie'
    elif args.scraper == 'elemis':
        scraper = ElemisScraper(delay=max(args.delay, 4.0))
        scraper_name = 'Elemis'
    elif args.scraper == 'ogee':
        scraper = OgeeScraper(delay=max(args.delay, 4.0))
        scraper_name = 'Ogee'
    
    try:
        if args.scraper in ['incidecoder', 'cosing', 'specialchem', 'pcpc_incipedia']:
            print(f"Starting {scraper_name} scraper (limit: {args.limit})")
            if args.scraper == 'incidecoder':
                print("Note: INCIDecoder focuses on ingredient analysis, category filtering not supported")
            elif args.scraper == 'cosing':
                print("Note: CosIng is the EU cosmetic ingredient database")
            elif args.scraper == 'specialchem':
                print("Note: SpecialChem INCI database for cosmetic ingredients")
            elif args.scraper == 'pcpc_incipedia':
                print("Note: PCPC INCIpedia for cosmetic ingredient definitions")
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
            elif args.scraper == 'caroline_hirons':
                print("Note: Caroline Hirons scraper extracts products from beauty blog articles")
            elif args.scraper == 'into_the_gloss':
                print("Note: Into The Gloss scraper extracts products from beauty blog articles")
            elif args.scraper == 'paulas_choice':
                print("Note: Paula's Choice scraper focuses on their Beautypedia and product catalog")
            elif args.scraper == 'skinsort':
                print("Note: SkinSort scraper extracts from their ingredient database")
            elif args.scraper == 'dermstore':
                print("Note: Dermstore scraper may face anti-bot protection - using slower delays")
            elif args.scraper == 'ulta':
                print("Note: Ulta scraper may face anti-bot protection - using slower delays")
            elif args.scraper == 'clearforme':
                print("Note: ClearForMe scraper extracts ingredient safety information")
            elif args.scraper == 'skin_signal':
                print("Note: Skin Signal scraper extracts skincare product reviews and analysis")
            elif args.scraper == 'bluemercury':
                print("Note: Bluemercury scraper focuses on luxury skincare products")
            elif args.scraper == 'beauty_pie':
                print("Note: Beauty Pie scraper extracts membership-based beauty products")
            elif args.scraper == 'cult_beauty':
                print("Note: Cult Beauty scraper focuses on premium beauty products")
            elif args.scraper == 'nykaa':
                print("Note: Nykaa scraper extracts products from Indian beauty marketplace")
            elif args.scraper == 'la_prairie':
                print("Note: La Prairie scraper focuses on luxury Swiss skincare")
            elif args.scraper == 'elemis':
                print("Note: Elemis scraper extracts spa-quality skincare products")
            elif args.scraper == 'ogee':
                print("Note: Ogee scraper focuses on organic and natural skincare products")
            products = scraper.scrape_products(limit=args.limit, category=args.category)
        
        if products:
            if args.scraper in ['incidecoder', 'cosing', 'specialchem', 'pcpc_incipedia']:
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