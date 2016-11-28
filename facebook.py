__author__ = 'benjamin'

import fxxxbxxk

# start simple browser
browser = fxxxbxxk.FxxxbxxkBrowser()
# a really simple edit.
with open('config.txt', 'r') as file:
    config = file.readline().split(',')
    browser.login(config[0], config[1])

browser.run()