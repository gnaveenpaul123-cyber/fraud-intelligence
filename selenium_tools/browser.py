from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_driver():

    options = Options()

    options.binary_location = "/usr/bin/chromium"

    options.add_argument(
        "--user-data-dir=/home/gnaveenpaul123/.config/chromium"
    )

    options.add_argument("--profile-directory=Default")

    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    return driver