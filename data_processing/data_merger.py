#!/usr/bin/env python3
"""
Data Merger - Creates unified database from all scraped sources
Combines data from EWG, INCIDecoder, CosDNA and other working scrapers
"""

import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import glob
from datetime import datetime

from ingredient_standardizer import IngredientStandardizer
from product_deduplicator import ProductDeduplicator


class DataMerger:
    """Merges all scraped data into a unified database"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.output_dir = self.data_dir / "unified"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize processing components
        self.ingredient_standardizer = IngredientStandardizer()
        self.product_deduplicator = ProductDeduplicator()
        
        # Statistics tracking
        self.merge_stats = {
            'files_processed': 0,
            'total_products': 0,
            'products_by_source': {},
            'unique_products': 0,
            'total_ingredients': 0,
            'unique_ingredients': 0,
            'processing_time': None
        }
    
    def create_unified_database(self) -> str:
        """Main method to create unified database from all scraped data"""
        start_time = datetime.now()
        print("Creating unified database from all scraped data...")
        print("=" * 60)
        
        # Step 1: Load all data files
        all_products = self._load_all_data_files()
        if not all_products:
            print("No data files found to process!")
            return ""
        
        print(f"Loaded {len(all_products)} total products from {self.merge_stats['files_processed']} files")
        
        # Step 2: Standardize ingredients
        print("\nStandardizing ingredients...")
        all_products = self._standardize_all_ingredients(all_products)
        
        # Step 3: Deduplicate products
        print("\nDeduplicating products...")
        unique_products = self.product_deduplicator.deduplicate_products(all_products)
        self.merge_stats['unique_products'] = len(unique_products)
        
        # Step 4: Add derived fields
        print("\nAdding derived fields...")
        unique_products = self._add_derived_fields(unique_products)
        
        # Step 5: Generate statistics
        self._calculate_final_statistics(unique_products)
        
        # Step 6: Save unified database
        output_file = self._save_unified_database(unique_products)
        
        # Step 7: Save processing report
        self.merge_stats['processing_time'] = str(datetime.now() - start_time)
        self._save_processing_report()
        
        print(f"\n✅ Unified database created: {output_file}")
        self._print_final_summary()
        
        return output_file
    
    def _load_all_data_files(self) -> List[Dict]:
        """Load all JSON data files from the data directory"""
        all_products = []
        
        # Look for JSON files from our scrapers
        json_patterns = [
            "ewg_*.json",
            "incidecoder_*.json", 
            "cosdna_*.json",
            "sephora_*.json",  # Include even if blocked
            "amazon_*.json",   # Include even if blocked
            "byrdie_*.json"    # Include even if blocked
        ]
        
        for pattern in json_patterns:
            files = glob.glob(str(self.data_dir / pattern))
            
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        # Track products by source
                        source = self._identify_source_from_filename(file_path)
                        for product in data:
                            product['file_source'] = source
                        
                        all_products.extend(data)
                        self.merge_stats['files_processed'] += 1
                        
                        # Update source statistics
                        if source not in self.merge_stats['products_by_source']:
                            self.merge_stats['products_by_source'][source] = 0
                        self.merge_stats['products_by_source'][source] += len(data)
                        
                        print(f"  Loaded {len(data)} products from {Path(file_path).name}")
                    
                except Exception as e:
                    print(f"  ⚠️  Error loading {file_path}: {e}")
        
        self.merge_stats['total_products'] = len(all_products)
        return all_products
    
    def _identify_source_from_filename(self, file_path: str) -> str:
        """Identify the source scraper from filename"""
        filename = Path(file_path).name.lower()
        
        if 'ewg' in filename:
            return 'EWG'
        elif 'incidecoder' in filename:
            return 'INCIDecoder'
        elif 'cosdna' in filename:
            return 'CosDNA'
        elif 'sephora' in filename:
            return 'Sephora'
        elif 'amazon' in filename:
            return 'Amazon'
        elif 'byrdie' in filename:
            return 'Byrdie'
        else:
            return 'Unknown'
    
    def _standardize_all_ingredients(self, products: List[Dict]) -> List[Dict]:
        """Standardize ingredients for all products"""
        for product in products:
            ingredients = product.get('ingredients', [])
            if ingredients:
                # Standardize the ingredient list
                standardized_ingredients = self.ingredient_standardizer.standardize_ingredient_list(ingredients)
                product['ingredients'] = standardized_ingredients
                product['ingredient_count'] = len(standardized_ingredients)
        
        # Save the updated ingredient mappings
        self.ingredient_standardizer.save_mappings()
        
        # Print standardization report
        report = self.ingredient_standardizer.get_standardization_report()
        print(f"  Processed {report['total_ingredients_processed']} ingredients")
        print(f"  Standardization rate: {report['standardization_rate']:.1f}%")
        print(f"  New mappings created: {report['new_mappings_created']}")
        
        return products
    
    def _add_derived_fields(self, products: List[Dict]) -> List[Dict]:
        """Add derived fields for better analysis"""
        
        for product in products:
            # Add ingredient statistics
            ingredients = product.get('ingredients', [])
            product['ingredient_count'] = len(ingredients)
            
            # Categorize product type based on name
            product['product_type'] = self._categorize_product_type(product.get('product_name', ''))
            
            # Add data quality score
            product['data_quality_score'] = self._calculate_data_quality_score(product)
            
            # Add price category if price exists
            if product.get('price'):
                product['price_category'] = self._categorize_price(product['price'])
            
            # Add boolean flags for key ingredients
            product['contains_retinol'] = self._contains_ingredient(ingredients, ['retinol', 'vitamin a'])
            product['contains_hyaluronic_acid'] = self._contains_ingredient(ingredients, ['hyaluronic acid'])
            product['contains_vitamin_c'] = self._contains_ingredient(ingredients, ['vitamin c', 'ascorbic acid'])
            product['contains_niacinamide'] = self._contains_ingredient(ingredients, ['niacinamide'])
            product['contains_aha_bha'] = self._contains_ingredient(ingredients, ['glycolic acid', 'salicylic acid', 'lactic acid'])
            
            # Add processing timestamp
            product['processed_date'] = datetime.now().isoformat()
        
        return products
    
    def _categorize_product_type(self, product_name: str) -> str:
        """Categorize product type based on name"""
        name_lower = product_name.lower()
        
        if any(word in name_lower for word in ['cleanser', 'cleansing', 'wash', 'foam', 'gel cleanser']):
            return 'Cleanser'
        elif any(word in name_lower for word in ['moisturizer', 'cream', 'lotion', 'hydrating']):
            return 'Moisturizer'
        elif any(word in name_lower for word in ['serum', 'essence', 'treatment']):
            return 'Serum/Treatment'
        elif any(word in name_lower for word in ['sunscreen', 'spf', 'sun protection']):
            return 'Sunscreen'
        elif any(word in name_lower for word in ['oil', 'facial oil']):
            return 'Oil'
        elif any(word in name_lower for word in ['mask', 'masque']):
            return 'Mask'
        elif any(word in name_lower for word in ['toner', 'tonic', 'astringent']):
            return 'Toner'
        else:
            return 'Other'
    
    def _calculate_data_quality_score(self, product: Dict) -> float:
        """Calculate a data quality score for the product (0-100)"""
        score = 0
        
        # Basic information (40 points total)
        if product.get('product_name'):
            score += 15
        if product.get('brand'):
            score += 10
        if product.get('price'):
            score += 10
        if product.get('url'):
            score += 5
        
        # Ingredient information (40 points total)
        ingredients = product.get('ingredients', [])
        if ingredients:
            score += 20  # Has ingredients
            if len(ingredients) >= 5:
                score += 10  # Good ingredient count
            if len(ingredients) >= 15:
                score += 10  # Excellent ingredient count
        
        # Additional data (20 points total)
        if product.get('rating'):
            score += 5
        if product.get('date_published'):
            score += 5
        if product.get('hazard_score'):
            score += 5
        if product.get('is_merged'):
            score += 5  # Merged products have more comprehensive data
        
        return min(score, 100)  # Cap at 100
    
    def _categorize_price(self, price_str: str) -> str:
        """Categorize price into ranges"""
        import re
        
        # Extract numeric price
        price_match = re.search(r'\$?(\d+\.?\d*)', str(price_str))
        if not price_match:
            return 'Unknown'
        
        price = float(price_match.group(1))
        
        if price < 10:
            return 'Budget (<$10)'
        elif price < 25:
            return 'Affordable ($10-25)'
        elif price < 50:
            return 'Mid-Range ($25-50)'
        elif price < 100:
            return 'Premium ($50-100)'
        else:
            return 'Luxury ($100+)'
    
    def _contains_ingredient(self, ingredients: List[str], target_ingredients: List[str]) -> bool:
        """Check if ingredients list contains any of the target ingredients"""
        ingredients_lower = [ing.lower() for ing in ingredients]
        return any(target.lower() in ' '.join(ingredients_lower) for target in target_ingredients)
    
    def _calculate_final_statistics(self, products: List[Dict]):
        """Calculate final statistics for the unified database"""
        
        # Count unique ingredients
        all_ingredients = set()
        total_ingredient_count = 0
        
        for product in products:
            ingredients = product.get('ingredients', [])
            total_ingredient_count += len(ingredients)
            all_ingredients.update(ing.lower() for ing in ingredients)
        
        self.merge_stats['total_ingredients'] = total_ingredient_count
        self.merge_stats['unique_ingredients'] = len(all_ingredients)
    
    def _save_unified_database(self, products: List[Dict]) -> str:
        """Save the unified database in multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_file = self.output_dir / f"unified_skincare_database_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        # Save as CSV
        csv_file = self.output_dir / f"unified_skincare_database_{timestamp}.csv"
        df = pd.DataFrame(products)
        
        # Handle ingredients list for CSV (convert to string)
        if 'ingredients' in df.columns:
            df['ingredients_list'] = df['ingredients'].apply(lambda x: '; '.join(x) if isinstance(x, list) else str(x))
            df['all_urls'] = df['all_urls'].apply(lambda x: '; '.join(x) if isinstance(x, list) and x else '')
        
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # Save latest version (without timestamp)
        latest_json = self.output_dir / "unified_skincare_database_latest.json" 
        latest_csv = self.output_dir / "unified_skincare_database_latest.csv"
        
        with open(latest_json, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        df.to_csv(latest_csv, index=False, encoding='utf-8')
        
        return str(latest_json)
    
    def _save_processing_report(self):
        """Save processing report"""
        report_file = self.output_dir / "processing_report.json"
        
        # Add additional reports
        report = {
            'merge_statistics': self.merge_stats,
            'deduplication_report': self.product_deduplicator.get_deduplication_report(),
            'standardization_report': self.ingredient_standardizer.get_standardization_report(),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📊 Processing report saved: {report_file}")
    
    def _print_final_summary(self):
        """Print final summary of the unified database"""
        print("\n" + "=" * 60)
        print("📊 UNIFIED DATABASE SUMMARY")
        print("=" * 60)
        
        print(f"🔢 Total Products: {self.merge_stats['total_products']}")
        print(f"✨ Unique Products: {self.merge_stats['unique_products']}")
        print(f"🧪 Total Ingredients: {self.merge_stats['total_ingredients']}")
        print(f"📝 Unique Ingredients: {self.merge_stats['unique_ingredients']}")
        
        print(f"\n📂 Products by Source:")
        for source, count in self.merge_stats['products_by_source'].items():
            print(f"   {source}: {count} products")
        
        print(f"\n⏱️  Processing Time: {self.merge_stats['processing_time']}")
        
        print(f"\n📁 Files Created:")
        print(f"   • unified_skincare_database_latest.json")
        print(f"   • unified_skincare_database_latest.csv") 
        print(f"   • processing_report.json")
        
        print("\n✅ Your unified database is ready to explore!")


def main():
    """Create unified database from all scraped data"""
    merger = DataMerger()
    output_file = merger.create_unified_database()
    
    if output_file:
        print(f"\n🎉 Success! Unified database created at:")
        print(f"   {output_file}")
        print("\nYou can now view your complete skincare ingredient database!")
    else:
        print("\n❌ No data found to process. Run some scrapers first!")


if __name__ == "__main__":
    main()