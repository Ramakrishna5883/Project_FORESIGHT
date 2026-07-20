import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import unittest
import numpy as np
from Project_FORESIGHT.forecasting.metrics import wape, bias, mae, rmse, r2

class TestModelMetrics(unittest.TestCase):
    
    def test_wape_calculation(self):
        y_true = np.array([10, 20, 30])
        y_pred = np.array([11, 18, 33])
        
        # WAPE = sum(|true - pred|) / sum(true) = (1 + 2 + 3) / 60 = 6 / 60 = 0.1
        self.assertAlmostEqual(wape(y_true, y_pred), 0.1)
        
    def test_bias_calculation(self):
        y_true = np.array([10, 20, 30])
        y_pred = np.array([11, 19, 32])
        
        # Bias = sum(pred - true) / sum(true) = (1 - 1 + 2) / 60 = 2 / 60 = 0.0333333
        self.assertAlmostEqual(bias(y_true, y_pred), 0.03333333333)
        
    def test_metrics_handles_zeros(self):
        y_true = np.array([0, 0, 0])
        y_pred = np.array([1, 2, 3])
        
        # Should handle division by zero cleanly
        self.assertEqual(wape(y_true, y_pred), 0.0)
        self.assertEqual(bias(y_true, y_pred), 0.0)

if __name__ == "__main__":
    unittest.main()
