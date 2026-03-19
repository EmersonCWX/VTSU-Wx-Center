"""
CoCoRaHS Backend - Submits data to CoCoRaHS using Selenium
Receives form data from VTSU form and automates submission to VT-CL-14
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# CoCoRaHS login credentials
COCORAHS_USERNAME = "lscwx"
COCORAHS_PASSWORD = "stratus"
COCORAHS_STATION = "VT-CL-14"
COCORAHS_LOGIN_URL = "https://www.cocorahs.org/Login.aspx"
COCORAHS_SUBMIT_URL = "https://www.cocorahs.org/Admin/MyDataEntry/DailyPrecipReport.aspx"


def setup_driver():
    """Initialize Selenium WebDriver with Chrome"""
    chrome_options = Options()
    # Uncomment the next line to run headless (no visible browser)
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
        raise


def login_to_cocorahs(driver):
    """Log in to CoCoRaHS"""
    try:
        logger.info("Navigating to CoCoRaHS login...")
        driver.get(COCORAHS_LOGIN_URL)
        time.sleep(2)
        
        # Log all input fields found on the page
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        logger.info(f"Found {len(all_inputs)} input fields on page")
        for idx, inp in enumerate(all_inputs):
            inp_id = inp.get_attribute("id")
            inp_name = inp.get_attribute("name")
            inp_type = inp.get_attribute("type")
            logger.info(f"  [{idx}] type={inp_type}, id={inp_id}, name={inp_name}")
        
        # Find all buttons
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        logger.info(f"Found {len(all_buttons)} button elements")
        for idx, btn in enumerate(all_buttons):
            btn_id = btn.get_attribute("id")
            btn_name = btn.get_attribute("name")
            btn_text = btn.text
            logger.info(f"  [{idx}] id={btn_id}, name={btn_name}, text={btn_text}")
        
        # Also check for inputs in forms
        all_forms = driver.find_elements(By.TAG_NAME, "form")
        logger.info(f"Found {len(all_forms)} form elements")
        
        # Try to find username field by checking multiple attributes
        username_field = None
        password_field = None
        login_button = None
        
        # Search for username field
        selectors = [
            (By.NAME, "UserName"),
            (By.NAME, "username"),
            (By.ID, "UserName"),
            (By.ID, "username"),
            (By.NAME, "txtUserName"),
            (By.ID, "txtUserName"),
        ]
        
        for selector in selectors:
            try:
                username_field = driver.find_element(*selector)
                logger.info(f"Found username field using {selector}")
                break
            except:
                continue
        
        if not username_field:
            # Try finding by placeholder or other means
            try:
                username_field = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
                logger.info("Found username field using CSS selector for text input")
            except:
                logger.error("Could not find username field by any method")
                return False
        
        # Search for password field
        selectors = [
            (By.NAME, "Password"),
            (By.NAME, "password"),
            (By.ID, "Password"),
            (By.ID, "password"),
            (By.NAME, "txtPassword"),
            (By.ID, "txtPassword"),
        ]
        
        for selector in selectors:
            try:
                password_field = driver.find_element(*selector)
                logger.info(f"Found password field using {selector}")
                break
            except:
                continue
        
        if not password_field:
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                logger.info("Found password field using CSS selector for password input")
            except:
                logger.error("Could not find password field")
                return False
        
        # Search for login button
        selectors = [
            (By.NAME, "btnLogin"),
            (By.ID, "btnLogin"),
            (By.CSS_SELECTOR, "button[type='submit']"),
        ]
        
        for selector in selectors:
            try:
                login_button = driver.find_element(*selector)
                logger.info(f"Found login button using {selector}")
                break
            except:
                continue
        
        if not login_button:
            logger.error("Could not find login button")
            return False
        
        # Fill in credentials
        logger.info(f"Filling username: {COCORAHS_USERNAME}")
        username_field.clear()
        username_field.send_keys(COCORAHS_USERNAME)
        
        logger.info("Filling password")
        password_field.clear()
        password_field.send_keys(COCORAHS_PASSWORD)
        
        logger.info("Clicking login button")
        login_button.click()
        
        # Wait for redirect
        time.sleep(4)
        logger.info(f"After login, page title: {driver.title}, URL: {driver.current_url}")
        
        # Check if login was successful
        if "Login" in driver.title or "login" in driver.current_url.lower():
            logger.error("Still on login page after clicking login button")
            return False
        
        logger.info("Successfully logged in to CoCoRaHS")
        return True
        
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def navigate_to_precip_form(driver):
    """Navigate to the daily precipitation report form"""
    try:
        logger.info("Navigating to precipitation report form...")
        
        # We should already be on the form after login, but verify
        current_url = driver.current_url
        logger.info(f"Current URL: {current_url}")
        
        # If not on the correct page, navigate to it
        if "DailyPrecipReport" not in current_url:
            logger.info(f"Not on precip form page, navigating to {COCORAHS_SUBMIT_URL}")
            driver.get(COCORAHS_SUBMIT_URL)
        
        # Wait for page to load - just check for any input fields or select elements
        time.sleep(3)
        
        # Log all inputs and selects on page to help debug
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            selects = driver.find_elements(By.TAG_NAME, "select")
            logger.info(f"Found {len(inputs)} input fields and {len(selects)} select dropdowns on form page")
        except Exception as e:
            logger.warning(f"Could not enumerate form elements: {str(e)}")
        
        logger.info("Precipitation form page loaded")
        return True
        
    except Exception as e:
        logger.error(f"Failed to navigate to form: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def select_station(driver):
    """Station is locked to login, no selection needed"""
    logger.info(f"Station {COCORAHS_STATION} is locked to user login, skipping selection")
    return True


def fill_form_fields(driver, form_data):
    """Fill in the precipitation report form with data"""
    try:
        logger.info("Filling form fields...")
        
        # Wait for form to be interactive
        time.sleep(2)
        
        # Log all available form elements to help with field discovery
        inputs = driver.find_elements(By.TAG_NAME, "input")
        selects = driver.find_elements(By.TAG_NAME, "select")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        logger.info(f"Found {len(inputs)} inputs, {len(selects)} selects, {len(textareas)} textareas on form")
        
        # Log all text/number inputs (excluding hidden/submit/checkbox)
        logger.info("Text/number input fields on form:")
        for idx, inp in enumerate(inputs):
            inp_type = inp.get_attribute("type")
            if inp_type not in ['hidden', 'submit', 'checkbox', 'button']:
                inp_id = inp.get_attribute("id")
                inp_name = inp.get_attribute("name")
                inp_placeholder = inp.get_attribute("placeholder")
                logger.info(f"  [{idx}] type={inp_type}, id='{inp_id}', name='{inp_name}', placeholder='{inp_placeholder}'")
        
        # Parse the report date
        report_datetime = datetime.fromisoformat(form_data['reportDate'])
        month = str(report_datetime.month).zfill(2)
        day = str(report_datetime.day).zfill(2)
        year = str(report_datetime.year)
        hour = str(report_datetime.hour).zfill(2)
        minute = str(report_datetime.minute).zfill(2)
        
        # Map of field names to CoCoRaHS field IDs (discovered from form inspection)
        fields_to_fill = {
            'date': ('frmReport_dcObsDate_di', f"{month}/{day}/{year}"),
            'time': ('frmReport_tObsTime_txtTime', f"{hour}:{minute}"),
            'gaugeCatch': ('frmReport_prTotalPrecip__ctl1_tbPrecip', str(form_data.get('gaugeCatch', ''))),
            'snowfallAmount': ('frmReport_prNewSnowAmount__ctl1_tbPrecip', str(form_data.get('snowfallAmount', ''))),
            'snowfallSWE': ('frmReport_prSnowCore__ctl1_tbPrecip', str(form_data.get('snowfallSWE', ''))),
            'snowpackDepth': ('frmReport_prTotalSnowDepth__ctl1_tbPrecip', str(form_data.get('snowpackDepth', ''))),
            'snowpackSWE': ('frmReport_prSWE__ctl1_tbPrecip', str(form_data.get('snowpackSWE', ''))),
        }
        
        # Fill each field
        for field_name, (field_id, field_value) in fields_to_fill.items():
            if field_value and field_value.strip():
                try:
                    field = driver.find_element(By.ID, field_id)
                    field.clear()
                    field.send_keys(field_value)
                    logger.info(f"Filled {field_name}: {field_value}")
                except Exception as e:
                    logger.warning(f"Could not fill {field_name} (ID: {field_id}): {str(e)}")
        
        # Fill Notes/Comments
        if form_data.get('additionalNotes'):
            try:
                notes_field = driver.find_element(By.ID, 'frmReport_txtNotes')
                notes_field.clear()
                notes_field.send_keys(str(form_data['additionalNotes']))
                logger.info(f"Filled Notes: {form_data['additionalNotes']}")
            except Exception as e:
                logger.warning(f"Could not fill notes field: {str(e)}")
        
        logger.info("Form fields filled successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error filling form: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def submit_form(driver):
    """Submit the form"""
    try:
        logger.info("Submitting form...")
        
        time.sleep(2)
        
        # Log all available buttons to help find the submit button
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        logger.info(f"Found {len(all_buttons)} button elements and {len(all_inputs)} input elements")
        
        submit_button = None
        
        # Look for buttons with type="submit" or text containing "Submit"
        logger.info("Searching for submit button...")
        for btn in all_buttons:
            btn_text = btn.text.strip()
            btn_type = btn.get_attribute("type")
            btn_id = btn.get_attribute("id")
            btn_name = btn.get_attribute("name")
            logger.info(f"  Button: type='{btn_type}', text='{btn_text}', id='{btn_id}', name='{btn_name}'")
            
            if btn_type == "submit" or "submit" in btn_text.lower():
                submit_button = btn
                logger.info(f"  -> Using this button as submit button")
                break
        
        # If not found in buttons, look in input elements with type="submit"
        if not submit_button:
            for inp in all_inputs:
                inp_type = inp.get_attribute("type")
                if inp_type == "submit":
                    inp_id = inp.get_attribute("id")
                    inp_value = inp.get_attribute("value")
                    logger.info(f"Found submit input: id='{inp_id}', value='{inp_value}'")
                    submit_button = inp
                    break
        
        if not submit_button:
            logger.error("Could not find submit button")
            return False
        
        logger.info("Clicking submit button")
        submit_button.click()
        
        # Wait for submission to complete
        time.sleep(3)
        
        logger.info(f"After submission, page title: {driver.title}, URL: {driver.current_url}")
        
        # Check for success indicators
        try:
            # Check for success message
            success_elements = driver.find_elements(By.CLASS_NAME, "successmessage")
            if success_elements:
                logger.info("Success message found on page")
                return True
        except:
            pass
        
        # Check if page redirected
        if "DailyPrecipReport" not in driver.current_url:
            logger.info("Redirected after submission, likely successful")
            return True
        
        # If still on form, check for errors
        try:
            error_messages = driver.find_elements(By.CLASS_NAME, "errormessage")
            if error_messages:
                logger.warning(f"Error messages found: {[e.text for e in error_messages]}")
                return False
        except:
            pass
        
        logger.info("Form submitted successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to submit form: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


@app.route('/api/submit-cocorahs', methods=['POST'])
def submit_cocorahs():
    """API endpoint to submit data to CoCoRaHS"""
    try:
        # Get JSON data from request
        form_data = request.get_json()
        
        logger.info(f"Received form data: {json.dumps(form_data, indent=2)}")
        
        # Validate required fields
        if not form_data.get('reportDate'):
            return jsonify({
                'success': False,
                'message': 'Report date is required'
            }), 400
        
        # Initialize Selenium driver
        driver = setup_driver()
        
        try:
            # Login to CoCoRaHS
            if not login_to_cocorahs(driver):
                return jsonify({
                    'success': False,
                    'message': 'Failed to log in to CoCoRaHS'
                }), 401
            
            # Navigate to precipitation form
            if not navigate_to_precip_form(driver):
                return jsonify({
                    'success': False,
                    'message': 'Failed to navigate to precipitation report form'
                }), 400
            
            # Select station
            if not select_station(driver):
                return jsonify({
                    'success': False,
                    'message': f'Failed to select station {COCORAHS_STATION}'
                }), 400
            
            # Fill form fields
            if not fill_form_fields(driver, form_data):
                return jsonify({
                    'success': False,
                    'message': 'Failed to fill form fields'
                }), 400
            
            # Submit form
            if not submit_form(driver):
                return jsonify({
                    'success': False,
                    'message': 'Failed to submit form to CoCoRaHS'
                }), 400
            
            logger.info("Data successfully submitted to CoCoRaHS")
            return jsonify({
                'success': True,
                'message': 'Report successfully submitted to CoCoRaHS for station VT-CL-14'
            }), 200
        
        finally:
            # Always close the driver
            driver.quit()
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    print("=" * 60)
    print("CoCoRaHS Backend Service Starting")
    print("=" * 60)
    print(f"Station: {COCORAHS_STATION}")
    print(f"Username: {COCORAHS_USERNAME}")
    print("Running on http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='localhost', port=5000)
