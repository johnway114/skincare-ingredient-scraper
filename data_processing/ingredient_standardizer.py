#!/usr/bin/env python3
"""
Ingredient Standardization System
Normalizes ingredient names across different scraped sources
"""

import re
import json
from typing import List, Dict, Set, Optional
from pathlib import Path


class IngredientStandardizer:
    """Standardizes ingredient names and creates unified ingredient database"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        
        # Load or create ingredient mappings
        self.ingredient_mappings = self._load_ingredient_mappings()
        self.inci_names = self._load_inci_database()
        self.common_variations = self._load_common_variations()
        
        # Statistics tracking
        self.standardization_stats = {
            'total_processed': 0,
            'standardized': 0,
            'unmapped': set(),
            'new_mappings': 0
        }
    
    def _load_ingredient_mappings(self) -> Dict[str, str]:
        """Load existing ingredient name mappings"""
        mapping_file = self.data_dir / "ingredient_mappings.json"
        
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                return json.load(f)
        
        # Default mappings for common variations
        return {
            # Hyaluronic Acid variations
            "hyaluronic acid": "Hyaluronic Acid",
            "sodium hyaluronate": "Hyaluronic Acid",
            "ha": "Hyaluronic Acid",
            
            # Vitamin C variations  
            "vitamin c": "Vitamin C",
            "ascorbic acid": "Vitamin C",
            "l-ascorbic acid": "Vitamin C",
            "magnesium ascorbyl phosphate": "Vitamin C",
            "sodium ascorbyl phosphate": "Vitamin C",
            
            # Retinol variations
            "retinol": "Retinol",
            "vitamin a": "Retinol", 
            "retinyl palmitate": "Retinol",
            "retinyl acetate": "Retinol",
            
            # Niacinamide variations
            "niacinamide": "Niacinamide",
            "nicotinamide": "Niacinamide",
            "vitamin b3": "Niacinamide",
            
            # Common moisturizers
            "glycerin": "Glycerin",
            "glycerol": "Glycerin",
            "glycerine": "Glycerin",
            
            # Water variations
            "water": "Water",
            "aqua": "Water",
            "eau": "Water",
            
            # Common oils
            "jojoba oil": "Jojoba Oil",
            "simmondsia chinensis seed oil": "Jojoba Oil",
            "argan oil": "Argan Oil",
            "argania spinosa kernel oil": "Argan Oil",
            "rosehip oil": "Rosehip Oil",
            "rosa canina fruit oil": "Rosehip Oil",
            
            # Acids
            "salicylic acid": "Salicylic Acid",
            "bha": "Salicylic Acid",
            "glycolic acid": "Glycolic Acid",
            "lactic acid": "Lactic Acid",
            "aha": "Alpha Hydroxy Acid",
            
            # Peptides
            "peptides": "Peptides",
            "copper peptides": "Copper Peptides",
            "matrixyl": "Peptides",
            
            # Ceramides
            "ceramides": "Ceramides",
            "ceramide np": "Ceramides",
            "ceramide ap": "Ceramides",
            "ceramide eop": "Ceramides"
        }
    
    def _load_inci_database(self) -> Dict[str, str]:
        """Load INCI (International Nomenclature of Cosmetic Ingredients) database"""
        # This would ideally load from a comprehensive INCI database
        # For now, return basic INCI mappings
        return {
            "Water": "Aqua",
            "Glycerin": "Glycerin", 
            "Hyaluronic Acid": "Sodium Hyaluronate",
            "Vitamin C": "Ascorbic Acid",
            "Retinol": "Retinol",
            "Niacinamide": "Niacinamide",
            "Salicylic Acid": "Salicylic Acid",
            "Glycolic Acid": "Glycolic Acid",
            "Lactic Acid": "Lactic Acid"
        }
    
    def _load_common_variations(self) -> Dict[str, List[str]]:
        """Load common spelling variations and synonyms"""
        return {
            "hyaluronic": ["hyaluronic", "hylauronic", "hialuronic"],
            "niacinamide": ["niacinamide", "nicotinamide", "niacin"],
            "ceramide": ["ceramide", "cerimide", "ceramides"],
            "retinol": ["retinol", "retin-ol", "vitamin a"],
            "glycerin": ["glycerin", "glycerine", "glycerol"],
            "dimethicone": ["dimethicone", "dimethicon", "cyclomethicone"]
        }
    
    def standardize_ingredient(self, ingredient: str) -> str:
        """Standardize a single ingredient name"""
        if not ingredient or not isinstance(ingredient, str):
            return ""
        
        self.standardization_stats['total_processed'] += 1
        
        # Clean the ingredient name
        cleaned = self._clean_ingredient_name(ingredient)
        
        # Try direct mapping first
        if cleaned.lower() in self.ingredient_mappings:
            self.standardization_stats['standardized'] += 1
            return self.ingredient_mappings[cleaned.lower()]
        
        # Try fuzzy matching
        standardized = self._fuzzy_match_ingredient(cleaned)
        if standardized:
            # Add new mapping for future use
            self.ingredient_mappings[cleaned.lower()] = standardized
            self.standardization_stats['new_mappings'] += 1
            self.standardization_stats['standardized'] += 1
            return standardized
        
        # If no match found, return cleaned version and track it
        self.standardization_stats['unmapped'].add(cleaned)
        return cleaned
    
    def _clean_ingredient_name(self, ingredient: str) -> str:
        """Clean ingredient name by removing unwanted characters and formatting"""
        # Remove common prefixes/suffixes
        cleaned = ingredient.strip()
        
        # Remove concentration indicators
        cleaned = re.sub(r'\s*\(\d+\.?\d*%?\)', '', cleaned)
        cleaned = re.sub(r'\s*\[\d+\.?\d*%?\]', '', cleaned)
        cleaned = re.sub(r'\s*\d+\.?\d*%\s*', '', cleaned)
        
        # Remove brand names in parentheses
        cleaned = re.sub(r'\s*\([^)]*®[^)]*\)', '', cleaned)
        cleaned = re.sub(r'\s*\([^)]*™[^)]*\)', '', cleaned)
        
        # Remove common prefixes
        prefixes_to_remove = [
            'organic ', 'natural ', 'pure ', 'premium ', 'pharmaceutical grade ',
            'cosmetic grade ', 'food grade ', 'usp grade ', 'refined '
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):]
        
        # Remove common suffixes
        suffixes_to_remove = [
            ' extract', ' oil', ' butter', ' wax', ' powder', ' crystals',
            ' (and)', ' &', ' +', ' complex'
        ]
        
        for suffix in suffixes_to_remove:
            if cleaned.lower().endswith(suffix):
                cleaned = cleaned[:-len(suffix)]
        
        # Clean up formatting
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single
        cleaned = re.sub(r'[^\w\s\-().,]', '', cleaned)  # Remove special chars except basic ones
        cleaned = cleaned.strip()
        
        # Capitalize properly
        return self._proper_capitalize(cleaned)
    
    def _proper_capitalize(self, text: str) -> str:
        """Apply proper capitalization to ingredient names"""
        # Handle special cases
        special_cases = {
            'ph': 'pH',
            'spf': 'SPF',
            'uv': 'UV',
            'dna': 'DNA',
            'rna': 'RNA',
            'aha': 'AHA',
            'bha': 'BHA',
            'peg': 'PEG',
            'ppg': 'PPG'
        }
        
        words = text.split()
        capitalized_words = []
        
        for word in words:
            word_lower = word.lower()
            if word_lower in special_cases:
                capitalized_words.append(special_cases[word_lower])
            elif len(word) <= 3 and word_lower not in ['and', 'or', 'of', 'in', 'on', 'at', 'to']:
                capitalized_words.append(word.upper())
            else:
                capitalized_words.append(word.capitalize())
        
        return ' '.join(capitalized_words)
    
    def _fuzzy_match_ingredient(self, ingredient: str) -> Optional[str]:
        """Attempt fuzzy matching against known ingredients"""
        ingredient_lower = ingredient.lower()
        
        # Check for partial matches in existing mappings
        for mapped_ingredient, standard_name in self.ingredient_mappings.items():
            if self._is_similar_ingredient(ingredient_lower, mapped_ingredient):
                return standard_name
        
        # Check against common variations
        for base_ingredient, variations in self.common_variations.items():
            for variation in variations:
                if variation in ingredient_lower or ingredient_lower in variation:
                    # Find the standard name for this base ingredient
                    if base_ingredient in self.ingredient_mappings:
                        return self.ingredient_mappings[base_ingredient]
        
        return None
    
    def _is_similar_ingredient(self, ingredient1: str, ingredient2: str) -> bool:
        """Check if two ingredient names are similar enough to be considered the same"""
        # Simple similarity check - can be enhanced with proper fuzzy matching
        
        # Exact match
        if ingredient1 == ingredient2:
            return True
        
        # One contains the other
        if ingredient1 in ingredient2 or ingredient2 in ingredient1:
            return True
        
        # Similar length and many common characters
        if abs(len(ingredient1) - len(ingredient2)) <= 2:
            common_chars = sum(1 for c in ingredient1 if c in ingredient2)
            if common_chars / max(len(ingredient1), len(ingredient2)) > 0.8:
                return True
        
        return False
    
    def standardize_ingredient_list(self, ingredients: List[str]) -> List[str]:
        """Standardize a list of ingredients"""
        standardized = []
        seen = set()
        
        for ingredient in ingredients:
            if not ingredient:
                continue
                
            standard_ingredient = self.standardize_ingredient(ingredient)
            
            # Avoid duplicates (case-insensitive)
            if standard_ingredient.lower() not in seen:
                standardized.append(standard_ingredient)
                seen.add(standard_ingredient.lower())
        
        return standardized
    
    def save_mappings(self):
        """Save updated ingredient mappings to file"""
        mapping_file = self.data_dir / "ingredient_mappings.json"
        mapping_file.parent.mkdir(exist_ok=True)
        
        with open(mapping_file, 'w') as f:
            json.dump(self.ingredient_mappings, f, indent=2)
    
    def get_standardization_report(self) -> Dict:
        """Get report on standardization process"""
        total = self.standardization_stats['total_processed']
        standardized = self.standardization_stats['standardized']
        
        return {
            'total_ingredients_processed': total,
            'successfully_standardized': standardized,
            'standardization_rate': (standardized / total * 100) if total > 0 else 0,
            'new_mappings_created': self.standardization_stats['new_mappings'],
            'unmapped_ingredients': list(self.standardization_stats['unmapped'])[:20],  # Show first 20
            'total_unmapped': len(self.standardization_stats['unmapped'])
        }
    
    def add_custom_mapping(self, ingredient_variations: List[str], standard_name: str):
        """Add custom ingredient mapping"""
        for variation in ingredient_variations:
            self.ingredient_mappings[variation.lower()] = standard_name
    
    def get_inci_name(self, standard_name: str) -> str:
        """Get INCI name for a standardized ingredient"""
        return self.inci_names.get(standard_name, standard_name)


def main():
    """Test the ingredient standardizer"""
    standardizer = IngredientStandardizer()
    
    # Test ingredients
    test_ingredients = [
        "Hyaluronic Acid",
        "sodium hyaluronate",
        "Vitamin C (20%)",
        "L-Ascorbic Acid",
        "Organic Jojoba Oil",
        "Water",
        "Aqua",
        "glycerin",
        "Niacinamide (5%)",
        "Retinol (0.1%)",
        "salicylic acid"
    ]
    
    print("Testing Ingredient Standardizer:")
    print("=" * 50)
    
    for ingredient in test_ingredients:
        standardized = standardizer.standardize_ingredient(ingredient)
        inci_name = standardizer.get_inci_name(standardized)
        print(f"'{ingredient}' → '{standardized}' (INCI: {inci_name})")
    
    print("\n" + "=" * 50)
    report = standardizer.get_standardization_report()
    print("Standardization Report:")
    for key, value in report.items():
        if key != 'unmapped_ingredients':
            print(f"{key}: {value}")
    
    # Save mappings
    standardizer.save_mappings()
    print("\nMappings saved to data/ingredient_mappings.json")


if __name__ == "__main__":
    main()