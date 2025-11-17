# main.py
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time

# Import your config variables and helper functions
import config
import phantom_utils as utils

if __name__ == "__main__":
    if not config.PHANTOM_PASSWORD:
        raise ValueError("PHANTOM_PASSWORD environment variable not set.")
        
    utils.fresh_profile_copy()
    driver = utils.build_driver()

    try:
        utils.open_phantom_popup(driver, config.PHANTOM_ID)
        print("✅ Phantom page opened at:", driver.current_url)

        # 1. Enter Password
        print("Waiting for password field...")
        password_input = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="unlock-form-password-input"]'))
        )
        password_input.send_keys(config.PHANTOM_PASSWORD)

        # 2. Click Unlock
        print("Waiting for unlock button...")
        unlock_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="unlock-form-submit-button"]'))
        )
        unlock_button.click()

        # 3. Verify Login Success
        print("Verifying login success by looking for the Send button...")
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, "//button[div[text()='Send']]"))
        )
        print("🎉 Successfully unlocked Phantom!")

        time.sleep(10)

    except TimeoutException:
        print("❌ Timed out waiting for an element. Check locators or network speed.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()