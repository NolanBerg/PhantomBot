# test_phantom.py
import time
import shutil
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

# === CONFIG ===
PHANTOM_ID = "bfnaelmomeimhlpmgjnjophhpkkoljpa"  # your Phantom extension ID
SRC_PROFILE = Path("/Users/nolanb/Library/Application Support/Google/Chrome/Default")

# We'll copy your Default profile into a dedicated working dir so ChromeDriver has exclusive access.
WORK_ROOT = Path.home() / "phantom-selenium-profile"  # e.g., /Users/nolanb/phantom-selenium-profile
DST_PROFILE = WORK_ROOT / "Default"


def fresh_profile_copy():
    """Copy your Default profile into a clean working folder (skip big caches)."""
    if WORK_ROOT.exists():
        shutil.rmtree(WORK_ROOT)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)

    # Skip large/ephemeral directories to speed up and avoid file locks
    ignore = shutil.ignore_patterns(
        "Cache", "Code Cache", "GPUCache", "ShaderCache", "DawnCache",
        "Service Worker", "GrShaderCache", "BrowserMetrics", "Crashpad",
        "Safe Browsing", "Media Cache"
    )
    shutil.copytree(SRC_PROFILE, DST_PROFILE, ignore=ignore)


def build_driver():
    """Start Chrome with the copied profile and sane flags for macOS."""
    options = Options()

    # Point Chrome at the *root* that contains a "Default" profile directory
    options.add_argument(f"user-data-dir={WORK_ROOT}")
    options.add_argument("profile-directory=Default")

    # Let ChromeDriver reliably attach when using a custom profile
    options.add_argument("--remote-debugging-port=9222")

    # Optional: nicer view
    options.add_argument("--start-maximized")

    # Create the driver (uses chromedriver from PATH, e.g., brew install chromedriver)
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
            url = driver.current_url
            if url.startswith(prefix):
                return True
            seen.add(handle)
        time.sleep(0.25)
    return False


def open_phantom_popup(driver, ext_id):
    """Open Phantom’s popup robustly, handling both tab and popup window flows."""
    base = f"chrome-extension://{ext_id}/"
    candidates = [
        "popup.html",
        "home.html",         # fallback names some extensions use
        "index.html",
        "window.html",
        "onboarding.html",   # if it ever routes there
    ]

    # Try navigate in the current tab first
    for page in candidates:
        target = base + page
        try:
            driver.get("about:blank")
            driver.get(target)
            WebDriverWait(driver, 6).until(lambda d: d.current_url.startswith(base))
            return
        except Exception:
            pass  # try next candidate

    # If navigation gets intercepted (startup pages, etc.), open a *new target* via CDP
    initial_handles = set(driver.window_handles)
    for page in candidates:
        target = base + page
        try:
            driver.execute_cdp_cmd("Target.createTarget", {"url": target})
            # Wait for a new window or tab to appear
            WebDriverWait(driver, 8).until(lambda d: len(set(d.window_handles) - initial_handles) > 0)
            if switch_to_window_with_url_prefix(driver, base, timeout=6):
                return
        except Exception:
            pass

    raise RuntimeError("Failed to open Phantom popup (tried multiple URLs and methods).")


if __name__ == "__main__":
    # 1) Make a fresh working copy of your Chrome profile (so there are no locks)
    fresh_profile_copy()

    # 2) Start Chrome under Selenium control with that profile
    driver = build_driver()

    try:
        # 3) Open Phantom’s popup (robustly)
        open_phantom_popup(driver, PHANTOM_ID)

        print("✅ Phantom opened at:", driver.current_url)
        # Keep it open so you can see it working
        time.sleep(5)

    finally:
        driver.quit()
