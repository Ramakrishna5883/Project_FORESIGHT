import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import unittest
from fastapi.testclient import TestClient
from Project_FORESIGHT.api.main import app

class TestAPI(unittest.TestCase):
    
    def setUp(self):
        self.client = TestClient(app)
        
    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())
        
    def test_health_check(self):
        response = self.client.get("/api/v1/health")
        # Health check should return 200 regardless of DB state (but status dict is returned)
        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json())

if __name__ == "__main__":
    unittest.main()
