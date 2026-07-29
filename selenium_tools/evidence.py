import os

def save_screenshot(driver, case_folder):
    """
    Save a screenshot of the current page.
    """

    screenshot_path = os.path.join(case_folder, "screenshot.png")

    driver.save_screenshot(screenshot_path)

    print(f"Screenshot saved: {screenshot_path}")

    return screenshot_path