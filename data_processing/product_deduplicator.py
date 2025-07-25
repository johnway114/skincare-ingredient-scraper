#!/usr/bin/env python3
"""
Product Deduplication System
Identifies and merges duplicate products from different sources
"""

import re
import json
from typing import List, Dict, Tuple, Optional, Set
from pathlib import Path
from difflib import SequenceMatcher
import pandas as pd


class ProductDeduplicator:
    """Identifies and handles duplicate products across different scraped sources"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        
        # Deduplication settings
        self.similarity_threshold = 0.85
        self.brand_weight = 0.3
        self.name_weight = 0.7
        
        # Statistics tracking
        self.dedup_stats = {
            'total_products': 0,
            'duplicates_found': 0,
            'unique_products': 0,
            'merge_operations': 0
        }
    
    def deduplicate_products(self, products: List[Dict]) -> List[Dict]:
        """Main deduplication method - removes duplicates and merges data"""
        if not products:
            return []
        
        self.dedup_stats['total_products'] = len(products)
        
        # Create similarity matrix
        print(f"Analyzing {len(products)} products for duplicates...")
        duplicate_groups = self._find_duplicate_groups(products)
        
        # Merge duplicates
        unique_products = self._merge_duplicate_groups(products, duplicate_groups)
        
        self.dedup_stats['unique_products'] = len(unique_products)
        self.dedup_stats['duplicates_found'] = self.dedup_stats['total_products'] - self.dedup_stats['unique_products']
        
        print(f"Deduplication complete: {self.dedup_stats['duplicates_found']} duplicates removed")
        return unique_products
    
    def _find_duplicate_groups(self, products: List[Dict]) -> List[List[int]]:
        """Find groups of duplicate products"""
        n = len(products)
        visited = [False] * n
        duplicate_groups = []
        
        for i in range(n):
            if visited[i]:
                continue
            
            # Start a new group with product i
            group = [i]
            visited[i] = True
            
            # Find all products similar to product i
            for j in range(i + 1, n):
                if visited[j]:
                    continue
                
                if self._are_products_similar(products[i], products[j]):
                    group.append(j)
                    visited[j] = True
            
            # Only add to duplicate groups if we found actual duplicates
            if len(group) > 1:
                duplicate_groups.append(group)
        
        return duplicate_groups
    
    def _are_products_similar(self, product1: Dict, product2: Dict) -> bool:
        """Determine if two products are the same product from different sources"""
        
        # Get cleaned names and brands
        name1 = self._clean_product_name(product1.get('product_name', ''))
        name2 = self._clean_product_name(product2.get('product_name', ''))
        brand1 = self._clean_brand_name(product1.get('brand', ''))
        brand2 = self._clean_brand_name(product2.get('brand', ''))
        
        # Skip if either name is too short
        if len(name1) < 5 or len(name2) < 5:
            return False
        
        # Calculate brand similarity
        brand_similarity = 1.0 if brand1 == brand2 else self._string_similarity(brand1, brand2)
        
        # Calculate name similarity
        name_similarity = self._string_similarity(name1, name2)
        
        # Combined similarity score
        combined_similarity = (brand_similarity * self.brand_weight + 
                             name_similarity * self.name_weight)
        
        # Additional checks for high confidence matches
        if combined_similarity > self.similarity_threshold:
            return True
        
        # Special case: exact brand match with very similar name
        if brand1 == brand2 and name_similarity > 0.75:
            return True
        
        # Special case: very similar names even with different brands (variant products)
        if name_similarity > 0.9 and brand_similarity > 0.5:
            return True
        
        return False
    
    def _clean_product_name(self, name: str) -> str:
        """Clean product name for comparison"""
        if not name:
            return ""
        
        cleaned = name.lower().strip()
        
        # Remove common variations
        cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)  # Remove parentheses content
        cleaned = re.sub(r'\s*\[[^\]]*\]', '', cleaned)  # Remove brackets content
        cleaned = re.sub(r'\s*-\s*\d+.*', '', cleaned)   # Remove size indicators
        cleaned = re.sub(r'\s*\d+\s*(ml|oz|g|mg).*', '', cleaned)  # Remove volume/weight
        
        # Remove common words that don't help identification
        stop_words = ['face', 'facial', 'skin', 'care', 'skincare', 'beauty', 'cosmetic']
        words = cleaned.split()
        words = [w for w in words if w not in stop_words]
        cleaned = ' '.join(words)
        
        # Remove extra whitespace and punctuation
        cleaned = re.sub(r'[^\w\s]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _clean_brand_name(self, brand: str) -> str:
        """Clean brand name for comparison"""
        if not brand:
            return ""
        
        cleaned = brand.lower().strip()
        
        # Remove common brand suffixes
        suffixes = ['inc', 'llc', 'ltd', 'co', 'corp', 'corporation', 'company']
        for suffix in suffixes:
            pattern = rf'\s+{suffix}\.?$'
            cleaned = re.sub(pattern, '', cleaned)
        
        # Remove special characters except hyphens and apostrophes
        cleaned = re.sub(r"[^\w\s\-']", '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        if not str1 or not str2:
            return 0.0
        
        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _merge_duplicate_groups(self, products: List[Dict], duplicate_groups: List[List[int]]) -> List[Dict]:
        """Merge products in duplicate groups into single entries"""
        unique_products = []
        processed_indices = set()
        
        # Process duplicate groups
        for group in duplicate_groups:
            self.dedup_stats['merge_operations'] += 1
            
            # Merge products in this group
            merged_product = self._merge_products([products[i] for i in group])
            unique_products.append(merged_product)
            
            # Mark these indices as processed
            processed_indices.update(group)
        
        # Add non-duplicate products
        for i, product in enumerate(products):
            if i not in processed_indices:
                unique_products.append(product)
        
        return unique_products
    
    def _merge_products(self, product_group: List[Dict]) -> Dict:
        """Merge multiple products into a single product entry"""
        if len(product_group) == 1:
            return product_group[0]
        
        # Choose the "best" product as the base
        base_product = self._choose_best_product(product_group)
        merged = base_product.copy()
        
        # Collect all sources
        sources = [p.get('source', 'Unknown') for p in product_group]
        merged['sources'] = list(set(sources))
        merged['source'] = ', '.join(merged['sources'])
        
        # Collect all URLs
        urls = [p.get('url', '') for p in product_group if p.get('url')]
        merged['all_urls'] = urls
        
        # Merge ingredients from all sources
        all_ingredients = []
        for product in product_group:
            ingredients = product.get('ingredients', [])
            if isinstance(ingredients, list):
                all_ingredients.extend(ingredients)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ingredients = []
        for ingredient in all_ingredients:
            if ingredient and ingredient.lower() not in seen:
                unique_ingredients.append(ingredient)
                seen.add(ingredient.lower())
        
        merged['ingredients'] = unique_ingredients
        merged['ingredient_count'] = len(unique_ingredients)
        
        # Take the best available data for other fields
        merged = self._merge_field_data(merged, product_group)
        
        # Add metadata about the merge
        merged['is_merged'] = True
        merged['merge_count'] = len(product_group)
        merged['data_sources'] = len(set(sources))
        
        return merged
    
    def _choose_best_product(self, product_group: List[Dict]) -> Dict:
        """Choose the best product to use as the base for merging"""
        
        # Scoring criteria (higher score = better)
        def score_product(product):
            score = 0
            
            # Prefer products with more ingredients
            ingredients = product.get('ingredients', [])
            score += len(ingredients) * 2
            
            # Prefer products with price
            if product.get('price'):
                score += 10
            
            # Prefer products with rating
            if product.get('rating'):
                score += 5
            
            # Prefer products with publication date
            if product.get('date_published'):
                score += 5
            
            # Prefer certain sources (based on data quality)
            source_scores = {
                'INCIDecoder': 20,
                'EWG': 15,
                'CosDNA': 10,
                'Byrdie': 8,
                'Sephora': 5,
                'Amazon': 3
            }
            source = product.get('source', '')
            score += source_scores.get(source, 0)
            
            # Prefer longer product names (more descriptive)
            name = product.get('product_name', '')
            score += min(len(name) / 10, 5)
            
            return score
        
        # Return the product with the highest score
        return max(product_group, key=score_product)
    
    def _merge_field_data(self, merged: Dict, product_group: List[Dict]) -> Dict:
        """Merge data for specific fields from all products"""
        
        # For each field, take the best available value
        fields_to_merge = ['brand', 'price', 'rating', 'date_published', 'hazard_score']
        
        for field in fields_to_merge:
            values = [p.get(field, '') for p in product_group if p.get(field)]
            
            if values:
                if field == 'price':
                    # For price, take the most common value or first valid one
                    merged[field] = self._get_best_price(values)
                elif field == 'rating':
                    # For rating, take the average or most detailed one
                    merged[field] = self._get_best_rating(values)
                elif field == 'brand':
                    # For brand, take the most complete one
                    merged[field] = max(values, key=len)
                else:
                    # For other fields, take the first non-empty value
                    merged[field] = values[0]
        
        return merged
    
    def _get_best_price(self, prices: List[str]) -> str:
        """Select the best price from multiple sources"""
        if not prices:
            return ""
        
        # Clean prices and find the most common pattern
        cleaned_prices = []
        for price in prices:
            # Extract numeric value
            price_match = re.search(r'\$?(\d+\.?\d*)', str(price))
            if price_match:
                cleaned_prices.append(price)
        
        return cleaned_prices[0] if cleaned_prices else prices[0]
    
    def _get_best_rating(self, ratings: List[str]) -> str:
        """Select the best rating from multiple sources"""
        if not ratings:
            return ""
        
        # Prefer numerical ratings
        for rating in ratings:
            if re.search(r'\d+\.?\d*', str(rating)):
                return rating
        
        return ratings[0]
    
    def get_deduplication_report(self) -> Dict:
        """Get report on deduplication process"""
        return {
            'total_products_processed': self.dedup_stats['total_products'],
            'duplicates_found': self.dedup_stats['duplicates_found'],
            'unique_products': self.dedup_stats['unique_products'],
            'merge_operations': self.dedup_stats['merge_operations'],
            'duplicate_rate': (self.dedup_stats['duplicates_found'] / 
                             self.dedup_stats['total_products'] * 100) if self.dedup_stats['total_products'] > 0 else 0
        }


def main():
    """Test the product deduplicator"""
    
    # Create test products with duplicates
    test_products = [
        {
            'product_name': 'CeraVe Daily Facial Moisturizing Lotion',
            'brand': 'CeraVe',
            'price': '$12.99',
            'source': 'EWG',
            'ingredients': ['Water', 'Glycerin', 'Ceramides'],
            'url': 'http://example.com/1'
        },
        {
            'product_name': 'CeraVe Daily Moisturizing Lotion for Face',
            'brand': 'CeraVe',
            'price': '$13.49',
            'source': 'Amazon',
            'ingredients': ['Aqua', 'Glycerin', 'Ceramides', 'Niacinamide'],
            'url': 'http://example.com/2'
        },
        {
            'product_name': 'The Ordinary Hyaluronic Acid 2% + B5',
            'brand': 'The Ordinary',
            'price': '$7.90',
            'source': 'INCIDecoder',
            'ingredients': ['Aqua', 'Sodium Hyaluronate', 'Pentylene Glycol'],
            'url': 'http://example.com/3'
        },
        {
            'product_name': 'Neutrogena Oil-Free Moisture Gel',
            'brand': 'Neutrogena',
            'price': '$8.99',
            'source': 'Sephora',
            'ingredients': ['Water', 'Glycerin', 'Dimethicone'],
            'url': 'http://example.com/4'
        }
    ]
    
    deduplicator = ProductDeduplicator()
    
    print("Testing Product Deduplicator:")
    print("=" * 50)
    print(f"Input: {len(test_products)} products")
    
    # Test deduplication
    unique_products = deduplicator.deduplicate_products(test_products)
    
    print(f"Output: {len(unique_products)} unique products")
    print()
    
    # Show results
    for i, product in enumerate(unique_products, 1):
        print(f"Product {i}:")
        print(f"  Name: {product['product_name']}")
        print(f"  Brand: {product['brand']}")
        print(f"  Sources: {product.get('sources', [product['source']])}")
        print(f"  Ingredients: {len(product['ingredients'])} total")
        if product.get('is_merged'):
            print(f"  *** MERGED from {product['merge_count']} sources ***")
        print()
    
    # Show report
    report = deduplicator.get_deduplication_report()
    print("Deduplication Report:")
    for key, value in report.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()