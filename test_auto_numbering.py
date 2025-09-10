#!/usr/bin/env python3
"""
Test automatic numbering system
"""

from core.numbering.auto_numberer import AutoNumberer

def test_auto_numbering():
    print("Testing automatic numbering system:")
    print("=" * 50)
    
    numberer = AutoNumberer()
    
    # Test sequence that should produce: 1, 1.1, 1.2, 1.2.1, 1.2.2, 1.3, 2, 2.1
    test_levels = [1, 2, 2, 3, 3, 2, 1, 2]
    expected = ["1", "1.1", "1.2", "1.2.1", "1.2.2", "1.3", "2", "2.1"]
    
    print("Testing numbering sequence:")
    for i, level in enumerate(test_levels):
        number = numberer.get_number_for_level(level)
        expected_num = expected[i]
        status = "✓" if number == expected_num else "✗"
        print(f"  H{level} -> {number} (expected {expected_num}) {status}")

if __name__ == "__main__":
    test_auto_numbering()