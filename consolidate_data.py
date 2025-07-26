#!/usr/bin/env python3
"""
Consolidate all scraped data from working sources into a unified database.
"""

import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Set

def load_json_data(file_path: str) -> List[Dict]:
    """Load JSON data from file."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
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

def filter_products(products: List[Dict]) -> List[Dict]:
    """Filter products to only include moisturizers and cleansers."""
    filtered = []
    for product in products:
        # Skip products without ingredients
        if not product.get('ingredients') or len(product['ingredients']) == 0:
            continue
            
        # Skip search pages and invalid products
        product_name = product.get('product_name', '').lower()
        if any(skip_term in product_name for skip_term in [
            'search', 'login', 'create', '搜尋', '搜索', '検索', 'market'
        ]):
            continue
            
        # For EWG data, we know it's already filtered by category
        if product.get('source') == 'EWG':
            filtered.append(product)
            continue
            
        # For other sources, check product type or name for relevant categories
        product_type = product.get('product_type', '').lower()
        if any(term in product_name for term in [
            'moistur', 'cream', 'lotion', 'balm', 'cleanser', 'cleansing', 
            'wash', 'foam', 'gel', 'oil', 'serum', 'treatment'
        ]) or any(term in product_type for term in [
            'moistur', 'cleanser', 'cleansing'
        ]):
            filtered.append(product)
    
    return filtered

def deduplicate_products(products: List[Dict]) -> List[Dict]:
    """Remove duplicate products based on name and brand."""
    seen = set()
    deduplicated = []
    
    for product in products:
        # Create a key for deduplication
        name = product.get('product_name', '').strip().lower()
        brand = product.get('brand', '').strip().lower()
        key = f"{brand}_{name}"
        
        if key not in seen and name:
            seen.add(key)
            deduplicated.append(product)
    
    return deduplicated

def main():
    """Consolidate all data from working scrapers."""
    data_dir = "data"
    
    # Data files from working scrapers
    data_files = [
        "ewg_moisturizer_12_products.json",
        "ewg_cleanser_12_products.json", 
        "incidecoder_30_products.json"
    ]
    
    all_products = []
    
    # Load data from each source
    for file_name in data_files:
        file_path = os.path.join(data_dir, file_name)
        products = load_json_data(file_path)
        print(f"Loaded {len(products)} products from {file_name}")
        all_products.extend(products)
    
    print(f"Total products before filtering: {len(all_products)}")
    
    # Filter for relevant product types
    filtered_products = filter_products(all_products)
    print(f"Products after filtering: {len(filtered_products)}")
    
    # Deduplicate
    final_products = deduplicate_products(filtered_products)
    print(f"Products after deduplication: {len(final_products)}")
    
    # Add processing metadata
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory
    output_dir = os.path.join(data_dir, "unified")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save unified database
    output_json = os.path.join(output_dir, f"unified_skincare_database_{timestamp}.json")
    output_csv = os.path.join(output_dir, f"unified_skincare_database_{timestamp}.csv")
    
    # Save JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(final_products, f, indent=2, ensure_ascii=False)
    
    # Save CSV
    if final_products:
        fieldnames = ['url', 'source', 'product_name', 'brand', 'price', 'rating', 
                     'ingredients', 'date_published', 'hazard_score', 'product_type']
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in final_products:
                # Ensure all required fields exist
                row = {field: product.get(field, '') for field in fieldnames}
                # Convert ingredients list to string for CSV
                if isinstance(row['ingredients'], list):
                    row['ingredients'] = ', '.join(row['ingredients'])
                writer.writerow(row)
    
    # Create latest symlinks
    latest_json = os.path.join(output_dir, "unified_skincare_database_latest.json")
    latest_csv = os.path.join(output_dir, "unified_skincare_database_latest.csv")
    
    # Remove existing latest files
    for latest_file in [latest_json, latest_csv]:
        if os.path.exists(latest_file):
            os.remove(latest_file)
    
    # Create new latest files
    import shutil
    shutil.copy2(output_json, latest_json)
    shutil.copy2(output_csv, latest_csv)
    
    # Generate summary report
    sources = {}
    ingredient_count = 0
    
    for product in final_products:
        source = product.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
        if product.get('ingredients'):
            ingredient_count += len(product['ingredients'])
    
    print(f"\n=== CONSOLIDATED DATABASE SUMMARY ===")
    print(f"Total products: {len(final_products)}")
    print(f"Total unique ingredients: {ingredient_count}")
    print(f"Sources breakdown:")
    for source, count in sources.items():
        print(f"  - {source}: {count} products")
    
    print(f"\nFiles saved:")
    print(f"  - {output_json}")
    print(f"  - {output_csv}")
    print(f"  - {latest_json}")
    print(f"  - {latest_csv}")

if __name__ == "__main__":
    main()