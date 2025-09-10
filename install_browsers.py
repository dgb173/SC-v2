import subprocess
import sys

def install_playwright_browsers():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        print("Playwright browsers installed successfully")
    except Exception as e:
        print(f"Error installing Playwright browsers: {e}")

if __name__ == "__main__":
    install_playwright_browsers()