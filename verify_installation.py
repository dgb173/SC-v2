import subprocess
import sys
import os

def check_python():
    """Check if Python is available"""
    try:
        result = subprocess.run([sys.executable, "--version"], 
                              capture_output=True, text=True)
        print(f"✓ Python version: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"✗ Error checking Python: {e}")
        return False

def check_pip():
    """Check if pip is available"""
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True)
        print(f"✓ Pip version: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"✗ Error checking pip: {e}")
        return False

def check_virtual_env():
    """Check if we're in a virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✓ Running in virtual environment")
    else:
        print("⚠ Not running in virtual environment")
    return in_venv

def check_requirements():
    """Check if requirements.txt exists and is readable"""
    if os.path.exists("requirements.txt"):
        try:
            with open("requirements.txt", "r") as f:
                lines = f.readlines()
                print(f"✓ Found requirements.txt with {len(lines)} lines")
                for i, line in enumerate(lines[:5]):  # Show first 5 lines
                    print(f"  {i+1}. {line.strip()}")
                if len(lines) > 5:
                    print(f"  ... and {len(lines) - 5} more lines")
            return True
        except Exception as e:
            print(f"✗ Error reading requirements.txt: {e}")
            return False
    else:
        print("✗ requirements.txt not found")
        return False

def test_imports():
    """Test importing key modules"""
    print("\nTesting module imports...")
    
    modules_to_test = [
        "streamlit",
        "pandas", 
        "bs4",
        "requests",
        "lxml",
        "playwright"
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ {module} imported successfully")
        except ImportError as e:
            print(f"✗ Error importing {module}: {e}")
    
    # Test local modules
    try:
        from modules import estudio_scraper
        print("✓ estudio_scraper imported successfully")
    except ImportError as e:
        print(f"✗ Error importing estudio_scraper: {e}")
        
    try:
        from modules import analisis_avanzado
        print("✓ analisis_avanzado imported successfully")
    except ImportError as e:
        print(f"✗ Error importing analisis_avanzado: {e}")

def main():
    print("=== Installation Verification Script ===\n")
    
    check_python()
    check_pip()
    check_virtual_env()
    check_requirements()
    test_imports()
    
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    main()