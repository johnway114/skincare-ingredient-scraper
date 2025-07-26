#!/usr/bin/env python3
"""
Comprehensive consolidation of ALL available scraped data.
"""

import json
import csv
import os
import glob
from datetime import datetime
from typing import List, Dict, Set

def load_json_data(file_path: str) -> List[Dict]:
    """Load JSON data from file."""
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return [data] if data else []
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def main():
    """Consolidate all data from all sources."""
    
    # Find all JSON data files
    data_files = glob.glob("data/*.json")
    data_files = [f for f in data_files if not f.endswith('_mappings.json')]
    
    all_products = []
    source_stats = {}
    
    for file_path in data_files:
        products = load_json_data(file_path)
        if products:
            print(f"Loaded {len(products)} products from {os.path.basename(file_path)}")
            all_products.extend(products)
            
            # Track source statistics
            for product in products:
                source = product.get('source', 'Unknown')
                source_stats[source] = source_stats.get(source, 0) + 1
    
    print(f"\nTotal products loaded: {len(all_products)}")
    
    # Filter for skincare products only
    skincare_products = []
    for product in all_products:
        product_type = product.get('product_type', '').lower()
        product_name = product.get('product_name', '').lower()
        
        # Include if it's explicitly skincare or has skincare terms
        if (product_type in ['moisturizer', 'cleanser', 'skincare'] or
            any(term in product_name for term in ['moistur', 'cream', 'lotion', 'clean', 'wash', 'serum', 'oil'])):
            skincare_products.append(product)
    
    print(f"Skincare products after filtering: {len(skincare_products)}")
    
    # Deduplicate by URL
    seen_urls = set()
    unique_products = []
    for product in skincare_products:
        url = product.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_products.append(product)
        elif not url:  # Include products without URLs
            unique_products.append(product)
    
    print(f"Unique products after deduplication: {len(unique_products)}")
    
    # Collect all unique ingredients
    all_ingredients = set()
    for product in unique_products:
        ingredients = product.get('ingredients', [])
        if isinstance(ingredients, list):
            for ingredient in ingredients:
                if ingredient and len(str(ingredient).strip()) > 2:
                    all_ingredients.add(str(ingredient).strip())
    
    # Generate final statistics
    print(f"\n=== COMPREHENSIVE DATABASE SUMMARY ===")
    print(f"Total products: {len(unique_products)}")
    print(f"Total unique ingredients: {len(all_ingredients)}")
    print(f"Sources breakdown:")
    for source, count in source_stats.items():
        print(f"  - {source}: {count} products")
    
    # Save consolidated data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ensure unified directory exists
    os.makedirs("data/unified", exist_ok=True)
    
    # Save timestamped files
    json_file = f"data/unified/comprehensive_database_{timestamp}.json"
    csv_file = f"data/unified/comprehensive_database_{timestamp}.csv"
    
    # Save latest files
    latest_json = "data/unified/comprehensive_database_latest.json"
    latest_csv = "data/unified/comprehensive_database_latest.csv"
    
    # Save JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(unique_products, f, indent=2, ensure_ascii=False)
    
    with open(latest_json, 'w', encoding='utf-8') as f:
        json.dump(unique_products, f, indent=2, ensure_ascii=False)
    
    # Save CSV
    if unique_products:
        fieldnames = ['product_name', 'brand', 'source', 'url', 'price', 'rating', 
                     'product_type', 'hazard_score', 'date_published', 'ingredients']
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for product in unique_products:
                # Convert ingredients list to string for CSV
                product_copy = product.copy()
                ingredients = product_copy.get('ingredients', [])
                if isinstance(ingredients, list):
                    product_copy['ingredients'] = '; '.join(str(ing) for ing in ingredients if ing)
                writer.writerow(product_copy)
        
        with open(latest_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for product in unique_products:
                product_copy = product.copy()
                ingredients = product_copy.get('ingredients', [])
                if isinstance(ingredients, list):
                    product_copy['ingredients'] = '; '.join(str(ing) for ing in ingredients if ing)
                writer.writerow(product_copy)
    
    print(f"\nFiles saved:")
    print(f"  - {json_file}")
    print(f"  - {csv_file}")
    print(f"  - {latest_json}")
    print(f"  - {latest_csv}")

if __name__ == "__main__":
    main()