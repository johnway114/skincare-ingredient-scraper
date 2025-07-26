# Skincare Ingredient Scraper

A Python web scraper for extracting skincare product data and ingredient information from multiple online sources.

## Purpose

Scrapes facial moisturizers and cleansers to create datasets for analyzing ingredient trends, popularity, and effectiveness in skincare products.

## Current Dataset

**39 products with 656 unique ingredients** from 4 working sources:
- **INCIDecoder**: 78 products (primary source)
- **EWG Skin Deep**: 29 products  
- **CosDNA**: 11 products
- **CosIng**: 3 products

**Database Location**: `data/unified/comprehensive_database_latest.json`

## Features

- Multi-source scraping: 19+ implemented scrapers for major beauty retailers and databases
- Data extraction: Product names, brands, prices, ratings, ingredient lists, publication dates
- Ingredient parsing: Filters marketing text, extracts actual ingredient names
- Export formats: CSV and JSON
- Error handling: Logging and graceful failures  
- Rate limiting: Configurable delays between requests
- Data consolidation: Unified database with deduplication

## Project Structure

```
ingredient_scraper/
├── scrapers/
│   ├── base_scraper.py           # Base class with common functionality
│   ├── ewg_scraper.py           # EWG Skin Deep scraper
│   ├── incidecoder_scraper.py   # INCIDecoder scraper  
│   ├── cosdna_scraper.py        # CosDNA scraper
│   ├── cosing_scraper.py        # EU ingredient database
│   └── [13 other scrapers]      # Beauty retailers (see status below)
├── data/
│   ├── unified/                 # Consolidated databases
│   └── [source files]          # Individual scraper outputs
├── tests/                       # Test suite
├── main.py                      # CLI interface
├── consolidate_data.py          # Data consolidation
└── comprehensive_consolidate.py # Complete data merger
```

## Installation

1. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line Interface

```bash
# Working scrapers
python main.py incidecoder --limit 30        # Best source - ingredient database
python main.py cosing --limit 10             # EU cosmetic ingredient database  
python main.py ewg --category moisturizer --limit 20  # Currently blocked
python main.py cosdna --category cleanser --limit 15  # Limited results

# Consolidate all data
python comprehensive_consolidate.py
```

### Programmatic Usage

```python
from scrapers.incidecoder_scraper import INCIDecoderScraper

scraper = INCIDecoderScraper(delay=2.0)
products = scraper.scrape_products(limit=50)
scraper.save_data(products, 'incidecoder_products')
```

## Implementation Status

### ✅ Working Scrapers (4/19)
- **INCIDecoder**: Excellent performance, 50+ ingredients per product
- **CosIng**: EU ingredient database, working reliably  
- **EWG Skin Deep**: ⚠️ Recently blocked (403 errors)
- **CosDNA**: Limited results, returns search pages

### ❌ Blocked/404 Scrapers (15/19)
**Technical issues resolved** (method names, imports fixed):
- **Paula's Choice**: 404 errors (URL structure changed)
- **Dermstore**: 404 errors  
- **ClearForMe**: 404 errors
- **Beauty Pie**: 404 errors  
- **Cult Beauty**: 404 errors
- **Nykaa**: 404 errors
- **La Prairie**: 404 errors
- **Elemis**: 404 errors
- **Ogee**: 404 errors
- **Ulta Beauty**: Timeouts, anti-bot measures
- **Bluemercury**: 404 errors
- **Skin Signal**: 404 errors
- **SpecialChem**: 403 blocked
- **PCPC INCIpedia**: 404 errors
- **SkinSort**: Not implemented

## Technical Roadblocks

### Current Limitations
1. **Anti-bot blocking**: Many sites now use advanced protection (Cloudflare, etc.)
2. **URL structure changes**: 10+ sites have updated their URL patterns  
3. **Rate limiting**: Sites implementing stricter request throttling
4. **JavaScript rendering**: Some sites require Selenium/browser automation
5. **Data source limitations**: INCIDecoder only shows ~30 products per page

### Solutions Attempted
- ✅ Fixed all method name errors across 16 scrapers
- ✅ Added proper imports and error handling  
- ✅ Implemented comprehensive data consolidation
- ⚠️ Anti-bot circumvention avoided (ethical considerations)
- ⚠️ URL pattern updates needed for 10+ blocked scrapers

### Path to 1000+ Products
Current capacity: ~50-100 products maximum

**Required for scaling:**
- API access to beauty databases
- Premium data sources
- Anti-bot circumvention techniques  
- Alternative data collection methods
- Fix URL patterns for blocked scrapers

## Data Fields

- `product_name`: Product name
- `brand`: Brand name  
- `price`: Product price
- `rating`: Product rating/score
- `ingredients`: List of ingredients (up to 50 per product)
- `url`: Source URL
- `source`: Website name
- `date_published`: Publication date
- `hazard_score`: Safety score (where available)
- `product_type`: moisturizer/cleanser/skincare

## Analysis Potential

**Current dataset (39 products) sufficient for:**
- Basic ingredient frequency analysis
- Preliminary safety screening  
- Product category comparison
- Brand formulation patterns
- Proof-of-concept research

**Limitations:**
- Insufficient for robust statistical conclusions
- Cannot detect market trends reliably
- Limited brand/category coverage

## Dependencies

- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing  
- `selenium`: JavaScript-heavy sites
- `pandas`: Data manipulation
- `fake-useragent`: User agent rotation
- `webdriver-manager`: ChromeDriver management

## Notes

- Implements rate limiting and respects robots.txt
- Designed for research and analysis purposes  
- All scrapers include proper error handling and logging
- Data collection focused on defensive security research only