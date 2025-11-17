# phantom_utils.py
import time
import shutil

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

# Import constants from your config file
import config

def fresh_profile_copy():
    """Copy your Default profile into a clean working folder (skip big caches)."""
    if config.WORK_ROOT.exists():
        shutil.rmtree(config.WORK_ROOT)
    config.WORK_ROOT.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns(
        "Cache", "Code Cache", "GPUCache", "ShaderCache", "DawnCache",
        "Service Worker", "GrShaderCache", "BrowserMetrics", "Crashpad",
        "Safe Browsing", "Media Cache"
    )
    shutil.copytree(config.SRC_PROFILE, config.DST_PROFILE, ignore=ignore)

def build_driver():
    """Start Chrome with the copied profile and sane flags for macOS."""
    options = Options()
    options.add_argument(f"user-data-dir={config.WORK_ROOT}")
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
    """Open Phantom’s popup robustly."""
    base = f"chrome-extension://{ext_id}/"
    candidates = ["popup.html", "home.html", "onboarding.html"]
    for page in candidates:
        target = base + page
        try:
            driver.get(target)
            WebDriverWait(driver, 6).until(lambda d: d.current_url.startswith(base))
            return
        except Exception:
            pass
    raise RuntimeError("Failed to open Phantom popup via direct navigation.")