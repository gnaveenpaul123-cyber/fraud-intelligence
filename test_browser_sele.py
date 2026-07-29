from selenium_tools.browser import get_driver

driver = get_driver()

print("Browser opened successfully!")

driver.get("https://www.reddit.com")

input("Press Enter to close the browser...")

driver.quit()