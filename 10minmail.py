#!/usr/bin/env pipenv-shebang

from io import BytesIO
from python_anticaptcha import AnticaptchaClient, ImageToTextTask
from websocket import create_connection
from PIL import Image
import mechanicalsoup
import os
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

file_object = open(os.path.expanduser("~/.ssh/anti_captcha.key"), "r")
api_key = file_object.readline().strip()
file_object.close()

class mailbox(object):
    """10 minute mailbox"""
    def __init__(self):
        super(mailbox, self).__init__()
        self.ws = create_connection("wss://dropmail.me/websocket")
        self.next = self.ws.recv
        self.close = self.ws.close
        self.email = self.next()[1:].split(":")[0]
        self.next()

def run(box):
    # stdlib
    # for box in boxes:
    # print("waiting for " + box.email)
    result = box.next()
    return "https" + result.split('https')[1].split('\\r\\n\\r\\n","subject"')[0]

def solve_captcha_manual(image_data):
    img = Image.open(image_data)
    img.show()

    ans =  input("What is the captcha?\n")
    os.system("killall display")

    return ans

def solve_captcha(image_data):
    client = AnticaptchaClient(api_key)
    task = ImageToTextTask(image_data)
    job = client.createTask(task)
    job.join()
    return job.get_captcha_text()

def firstPage(browser, email, retries=3):
    if retries==0:
        print("Failed")
        return None
    url = "https://duwo.multiposs.nl/login/submit.php?Request=SignUp"
    response = browser.open(url, verify=False)

    url = "https://duwo.multiposs.nl" + browser.get_current_page().find('div', {'id': 'captcha_container_1'}).find('img')['src']

    response = browser.open(url, verify=False)
    image_data = BytesIO(response.content)
    answer = solve_captcha(image_data)

    url = "https://duwo.multiposs.nl/login/submit.php?Request=SignUp"
    response = browser.open(url, verify=False)

    form = browser.select_form('form#FormSendMail')
    form['recoveradress'] = email
    form['captcha_code'] = answer.strip()
    #TODO: this submit is incorrect and blocks the ip
    print(form)
    print("TODO: this submit is incorrect and blocks the ip")
    exit()
    browser.submit_selected()

    if("Enter" in browser.get_current_page().find('div', {'id': 'MainLogin'}).
            find('div', {'id': 'LoginBoxInner'}).find('p').text):
        firstPage(browser, email, retries-1)

    return answer


def secondPage(browser, link, email, location):
    browser.open(link, verify=False)

    form = browser.select_form('form#FormLoginInfo')
    form['SaveUserLocationID'] = location
    form['InputLocation'] = location
    form['SaveUser'] = email
    form['SavePwd'] = "c129b324aee662b04eccf68babba85851346dff9"
    # browser.get_current_form().print_summary()

    browser.submit_selected()

    # print(browser.get_current_page())

def create_account(location='FF-1024'):
    box = mailbox()
    browser = mechanicalsoup.StatefulBrowser()  # Generate fresh browser
    # print(location + ", " + box.email)

    ans = firstPage(browser, box.email)  # Show capcha to user and generate email
    if ans is None:
        box.close()
        return None
    link = run(box)  # Wait for email and return link
    # print(link)
    secondPage(browser, link, box.email, location)  # Process link to finish registration

    box.close()

    os.system("echo " + box.email + " >> accounts2.txt")

    return box.email

def create_one_of_each():
    amount = 1000
    boxes = list()
    count = 1

    file_object = open("codes.txt", "r")
    for line in file_object:
        print(count)
        count = count + 1
        amount = amount - 1

        location = line.strip()
        email = create_account()

        if amount == 0:
            break

    file_object.close()
    # run(boxes)

if __name__ == '__main__':
    print(create_account())

