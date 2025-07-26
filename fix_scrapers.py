#!/usr/bin/env python3
"""
Quick script to fix method names in all scrapers
"""

import os
import re

scrapers_to_fix = [
    'beauty_pie_scraper.py',
    'cult_beauty_scraper.py', 
    'nykaa_scraper.py',
    'la_prairie_scraper.py',
    'elemis_scraper.py',
    'ogee_scraper.py'
]

def fix_scraper_file(filepath):
    """Fix method names and imports in a scraper file"""
    print(f"Fixing {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add urljoin import if missing
    if 'from urllib.parse import urljoin' not in content:
        content = content.replace(
            'from .base_scraper import BaseScraper',
            'from urllib.parse import urljoin\nfrom .base_scraper import BaseScraper'
        )
    
    # Fix _get_with_retry calls
    content = re.sub(
        r'response = self\._get_with_retry\(([^)]+)\)\s*\n\s*if response and response\.status_code == 200:\s*\n\s*soup = BeautifulSoup\(response\.text, [^)]+\)',
        r'soup = self.get_page(\1)\n            if soup:',
        content
    )
    
    # Fix _get_with_retry error handling
    content = re.sub(
        r'response = self\._get_with_retry\(([^)]+)\)\s*\n\s*if not response or response\.status_code != 200:\s*\n\s*self\.logger\.error\(f"Failed to fetch \{[^}]+\}: \{response\.status_code if response else \'No response\'\}"\)\s*\n\s*return None\s*\n\s*soup = BeautifulSoup\(response\.text, [^)]+\)',
        r'soup = self.get_page(\1)\n            if not soup:\n                self.logger.error(f"Failed to fetch {\1}")\n                return None',
        content
    )
    
    # Fix _make_absolute_url calls
    content = content.replace('self._make_absolute_url(', 'urljoin(self.base_url, ')
    
    # Fix remaining response references
    content = re.sub(
        r'if response and response\.status_code == 200:',
        'if soup:',
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

def main():
    scrapers_dir = '/Users/johnconway/Desktop/ingredient_scraper/scrapers'
    
    for scraper_file in scrapers_to_fix:
        filepath = os.path.join(scrapers_dir, scraper_file)
        if os.path.exists(filepath):
            fix_scraper_file(filepath)
        else:
            print(f"File not found: {filepath}")

if __name__ == "__main__":
    main()