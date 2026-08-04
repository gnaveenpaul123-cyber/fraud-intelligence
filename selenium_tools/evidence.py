import os

def save_screenshot(driver, case_folder):
    """
    Save a screenshot of the current page.
    """

    screenshot_path = os.path.join(case_folder, "screenshot.png")

    saved = driver.save_screenshot(screenshot_path)
    if not saved or not os.path.isfile(screenshot_path) or os.path.getsize(screenshot_path) == 0:
        raise RuntimeError("Browser did not produce a usable screenshot")

    print(f"Screenshot saved: {screenshot_path}")

    return screenshot_path
