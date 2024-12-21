import sys
import json
import time
import random
import pyautogui
import pygetwindow as gw
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Define proxy details file
passwords_file_path = "passwords.txt"

# Check if a queue file path argument is passed, otherwise use a default path
queue_file_path = sys.argv[1] if len(sys.argv) > 1 else 'queue.json'

# Read passwords into a dictionary
def load_passwords(file_path):
    passwords = {}
    with open(file_path, 'r') as f:
        for line in f:
            key, value = line.strip().split(' : ')
            passwords[key.strip().lower()] = value.strip()
    return passwords

passwords = load_passwords(passwords_file_path)

# Function to wait for the proxy authentication popup
def wait_for_proxy_popup(proxy_user, proxy_pass):
    # Continuously check for the proxy popup window until it's found
    while True:
        try:
            # Look for the popup window by its title
            popup_window = gw.getWindowsWithTitle("Authentication Required")
            if popup_window:
                popup_window[0].activate()
                pyautogui.typewrite(proxy_user)
                pyautogui.press("tab")
                pyautogui.typewrite(proxy_pass)
                pyautogui.press("enter")
                print("Proxy authentication completed.")
                break  # Exit the loop after successfully handling the popup
            else:
                print("Waiting for proxy authentication popup...")
                time.sleep(2)  # Wait for 2 seconds before checking again
        except Exception as e:
            print(f"Error while waiting for popup: {e}")
            time.sleep(2)

# Function to set up browser with proxy settings
def setup_browser_with_proxy(form_data):
    options = Options()
    options.set_preference("network.proxy.type", 1)
    
    # Determine the appropriate proxy password based on city or state
    city_or_state = form_data.get("City", form_data.get("State")).strip().lower()
    proxy_pass = None

    # Search for city match first, then state if no city match found
    if form_data.get("City") and form_data["City"].strip().lower() in passwords:
        proxy_pass = passwords[form_data["City"].strip().lower()]
    elif form_data.get("State") and form_data["State"].strip().lower() in passwords:
        proxy_pass = passwords[form_data["State"].strip().lower()]

    if proxy_pass:
        proxy_host = "geo.iproyal.com"
        proxy_port = "12321"
        options.set_preference("network.proxy.http", proxy_host)
        options.set_preference("network.proxy.http_port", int(proxy_port))
        options.set_preference("network.proxy.ssl", proxy_host)
        options.set_preference("network.proxy.ssl_port", int(proxy_port))
        options.set_preference("network.proxy.share_proxy_settings", True)
        options.set_preference("signon.autologin.proxy", True)

        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)

        wait_for_proxy_popup("Kavesh", proxy_pass)  # Use static username 'Kavesh'
        return driver, proxy_pass
    else:
        print(f"No matching proxy password found for City: {city_or_state} or State: {form_data.get('State', '')}.")
        return None, None

# Function to introduce random delays
def random_delay_between_typing():
    """Introduce a random delay between typing characters."""
    time.sleep(random.uniform(0.2, 0.5))  # Adjust delay range for typing

# Function to calculate delays based on field typing times
def calculate_delays():
    """Calculate delays based on field typing times."""
    # Define fixed delays (in seconds) for each field
    delays = {
        "FirstName": random.uniform(2, 3),
        "LastName": random.uniform(2, 3),
        "Email": random.uniform(1.5, 2),
        "PhoneNumber": random.uniform(1.5, 2),
        "State": random.uniform(1.5, 2),
        "ZipCode": random.uniform(1, 1.5),
        "Address": random.uniform(1.5, 2)
    }

    total_delay = sum(delays.values())
    return delays, total_delay

# Function to submit the form
def submit_form(driver, form_data, proxy_pass):
    form_url = "https://yourinsuranceneed.com/medicare-insurance/"
    driver.get(form_url)

    delays, total_delay = calculate_delays()

    try:
        fields = [
            ("FirstName", form_data["FirstName"]),
            ("LastName", form_data["LastName"]),
            ("Email", form_data["Email"]),
            ("PhoneNumber", form_data["PhoneNumber"]),
            ("State", form_data["State"]),
            ("ZipCode", form_data["ZipCode"]),
            ("Address", form_data["Address"])
        ]

        for field_name, value in fields:
            field_element = driver.find_element(By.NAME, field_name)
            delay = delays[field_name]
            time.sleep(delay)  # Delay before interacting with the field
            field_element.clear()
            for char in value:
                field_element.send_keys(char)
                random_delay_between_typing()

        # Wait for the Legal checkbox to be clickable and click it if it's not already checked
        try:
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "Legal"))
            )
            time.sleep(total_delay / 2)  # Add a delay before clicking the checkbox
            if not checkbox.is_selected():
                checkbox.click()
                print("Agreement checkbox clicked.")
            else:
                print("Agreement checkbox already checked.")
        except TimeoutException:
            print("No checkbox found. Proceeding without it.")

        # Find the submit button and click it
        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        time.sleep(total_delay / 2)  # Add a delay before clicking submit
        submit_button.click()

        # Static 10-second wait after form submission before considering the page fully loaded
        time.sleep(10)

        print("Form submitted and page loaded.")

        # Log the password used along with phone number and user
        log_password_used(form_data["PhoneNumber"], "Kavesh", proxy_pass)

    except Exception as e:
        print(f"Error during form submission: {e}")

    driver.quit()

# Function to log the password used along with phone number and user
def log_password_used(phone_number, user, password):
    log_file_path = "password_log.txt"

    # Format the log entry
    log_entry = f"Phone Number: {phone_number}, User: {user}, Password: {password}\n"

    # Append to the log file
    with open(log_file_path, 'a') as log_file:
        log_file.write(log_entry)

# Function to process the form submission queue
def process_queue():
    try:
        with open(queue_file_path, 'r') as file:
            queue = json.load(file)

        if queue:
            form_data = queue.pop(0)  # Pop the first item
            with open(queue_file_path, 'w') as file:
                json.dump(queue, file, indent=4)  # Update the queue file

            # Start form submission process
            driver, proxy_pass = setup_browser_with_proxy(form_data)
            if driver and proxy_pass:
                submit_form(driver, form_data, proxy_pass)
            else:
                print("Failed to setup browser with proxy.")

    except Exception as e:
        print(f"Error processing the queue: {e}")

process_queue()
