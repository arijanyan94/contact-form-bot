import time
import random
import traceback
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

def translate_page(driver, website_url):

	driver.get(website_url)

	# Use JavaScript to get the language from the <html> lang attribute
	lang = driver.execute_script("return document.documentElement.lang;")

	# Check if the page is already in English
	if lang.startswith('en'):
		print(f"Page is already in {lang}.")
	else:
		print(f"Page language is {lang}")
		# Google Translate URL with auto-detection and English as the target language
		google_translate_url = f'https://translate.google.com/translate?hl=en&sl=auto&tl=en&u={website_url}'

		# Navigate to the Google Translate URL which will show the translated website
		driver.get(google_translate_url)

		# The content will now be within an iframe, so you might need to switch to it
		# Look for the iframe id or name in the translated page (it might change over time or be different)
		iframe_id = 'google_translate_iframe'  # This is a placeholder; you'll need to check the correct id or name
		try:
			WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, iframe_id)))
			# Now you can interact with the translated content
		except WebDriverException as e:
			pass
		except Exception as e:
			pass


def find_elements_from_soup(query_element, include_tags, include_attributes_per_tag, exclude_attributes_per_tag):
	
	def match_conditions(tag, element):
		# Check inclusion criteria (case-insensitive substring match)
		for attr, include_values in include_attributes_per_tag.get(tag, {}).items():
			element_attr_value = element.get(attr, '').lower()
			# All include_values must be present in element_attr_value
			if not all(include_value.lower() in element_attr_value for include_value in include_values):
				return False
		# Check exclusion criteria (case-insensitive substring match)
		for attr, exclude_values in exclude_attributes_per_tag.get(tag, {}).items():
			element_attr_value = element.get(attr, '').lower()
			# Any of exclude_values being present means exclusion
			if any(exclude_value.lower() in element_attr_value for exclude_value in exclude_values):
				return False
		return True

	def construct_css_selector(element):
		tag_name = element.name
		class_name = element.get('class')[0] if element.get('class') else None
		element_id = element.get('id')

		selector = tag_name
		if class_name:
			selector += f".{class_name}"
		if element_id:
			selector += f"#{element_id}"


		return selector

	outer_html = query_element.get_attribute('outerHTML')
	soup = BeautifulSoup(outer_html, 'html.parser')    
	result = []
	for tag in include_tags:
		for element in soup.find_all(tag):
			if match_conditions(tag, element):
				css_selector = construct_css_selector(element)
				result.append(css_selector)

	return result

def fill_in_section(element, attribute, inputs, message, visited):
	"""
	Fills in each input section in the contact form.

	Args:
		driver: webdriver object
		attribute: web element attribute name
		section: the contact form section, i.e. name, phone, company, etc
		message: the message to send in the form
	"""
	try:
		res = {'@type': [],
				'@name': [],
				'@class': [],
				'@placeholder': []}
		for i in inputs:
			res['@type'].append(xpath_lower('@type', i))
			res['@name'].append(xpath_lower('@name', i))
			res['@class'].append(xpath_lower('@class', i))
			res['@placeholder'].append(xpath_lower('@placeholder', i))
		xpath_query = f"""//{attribute}[({' and '.join(res['@type'])}) or
										({' and '.join(res['@name'])}) or
										({' and '.join(res['@class'])}) or
										({' and '.join(res['@placeholder'])})]"""

		section_input = element.find_element(By.XPATH, xpath_query)
		if section_input.id in visited:
			return None
		time.sleep(1)
		section_input.send_keys(message)
		time.sleep(random.uniform(1.0, 2.0))
		return section_input.id
	except (NoSuchElementException, ElementNotInteractableException, TimeoutException) as e:
		return None

def filter_contact_forms(forms):

	for form in forms:
		try:
			email_inputs = form.find_element(By.XPATH, f"""//input[{
											to_xpath_converter([('@name', 'email'),
																('@id', 'email'),
																('@class', 'email'),
																('@placeholder', 'email')])}]""")
			text_area = form.find_element(By.XPATH, "//textarea")
			# Email input was found, try to find submit button
			include_tags = ['input', 'button']
			include_attributes_per_tag = {
				'input': {'type': ['submit']},
				'button': {}
			}
			exclude_attributes_per_tag = {}
			submit_buttons = find_elements_from_soup(form, include_tags, include_attributes_per_tag, exclude_attributes_per_tag)
			if len(submit_buttons) == 1:
				return form
		except NoSuchElementException:
			continue
	return None

def find_contact_us_page(driver):
	"""
	Finds the contect form on the webpage using keywords

	Args:
		driver: webdriver object
	"""
	contact_strings = ['contact', 'kontakt', 'kontact', 'get in touch']
	exclude_this = """not(contains(@id, 'css')) and
						not(contains(@type, 'css')) and 
						not(contains(@href, 'css')) and
						not(contains(@id, 'javascript')) and
						not(contains(@type, 'javascript')) and 
						not(contains(@src, 'javascript'))"""
	contact_list = []
	for i in contact_strings:
		xpath_query = f"""//a[({to_xpath_converter([('@href', i),('text()', i)])}) and {exclude_this}] |
						//span[({to_xpath_converter([('@href', i),('text()', i)])}) and {exclude_this}] |
						//button[({to_xpath_converter([('@href', i),('text()', i)])}) and {exclude_this}] |
						//*[(name()!='span' and name()!='button') and 
						({to_xpath_converter([('@href', i),('text()', i)])}) and {exclude_this}]"""

		elements_containing_contact = driver.find_elements(By.XPATH, xpath_query)
		contact_list.extend(elements_containing_contact)
	
	for contact in contact_list:
		try:
			driver.execute_script("arguments[0].scrollIntoView(true);", contact)
			time.sleep(random.uniform(1.0, 2.0))
			driver.execute_script("arguments[0].click();", contact)
			# element_attributes(driver, contact)
			time.sleep(random.uniform(3.0, 4.0))
			return
		except (ElementNotInteractableException,
				StaleElementReferenceException) as e:
			continue
	raise BotException("'Contac us' page was not found")

def find_contact_form(driver):
	# if there is only one post method form, take it

	forms = driver.find_elements(By.XPATH, "//form")
	good_forms = []
	post_forms = []
	for f in range(len(forms)):
		if (forms[f].get_attribute('id') == 'goog-gt-votingForm' or
			'search' in forms[f].get_attribute('id') or
			'search' in forms[f].get_attribute('class')):
			continue
		elif forms[f].get_attribute('method').lower() == 'post':
			post_forms.append(forms[f])	
			good_forms.append(forms[f])
		else:
			good_forms.append(forms[f])
	if not good_forms:
		return None
	if len(post_forms) == 1:
		return post_forms[0]
	if len(good_forms) == 1:
		element_attributes(driver, forms[0])
		return good_forms[0]

	return filter_contact_forms(good_forms)

def find_form_in_iframe(driver):

	form_element = None
	n_iframes = len(driver.find_elements(By.TAG_NAME, "iframe"))

	for index in range(n_iframes):
		# We should find iframes for each index.
		# If we re-use the same list of iframes the elements in it will become
		# stale after each call to driver.switch_to.frame()

		iframes = driver.find_elements(By.TAG_NAME, "iframe")
		iframe = iframes[index]
		try:
			driver.switch_to.frame(iframe)
			form_element = find_contact_form(driver)
			if form_element:
				element_attributes(driver, form_element)
		finally:
			driver.switch_to.default_content()

		if form_element is not None:
			break

	driver.switch_to.default_content()  # just in case

	if form_element is None:
		raise BotException("Contact form was not found")

	return form_element


def create_driver():

	options = Options()
	options.add_argument("--start-maximized")
	driver = webdriver.Chrome(options)

	return driver

def to_xpath_converter(attributes):
	"""
	Adds the attribute and the search string to the
	XPath expresion

	Args:
		attributes: list of 2d tuples

	Returns:
		XPath string expresion
	"""
	xpath_conditions = [
		f"""contains(translate({attribute}, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 
					'abcdefghijklmnopqrstuvwxyz'), '{value.lower()}')"""
		for attribute, value in attributes
	]
	return " or ".join(xpath_conditions)

def xpath_lower(attribute, value):
	res = f"""contains(translate({attribute}, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 
				'abcdefghijklmnopqrstuvwxyz'), '{value.lower()}')"""

	return res

def element_attributes(driver, element):

	script = """
	var items = {}; 
	for (var index = 0; index < arguments[0].attributes.length; ++index) { 
		items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value
	}; 
	return items;
	"""

	# Execute the script to get all attributes
	attributes = driver.execute_script(script, element)

def check_for_captcha(driver):

	try:
		captchas = driver.find_elements(By.XPATH, f"""//input[{
									to_xpath_converter([('@name', 'captcha'),
														('@id', 'captcha'),
														('@class', 'captcha')])}] |
									//img[{to_xpath_converter([('@id', 'captcha'),
																('@alt', 'captcha')])}]""")
		raise BotException("Form is protected with a Captcha")
	except (NoSuchElementException):
		return

def check_for_cookie(driver):
	"""
	Checks for the Cookies pop up on the webpage.
	Tries to Accept Cookies if any.

	Args:
		driver: webdriver object
	"""
	time.sleep(7)
	accept_buttons = driver.find_elements(By.XPATH, f"""//a[
								{to_xpath_converter([('@data-action', 'accept'),
													('text()', 'accept'),
													('@id', 'accept'),
													('@class', 'accept'),
													('@data-action', 'allow'),
													('text()', 'allow'),
													('@id', 'allow'),
													('@class', 'allow')])}] | 
								//button[
								{to_xpath_converter([('@data-action', 'accept'),
													('text()', 'accept'),
													('@id', 'accept'),
													('@class', 'accept'),
													('@data-action', 'allow'),
													('text()', 'allow'),
													('@id', 'allow'),
													('@class', 'allow')])}] |
								//div[
								{to_xpath_converter([('@class', 'button')])} and
								{to_xpath_converter([('@class', 'accept')])}] |
								//a[
								({to_xpath_converter([('@class', 'button')])} and
								{to_xpath_converter([('text()', 'accept')])}) or
								({to_xpath_converter([('@id', 'button')])} and
								{to_xpath_converter([('text()', 'accept')])}) or
								({to_xpath_converter([('@class', 'button')])} and
								{to_xpath_converter([('text()', 'allow')])}) or
								({to_xpath_converter([('@id', 'button')])} and
								{to_xpath_converter([('text()', 'allow')])})]""")
	for accept in accept_buttons:
		try:
			accept.click()
			time.sleep(1)
			print("Cookie pop-up accepted.")
			return
		except (NoSuchElementException, ElementNotInteractableException):
			continue
	print("No cookie pop-up found or error in accepting cookies.")
