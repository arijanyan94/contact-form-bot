# "Contact us" form Submission bot

## Introduction
A web crawler bot which tries to submit the contact form on each website given.
It first opens the website, Accept the **Cookies** pop up, if any, goes to the **Contact Us** page 
in the website, tries to find the **Contact form**, fills in the information and submits.
The bot reads the infomration for the form filling from the **contact_information.json** file.
If you want the fill the form with your information, just change it from that file, keeping tha same format.

## Instalation
Clone the repo, create and activate the virtual environment and run

		pip install -r requirements.txt

## Usage
After the installations you can run the following command to start the bot

		python web_bot.py

It reads the **Websites Sample.xlsx** file, which is in the same folder, loops over each website
in the "Website" column and writes the result in **full_test.xlsx** file.
To stop the application, termiante the program with **CTRL + C** .
You can see the previous results of the test in the "full_test.xlsx" file.

## Citation
Author - Arsen Arijanyan

Email  - arsen.aridjanyan@gmail.com
