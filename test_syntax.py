#!/usr/bin/env python3
"""
Simple test script to check syntax of advanced_analyzer.py
"""

import sys
import os


def test_syntax():
    """Test syntax of the advanced analyzer script"""
    try:
        # Try to import/compile the script
        script_path = os.path.join(os.path.dirname(__file__), "advanced_analyzer.py")

        if not os.path.exists(script_path):
            print("❌ [ERROR] File advanced_analyzer.py not found")
            return False

        with open(script_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Try to compile the code
        compile(code, script_path, "exec")
        print("✅ [SUCCESS] Syntax check passed!")
        return True

    except SyntaxError as e:
        print(f"❌ [SYNTAX ERROR] Line {e.lineno}: {e.msg}")
        print(f"   {e.text}")
        return False
    except Exception as e:
        print(f"❌ [ERROR] {e}")
        return False


if __name__ == "__main__":
    print("🔍 [TEST] Checking syntax of advanced_analyzer.py...")
    success = test_syntax()

    if success:
        print("\n🎉 Script is ready to run!")
        print("💡 Usage: python advanced_analyzer.py [--quick]")
    else:
        print("\n⚠️  Please fix syntax errors before running")
