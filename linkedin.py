# -*- coding: utf-8 -*-
"""
Simple Linkedin crawler to collect user's  profile data.

@author: idwaker

To use this you need linkedin account, all search is done through your account

Requirements:
    python-selenium
    python-click
    python-keyring

Tested on Python 3 not sure how Python 2 behaves
"""

import sys
import csv
import time
import click
import getpass
import keyring
from contextlib import contextmanager
from selenium import webdriver
from selenium.common.exceptions import (WebDriverException,
                                        NoSuchElementException)


LINKEDIN_URL = 'https://www.linkedin.com'


class UnknownUserException(Exception):
    pass


class UnknownBrowserException(Exception):
    pass


@contextmanager
def bus(browser):
    """
    XXX: check if it is correct way to it
    """
    driver = None
    try:
        if browser.lower() == 'firefox':
            driver = webdriver.Firefox()
        elif browser.lower() == 'chrome':
            driver = webdriver.Chrome()
        elif browser.lower() == 'phantomjs':
            driver = webdriver.PhantomJS()
        else:
            driver = webdriver.Remote(browser)
        yield driver
    except (FileNotFoundError, WebDriverException):
        click.echo("Please install selected browser first or use either Firefox, PhantomJS or Chrome")
        yield driver
    finally:
        if driver:
            driver.close()


def get_password(username):
    """
    get password from stored keychain service
    """
    password = keyring.get_password('linkedinpy', username)
    if not password:
        raise UnknownUserException("""You need to store password for this user
                                        first.""")

    return password


def login_into_linkedin(driver, username):
    """
    Just login to linkedin if it is not already loggedin
    """
    userfield = driver.find_element_by_id('login-email')
    passfield = driver.find_element_by_id('login-password')

    submit_xpath = '//form[@class="login-form"]/input[@name="submit"]'

    password = get_password(username)

    # If we have login page we get these fields
    # I know it's a hack but it works
    if userfield and passfield:
        userfield.send_keys(username)
        passfield.send_keys(password)
        submit = driver.find_element_by_xpath(submit_xpath)
        submit.click()


def collect_names(filepath):
    """
    collect names from the file given
    """
    names = []
    with open(filepath, 'r') as _file:
        names = [line.strip() for line in _file.readlines()]
    return names


@click.group()
def cli():
    """
    First store password

    $ python linkedin store username@example.com
    Password: **

    Then crawl linkedin for users

    $ python linkedin crawl username@example.com with_names output.csv --browser=firefox
    """
    pass


@click.command()
@click.option('--browser', default='phantomjs', help='Browser to run with')
@click.argument('username')
@click.argument('infile')
@click.argument('outfile')
def crawl(browser, username, infile, outfile):
    """
    Run this crawler with specified username
    """

    # first check and read the input file
    all_names = collect_names(infile)

    fieldnames = ['fullname', 'locality', 'industry', 'current summary',
                  'past summary', 'education', ]
    # then check we can write the output file
    # we don't want to complete process and show error about not
    # able to write outputs
    with open(outfile, 'w') as csvfile:
        # just write headers now
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    search_btn = '//form[@id="global-search"]//button[@class="search-button"]'
    link_title = './/a[@class="title main-headline"]'

    # now open the browser
    with bus(browser) as driver:
        if not driver:
            return

        driver.get(LINKEDIN_URL)

        login_into_linkedin(driver, username)

        for name in all_names:
            search_input = driver.find_element_by_id('main-search-box')
            search_input.send_keys(name)

            search_button = bus.driver.find_element_by_xpath(search_btn)
            search_button.click()

            profiles = []

            # collect all the profile links
            results = driver.find_element_by_id('results-container')
            links = results.find_elements_by_xpath(link_title)

            # get all the links before going through each page
            links = [link.get_attribute('href') for link in links]
            for link in links:
                # XXX: This whole section should be separated from this method
                # XXX: move try-except to context managers
                driver.get(link)

                overview = None
                overview_xpath = '//div[@class="profile-overview-content"]'
                try:
                    overview = driver.find_element_by_xpath(overview_xpath)
                except NoSuchElementException:
                    click.echo("No overview section skipping this user")
                    continue

                # every xpath below here are relative
                fullname = None
                fullname_xpath = './/span[@class="full-name"]'
                try:
                    fullname = overview.find_element_by_xpath(fullname_xpath)
                except NoSuchElementException:
                    # we store empty fullname : notsure for this
                    fullname = ''
                else:
                    fullname = fullname.text.strip()

                locality = None
                try:
                    locality = overview.find_element_by_class_name('locality')
                except NoSuchElementException:
                    locality = ''
                else:
                    locality = locality.text.strip()

                industry = None
                try:
                    industry = overview.find_element_by_class_name('industry')
                except NoSuchElementException:
                    industry = ''
                else:
                    industry = industry.text.strip()

                current_summary = None
                csummary_xpath = './/tr[@id="overview-summary-current"]/td'
                try:
                    current_summary = overview.find_element_by_xpath(csummary_xpath)
                except NoSuchElementException:
                    current_summary = ''
                else:
                    current_summary = current_summary.text.strip()

                past_summary = None
                psummary_xpath = './/tr[@id="overview-summary-past"]/td'
                try:
                    past_summary = overview.find_element_by_xpath(psummary_xpath)
                except NoSuchElementException:
                    past_summary = ''
                else:
                    past_summary = past_summary.text.strip()

                education = None
                education_xpath = './/tr[@id="overview-summary-education"]/td'
                try:
                    education = overview.find_element_by_xpath(education_xpath)
                except NoSuchElementException:
                    education = ''
                else:
                    education = education.text.strip()

                data = {
                    'fullname': fullname,
                    'locality': locality,
                    'industry': industry,
                    'current summary': current_summary,
                    'past summary': past_summary,
                    'education': education,
                }
                profiles.append(data)

            with open(outfile, 'a+') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerows(profiles)


@click.command()
@click.argument('username')
def store(username):
    """
    Store given password for this username to keystore
    """
    passwd = getpass.getpass()
    keyring.set_password('linkedinpy', username, passwd)
    click.echo("Password updated successfully")


cli.add_command(crawl)
cli.add_command(store)


if __name__ == '__main__':
    cli()
