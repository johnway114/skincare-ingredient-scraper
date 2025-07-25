#!/usr/bin/env python3
"""
Create Unified Database
Main script to process all scraped data into a single unified database
"""

import sys
from pathlib import Path

# Add data_processing to path
sys.path.append(str(Path(__file__).parent / "data_processing"))

from data_processing.data_merger import DataMerger


def main():
    """Create unified database from all scraped data"""
    print("🚀 Creating Unified Skincare Ingredient Database")
    print("=" * 60)
    
    try:
        merger = DataMerger()
        output_file = merger.create_unified_database()
        
        if output_file:
            print("\n" + "🎉" * 3 + " SUCCESS! " + "🎉" * 3)
            print(f"\nYour unified database is ready:")
            print(f"📄 JSON: {Path(output_file).parent / 'unified_skincare_database_latest.json'}")
            print(f"📊 CSV:  {Path(output_file).parent / 'unified_skincare_database_latest.csv'}")
            
            print(f"\n📁 Location: {Path(output_file).parent}")
            print(f"\nYou can now:")
            print(f"  • Open the CSV file in Excel/Google Sheets")
            print(f"  • Load the JSON file in any data analysis tool")
            print(f"  • Explore your complete skincare ingredient database!")
            
        else:
            print("\n❌ No scraped data found!")
            print("\n💡 Next steps:")
            print("  1. Run some scrapers first:")
            print("     python main.py ewg --limit 20")
            print("     python main.py incidecoder --limit 20") 
            print("     python main.py cosdna --limit 10")
            print("  2. Then run this script again")
    
    except Exception as e:
        print(f"\n❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()