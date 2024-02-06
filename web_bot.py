import time
import json
import random
import traceback
import pandas as pd
from utils import *
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.common.exceptions import WebDriverException

class BotException(Exception):
	pass


def select_options(element, attribute, input_str):

	try:
		select_option = element.find_element(By.XPATH, f"""//{attribute}[
										{to_xpath_converter([('@name', input_str),
															('@id', input_str),
															('text()', input_str),
															('@class', input_str)])}]""")

		if 'radio' in select_option.get_attribute('id'):
			try:
				select_option.click()
				time.sleep(1)
			except ElementClickInterceptedException:
				label_xpath = "//label[contains(@for,'radio')]"
				select_option = element.find_element(By.XPATH, label_xpath)
				select_option.click()
				time.sleep(1)
		else:
			options = select_option.find_elements(By.TAG_NAME, "option")

			# Iterate over the options and click the first enabled one
			for option in options:
				if option.is_enabled() and option.get_attribute("value"):
					option.click()
					break
			time.sleep(1)
	except (NoSuchElementException):
		return

def filter_submit_buttons(driver, form_element, submit_buttons):
	"""
	Filter elements that have the given ancestor_element in their ancestor chain.

	:param driver: Selenium WebDriver instance.
	:param ancestor_element: The ancestor WebElement to compare against.
	:param elements_list: List of WebElements to filter.
	:return: A list of elements that have ancestor_element in their ancestors.
	"""
	correct_buttons = []

	for element in submit_buttons:
		# Check if the current element has the given ancestor_element in its ancestors
		if driver.execute_script("return arguments[0].contains(arguments[1]);", form_element, element):
			correct_buttons.append(element)

	return correct_buttons

def click_submit(element, driver):
	"""
	Clicks on the submit button to send the filled form

	Args:
		driver: webdriver object
		index: the index of the element in the list
		button: attribute name, "button" or "input"
	"""
	include_tags = ['input', 'button']
	include_attributes_per_tag = {
		'input': {'type': ['submit']},
		'button': {}
	}
	exclude_attributes_per_tag = {}

	submit_buttons = element.find_elements(By.XPATH, """//input[contains(@type, 'submit')] |
														//button""")
	submit_buttons = filter_submit_buttons(driver, element, submit_buttons)
	for button in submit_buttons:
		try:
			button.click()
			return
		except (NoSuchElementException, ElementNotInteractableException):
			continue
		except WebDriverException as e:
			raise BotException("Submit button click exception")
	raise BotException("Submit button click exception")

def click_on_checkbox(element, driver):
	"""
	Clicks on the checkbox for acceptance, to be able to submit the form

	Args:
		driver: webdriver object
	"""
	try:
		data_collection_checkbox = element.find_element(By.XPATH, """
															//input[@type='checkbox' and 
															(@aria-required='true' or
															@required='required' or
															@required or
															contains(@name,'accept'))]""")
		driver.execute_script("arguments[0].click();", data_collection_checkbox)
		# data_collection_checkbox.click()
		print("Checkbox clicked")
		time.sleep(random.uniform(2.0, 3.0))
	except (NoSuchElementException, ElementNotInteractableException):
		try:
			data_collection_checkbox = element.find_element(By.XPATH, "//input[@type='checkbox']")
		except NoSuchElementException:
			pass

def fill_input_by_label(element, xpath_expression, message, checker):
	"""
	Finds an input element based on the text of its associated label.

	:param driver: The Selenium WebDriver.
	:param label_text: The text contained in the label associated with the input.
	:return: The input WebElement if found, None otherwise.
	"""
	try:
		# Find the label by its text using XPath

		label = element.find_element(By.XPATH, xpath_expression)
		
		# Get the 'for' attribute, which should match the input element's ID
		input_id = label.get_attribute('for')
		
		if input_id:
			# Find and return the input element by its ID
			section_input = element.find_element(By.ID, input_id)
			if section_input.id in checker:
				return None
			section_input.send_keys(message)
			time.sleep(random.uniform(1.0, 2.0))
			return section_input.id
		else:
			return None
	except NoSuchElementException as e:
		return None

def check_for_success_alert(driver, confirmation_messages):
	"""
	Checks for the "Successfull submission" alert after form submission

	Args:
		driver: webdriver object
		confirmation_messages: list of strings to check if the submission was successfull or failed
	
	Returns:
		boolean: successfull or failed
	"""
	try:
		# Wait for the success alert to be visible (timeout 5 seconds)
		success_alert = WebDriverWait(driver, 5).until(
			EC.visibility_of_element_located((By.CLASS_NAME, "alert-success"))
		)
		# Check if the expected text is in the success alert
		for message in confirmation_messages:
			if message in success_alert.text:
				return True
	except Exception as e:
		return False
	return False

def is_submission_confirmed(driver, confirmation_messages):
	"""
	Checks for the "Successfull submission" message after form submission on the webpage

	Args:
		driver: webdriver object
		confirmation_messages: list of strings to check if the submission was successfull or failed
	
	Returns:
		boolean: successfull or failed
	"""
	for message in confirmation_messages:
		try:
			confirmation_message_xpath = f"//*[{to_xpath_converter([('.', message)])}]"
	
			# Wait for the confirmation message to be visible (timeout in 10 seconds)
			confirmation_message_element = WebDriverWait(driver, 3).until(
				EC.visibility_of_element_located((By.XPATH, confirmation_message_xpath))
			)
			print(f"'{message}' was found on page")
			return True
		except:
			continue
	return False

def check_form_disapears(form_element, driver):

	try:
		form = find_contact_form(driver)
		if form_element == form:
			print("Form still exists")
			return False
	except NoSuchElementException:
		return True
	return True

def fill_the_form(element, tag, search_array, input_str, checker):

	inputed = fill_in_section(element, tag, search_array, input_str, checker)
	if not inputed:
		xpath = []
		for text in search_array:
			xpath.append(xpath_lower('text()', text))
		xpath_expression = f"//label[{' and '.join(xpath)}]"
		inputed = fill_input_by_label(element, xpath_expression, input_str, checker)
	if not inputed:
		xpath_expression = f"//font[{' and '.join(xpath)}]/ancestor::label"
		inputed = fill_input_by_label(element, xpath_expression, input_str, checker)

	return inputed

def automate_contact_form(driver,website_url, info, confirmation_messages):

	# try:

	translate_page(driver, website_url)
	check_for_cookie(driver)
	time.sleep(5)
	iframe_driver = False
	find_contact_us_page(driver)
	check_for_cookie(driver)
	form_element = find_contact_form(driver)
	if not form_element:
		form_element = find_form_in_iframe(driver)
		iframe_driver = True
	time.sleep(5)
	visited = []
	visited.append(fill_the_form(form_element, 'input', ['full', 'name'], info['fullname'], visited))
	visited.append(fill_the_form(form_element, 'input', ['first', 'name'], info['firstname'], visited))
	visited.append(fill_the_form(form_element, 'input', ['last', 'name'], info['lastname'], visited))
	visited.append(fill_the_form(form_element, 'input', ['sur', 'name'], info['lastname'], visited))
	visited.append(fill_the_form(form_element, 'input', ['name'], info['fullname'], visited))

	visited.append(fill_the_form(form_element, 'input', ['mail'], info['email'], visited))
	visited.append(fill_the_form(form_element, 'input', ['compan'], info['company'], visited))

	visited.append(fill_the_form(form_element, 'input', ['phone'], info['phone'], visited))
	visited.append(fill_the_form(form_element, 'input', ["tel"], info['phone'], visited))

	country = fill_the_form(form_element, 'input', ['country'], info['country'], visited)
	if not country:
		visited.append(country)
	else:
		select_options(form_element, 'select', 'country')

	visited.append(fill_the_form(form_element, 'input', ['address'], info['address'], visited))
	visited.append(fill_the_form(form_element, 'input', ['street'], info['street'], visited))
	visited.append(fill_the_form(form_element, 'input', ['city'], info['city'], visited))
	visited.append(fill_the_form(form_element, 'input', ['postcode'], info['postcode'], visited))
	visited.append(fill_the_form(form_element, 'input', ['zip'], info['postcode'], visited))

	visited.append(fill_the_form(form_element, 'input', ['job'], info['job'], visited))

	visited.append(fill_the_form(form_element, 'input', ['subject'], info['message'], visited))
	visited.append(fill_the_form(form_element, 'input', ['regarding'], info['message'], visited))

	select_options(form_element, 'select', 'request')
	select_options(form_element, 'select', 'salutation')
	select_options(form_element, 'select', 'gender')
	select_options(form_element, 'input', 'salutation')

	visited.append(fill_the_form(form_element, 'textarea', ['message'], info['message'], visited))
	visited.append(fill_the_form(form_element, 'textarea', ['inquiry'], info['message'], visited))

	click_on_checkbox(form_element, driver)
	time.sleep(2)
	click_submit(form_element, driver)
	time.sleep(5)
	if iframe_driver:
		driver.switch_to.default_content()
	is_on_page = is_submission_confirmed(driver, confirmation_messages)
	is_alert = check_for_success_alert(driver, confirmation_messages)
	return (is_on_page or is_alert , "Submitted")

	# except Exception as e:
	# 	print(e)
	# 	return (False, e)


# Load the Excel file with website URLs
excel_file_path = 'Websites Sample.xlsx'
df = pd.read_excel(excel_file_path)

with open("contact_information.json", 'r') as f:
	info = json.load(f)


confirmation_messages = [
	"thank you",
	"thanks",
	"contact you soon",
	"was submitted",
	"has been submitted",
	"submitted successfully",
	"was send",
	"has been sent"
]

# Configure the Selenium webdriver
driver = create_driver()

website_url = "http://www.aclas.tw"
message =   "Meeting at "
info["message"] = message
res = automate_contact_form(driver, website_url, info, confirmation_messages)


# df['Status'] = ''
# for i in range(0, len(df)):
# 	website_url = df.loc[i, 'Website']
# 	event = df.loc[i, 'Event']
# 	message =   "Meeting at " + event  if isinstance(event, str) else ""
# 	info["message"] = message
# 	res = automate_contact_form(driver, website_url, info, confirmation_messages)
# 	df.loc[i, 'Status'] = res[0]
# 	df.to_excel('full_test.xlsx', index=False)
# 	print(f"Finished {i}")

