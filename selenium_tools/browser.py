from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def get_driver():

    options = Options()

    options.binary_location = "/usr/bin/chromium"

    options.add_argument(
        "--user-data-dir=/home/gnaveenpaul123/.config/fraud_profile"
    )

    options.add_argument("--profile-directory=Default")

    options.add_argument("--start-maximized")

    print("Creating Chrome driver...")

    service = Service(
        log_output="chromedriver.log",
        service_args=["--verbose"]
    )

    driver = webdriver.Chrome(
        service=service,
        options=options
    )

    print("Chrome driver created!")

    return driver