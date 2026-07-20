import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import unittest
import pandas as pd
import numpy as np
from Project_FORESIGHT.pipeline.cleaning import clean_sku_master, clean_sales

class TestPipeline(unittest.TestCase):
    
    def test_clean_sku_master_categories(self):
        # test data with messy categories
        df = pd.DataFrame({
            "sku_id": ["NBL-1000", "NBL-1001", "NBL-1000"],
            "category": ["furnishings ", "decor", " FURNISHINGS"],
            "unit_cost": [10.0, "15.0", 12.0],
            "list_price": [20.0, 30.0, 24.0]
        })
        
        cleaned = clean_sku_master(df)
        
        # Should deduplicate row index NBL-1000
        self.assertEqual(len(cleaned), 2)
        # Should normalize categories
        self.assertIn("Furnishings", cleaned["category"].values)
        self.assertIn("Decor", cleaned["category"].values)
        
    def test_clean_sales_negatives(self):
        df = pd.DataFrame({
            "date": ["2026-07-01", "2026-07-02"],
            "sku_id": ["NBL-1000", "NBL-1000"],
            "units_sold": [5, -2],
            "unit_price": [10.0, 10.0],
            "revenue": [50.0, np.nan],
            "promo_flag": [0, 1]
        })
        
        cleaned = clean_sales(df)
        
        # Negative units sold should be floored to 0
        self.assertEqual(cleaned.iloc[1]["units_sold"], 0)
        # Revenue for negative (now zero) sales should be recomputed to 0
        self.assertEqual(cleaned.iloc[1]["revenue"], 0)
        
if __name__ == "__main__":
    unittest.main()
