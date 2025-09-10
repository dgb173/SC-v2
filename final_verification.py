#!/usr/bin/env python3
"""
Final verification script to check if the project is ready for Streamlit deployment
"""

import os
import sys
import subprocess
from pathlib import Path

def check_project_structure():
    """Check if all required files and directories exist"""
    print("=== Checking Project Structure ===")
    
    required_files = [
        "app.py",
        "requirements.txt",
        "README.md"
    ]
    
    required_dirs = [
        "modules"
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
            
    for dir in required_dirs:
        if not os.path.exists(dir):
            missing_dirs.append(dir)
            
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files present")
        
    if missing_dirs:
        print(f"✗ Missing directories: {missing_dirs}")
        return False
    else:
        print("✓ All required directories present")
        
    # Check modules directory contents
    modules_dir = Path("modules")
    if modules_dir.exists():
        module_files = list(modules_dir.glob("*.py"))
        print(f"✓ Found {len(module_files)} module files:")
        for module in module_files:
            print(f"  - {module.name}")
            
    return True

def check_requirements():
    """Check requirements.txt format and content"""
    print("\n=== Checking Requirements ===")
    
    if not os.path.exists("requirements.txt"):
        print("✗ requirements.txt not found")
        return False
        
    try:
        with open("requirements.txt", "r") as f:
            content = f.read().strip()
            lines = [line.strip() for line in content.split("\n") if line.strip() and not line.startswith("#")]
            
        print(f"✓ requirements.txt has {len(lines)} dependencies:")
        for line in lines:
            print(f"  - {line}")
            
        # Check for required dependencies
        required_deps = ["streamlit", "playwright", "pandas", "beautifulsoup4", "requests", "lxml"]
        missing_deps = []
        
        for dep in required_deps:
            if not any(dep in line.lower() for line in lines):
                missing_deps.append(dep)
                
        if missing_deps:
            print(f"⚠ Warning: These dependencies might be missing: {missing_deps}")
        else:
            print("✓ All core dependencies appear to be present")
            
        return True
    except Exception as e:
        print(f"✗ Error reading requirements.txt: {e}")
        return False

def check_python_environment():
    """Check Python version and virtual environment"""
    print("\n=== Checking Python Environment ===")
    
    # Check Python version
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("⚠ Warning: Python 3.8+ is recommended")
        
    # Check if in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✓ Running in virtual environment")
    else:
        print("⚠ Not running in virtual environment (recommended)")
        
    return True

def check_imports():
    """Test importing key modules"""
    print("\n=== Testing Module Imports ===")
    
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    modules_to_test = [
        ("streamlit", "st"),
        ("pandas", "pd"),
        ("bs4", "BeautifulSoup"),
        ("requests", "requests"),
        ("lxml", "lxml"),
        ("playwright.async_api", "async_playwright")
    ]
    
    all_passed = True
    
    for module_import, module_name in modules_to_test:
        try:
            __import__(module_import)
            print(f"✓ {module_import} imported successfully")
        except ImportError as e:
            print(f"✗ Error importing {module_import}: {e}")
            all_passed = False
            
    # Test local modules
    local_modules = [
        "modules.estudio_scraper",
        "modules.analisis_avanzado",
        "modules.utils"
    ]
    
    for module in local_modules:
        try:
            __import__(module)
            print(f"✓ {module} imported successfully")
        except ImportError as e:
            print(f"✗ Error importing {module}: {e}")
            all_passed = False
            
    return all_passed

def check_playwright():
    """Check Playwright installation"""
    print("\n=== Checking Playwright ===")
    
    try:
        # Try to run playwright install command
        result = subprocess.run([sys.executable, "-m", "playwright", "install-deps"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✓ Playwright dependencies check completed")
        else:
            print(f"⚠ Playwright dependencies check returned code {result.returncode}")
            print(f"  Output: {result.stdout}")
            print(f"  Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⚠ Playwright dependencies check timed out")
    except Exception as e:
        print(f"⚠ Could not check Playwright dependencies: {e}")
        
    return True

def main():
    """Main verification function"""
    print("=== Streamlit Project Verification ===\n")
    
    checks = [
        check_project_structure,
        check_requirements,
        check_python_environment,
        check_imports,
        check_playwright
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"✗ Check {check.__name__} failed with error: {e}")
            results.append(False)
            
    print("\n=== Summary ===")
    if all(results):
        print("✓ All checks passed! The project should be ready for Streamlit deployment.")
        print("\nTo run the application:")
        print("  streamlit run app.py")
    else:
        failed_count = len([r for r in results if not r])
        print(f"✗ {failed_count} check(s) failed. Please review the errors above.")
        
    return all(results)

if __name__ == "__main__":
    main()