import time
import shutil
from pathlib import Path
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# === CONFIG ===
PHANTOM_ID = "bfnaelmomeimhlpmgjnjophhpkkoljpa"
# ⚠️ IMPORTANT: Update this to your actual Chrome profile path
SRC_PROFILE = Path("/Users/nolanb/Library/Application Support/Google/Chrome/Default")
WORK_ROOT = Path.home() / "phantom-selenium-profile"
DST_PROFILE = WORK_ROOT / "Default"

# --- SECURITY BEST PRACTICE ---
# Store your password in an environment variable, not directly in the code.
# In your terminal (before running the script), run:
# export PHANTOM_PASSWORD="your_super_secret_password"
PHANTOM_PASSWORD = os.getenv("PHANTOM_PASSWORD")

def fresh_profile_copy():
    """Copy your Default profile into a clean working folder (skip big caches)."""
    if WORK_ROOT.exists():
        shutil.rmtree(WORK_ROOT)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns(
        "Cache", "Code Cache", "GPUCache", "ShaderCache", "DawnCache",
        "Service Worker", "GrShaderCache", "BrowserMetrics", "Crashpad",
        "Safe Browsing", "Media Cache"
    )
    shutil.copytree(SRC_PROFILE, DST_PROFILE, ignore=ignore)

def build_driver():
    """Start Chrome with the copied profile and sane flags for macOS."""
    options = Options()
    options.add_argument(f"user-data-dir={WORK_ROOT}")
    options.add_argument("profile-directory=Default")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver

def switch_to_window_with_url_prefix(driver, prefix, timeout=10):
    """Switch to the first window whose current_url starts with prefix."""
    end = time.time() + timeout
    seen = set()
    while time.time() < end:
        for handle in driver.window_handles:
            if handle in seen:
                continue
            driver.switch_to.window(handle)
            if driver.current_url.startswith(prefix):
                return True
            seen.add(handle)
        time.sleep(0.25)
    return False

def open_phantom_popup(driver, ext_id):
    """Open Phantom’s popup robustly, handling both tab and popup window flows."""
    base = f"chrome-extension://{ext_id}/"
    candidates = ["popup.html", "home.html", "index.html", "window.html", "onboarding.html"]
    for page in candidates:
        target = base + page
        try:
            driver.get("about:blank")
            driver.get(target)
            WebDriverWait(driver, 6).until(lambda d: d.current_url.startswith(base))
            return
        except Exception:
            pass
    initial_handles = set(driver.window_handles)
    for page in candidates:
        target = base + page
        try:
            driver.execute_cdp_cmd("Target.createTarget", {"url": target})
            WebDriverWait(driver, 8).until(lambda d: len(set(d.window_handles) - initial_handles) > 0)
            if switch_to_window_with_url_prefix(driver, base, timeout=6):
                return
        except Exception:
            pass
    raise RuntimeError("Failed to open Phantom popup (tried multiple URLs and methods).")

if __name__ == "__main__":
    if not PHANTOM_PASSWORD:
        raise ValueError("PHANTOM_PASSWORD environment variable not set. Please set it before running.")
        
    fresh_profile_copy()
    driver = build_driver()

    try:
        open_phantom_popup(driver, PHANTOM_ID)
        print("✅ Phantom page opened at:", driver.current_url)

        # 1. Wait for the password input using its exact data-testid
        print("Waiting for password field...")
        password_input = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="unlock-form-password-input"]'))
        )
        print("Typing password...")
        password_input.send_keys(PHANTOM_PASSWORD)

        # 2. Wait for the unlock button using its exact data-testid
        print("Waiting for unlock button...")
        unlock_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="unlock-form-submit-button"]'))
        )
        print("Clicking unlock...")
        unlock_button.click()

        # 3. VERIFICATION STEP: Find the button using its visible text via XPath.
        print("Verifying login success by looking for the Send button...")
        send_button = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, "//button[div[text()='Send']]"))
        )
        print("🎉 Successfully unlocked Phantom!")

        # Keep it open so you can see the result
        time.sleep(10)

    except TimeoutException:
        print("❌ Timed out waiting for a page element. Double-check your locators or network speed.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()