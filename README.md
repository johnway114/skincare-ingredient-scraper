# Skincare Ingredient Scraper

A Python web scraper for extracting skincare product data and ingredient information from multiple online sources.

## Purpose

Scrapes facial moisturizers and cleansers to create datasets for analyzing ingredient trends, popularity, and effectiveness in skincare products.

## Features

- Multi-source scraping: EWG Skin Deep, Sephora, Amazon, premium brands, ingredient databases
- Data extraction: Product names, brands, prices, ratings, ingredient lists, publication dates
- Ingredient parsing: Filters marketing text, extracts actual ingredient names
- Export formats: CSV and JSON
- Error handling: Logging and graceful failures
- Rate limiting: Configurable delays between requests

## Project Structure

```
ingredient_scraper/
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py      # Base class with common functionality
│   └── ewg_scraper.py       # EWG Skin Deep scraper
├── tests/
│   └── test_ewg.py          # Test suite for EWG scraper
├── data/                    # Output directory for scraped data
├── logs/                    # Scraper logs
├── requirements.txt         # Python dependencies
└── README.md
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
# Scrape 50 moisturizers from EWG
python main.py ewg --limit 50 --category moisturizer

# Scrape cleansers with custom delay and output name
python main.py ewg --limit 25 --category cleanser --delay 3.0 --output my_cleansers

# Scrape from INCIDecoder (ingredient database)
python main.py incidecoder --limit 20

# Scrape from CosDNA (cosmetic analysis database)
python main.py cosdna --limit 15 --category cleanser
```

### Programmatic Usage

```python
from scrapers.ewg_scraper import EWGScraper

scraper = EWGScraper(delay=2.0)

try:
    products = scraper.scrape_products(limit=50, category='moisturizer')
    scraper.save_data(products, 'ewg_moisturizers')
    print(f"Scraped {len(products)} products")
finally:
    scraper.close()
```

### Running Tests

```bash
python tests/test_ewg.py
```

## Data Fields

- `product_name`: Product name
- `brand`: Brand name
- `price`: Product price
- `rating`: Product rating/score
- `ingredients`: List of ingredients
- `url`: Source URL
- `source`: Website name
- `date_published`: Publication date
- `hazard_score`: EWG hazard score (EWG only)

## Implementation Status

**Completed:**
- EWG Skin Deep scraper (fully functional)
- INCIDecoder scraper (fully functional)
- CosDNA scraper (fully functional)
- Sephora scraper (implementation complete, blocked by anti-bot measures)
- Base scraper framework with Selenium support
- CSV/JSON export
- Test suite

**Status:**
- **EWG Skin Deep**: Working reliably, extracting product data and ingredients
- **INCIDecoder**: Excellent performance, 50+ ingredients per product, includes ingredient lookup functionality
- **CosDNA**: Implemented with search functionality and ingredient safety analysis capabilities
- **Sephora**: Implemented but blocked by advanced anti-bot systems. Code structure ready for future access methods.

**Planned:**
- Amazon scraper
- Premium brand scrapers  
- Beauty blog scrapers

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
- Handles dynamic content and anti-scraping measures