#!/usr/bin/env python3
"""
Syntax check script to verify all Python files are syntactically correct
"""

import ast
import os
from pathlib import Path

def check_syntax(filepath):
    """Check syntax of a Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def main():
    """Main function to check all Python files"""
    print("=== Python Syntax Check ===\n")
    
    # Find all Python files
    project_root = Path(".")
    python_files = list(project_root.rglob("*.py"))
    
    if not python_files:
        print("No Python files found!")
        return
        
    print(f"Found {len(python_files)} Python files to check:\n")
    
    all_passed = True
    
    for py_file in python_files:
        # Skip __pycache__ directories
        if "__pycache__" in str(py_file):
            continue
            
        is_valid, error = check_syntax(py_file)
        if is_valid:
            print(f"✓ {py_file}")
        else:
            print(f"✗ {py_file} - {error}")
            all_passed = False
            
    print(f"\n=== Summary ===")
    if all_passed:
        print("✓ All Python files passed syntax check!")
    else:
        print("✗ Some Python files have syntax errors!")
        
    return all_passed

if __name__ == "__main__":
    main()
