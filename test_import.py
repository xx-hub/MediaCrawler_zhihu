#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify that extract_images_from_html can be imported
"""

print("Testing import of extract_images_from_html...")
try:
    from tools.crawler_util import extract_images_from_html
    print("✓ Successfully imported extract_images_from_html")
    
    # Test the function
    test_html = '<img src="https://example.com/image1.jpg"><img src="https://example.com/image2.jpg">'
    result = extract_images_from_html(test_html)
    print(f"✓ Function works: {result}")
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\nTesting import of extract_text_from_html...")
try:
    from tools.crawler_util import extract_text_from_html
    print("✓ Successfully imported extract_text_from_html")
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
