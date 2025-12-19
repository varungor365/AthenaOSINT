
import unittest
import shutil
from pathlib import Path
from modules.breach_processor import BreachProcessor

class TestBreachProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = BreachProcessor()
        self.test_dir = Path("test_data")
        self.test_dir.mkdir(exist_ok=True)
        self.input_file = self.test_dir / "combos.txt"
        self.output_file = self.test_dir / "clean.txt"
        
        # Create dummy data
        with open(self.input_file, 'w') as f:
            f.write("user1@example.com:pass1\n")
            f.write("user2@gmail.com;pass2\n") # Different sep
            f.write("user1@example.com:pass1\n") # Duplicate
            f.write("invalid_line_here\n")
            f.write("admin@corp.com:SuperSecret123\n")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_clean_combos(self):
        stats = self.processor.clean_combos(self.input_file, self.output_file)
        self.assertEqual(stats['valid_combos'], 3) # user1, user2, admin
        self.assertEqual(stats['duplicates_removed'], 1) 
        self.assertEqual(stats['invalid_format'], 1)
        
        with open(self.output_file, 'r') as f:
            content = f.read()
            self.assertIn("user1@example.com:pass1", content)
            self.assertIn("user2@gmail.com:pass2", content) # Should normalize separator

    def test_sort_combos(self):
        # Clean first
        self.processor.clean_combos(self.input_file, self.output_file)
        sorted_file = self.test_dir / "sorted.txt"
        
        # Sort by length
        self.processor.sort_combos(self.output_file, sorted_file, sort_by='length')
        
        with open(sorted_file, 'r') as f:
            lines = f.readlines()
            # admin@corp.com:SuperSecret123 is longest (14 chars)
            self.assertIn("admin@corp.com", lines[0]) 

    def test_categorize(self):
        self.processor.clean_combos(self.input_file, self.output_file)
        out_dir = self.test_dir / "domains"
        counts = self.processor.categorize_by_domain(self.output_file, out_dir)
        
        self.assertTrue((out_dir / "example.com.txt").exists())
        self.assertTrue((out_dir / "gmail.com.txt").exists())
        self.assertEqual(counts['example.com'], 1)

if __name__ == '__main__':
    unittest.main()
