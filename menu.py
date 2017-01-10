__author__ = 'marcel'

import imaplib
import email
import tempfile, xlrd
import keyring

def getAttachmentsInEmail(mail):
    if mail.get_content_maintype() != 'multipart':
        return
    for part in mail.walk():
        if part.get_filename() is not None:
            return part.get_payload(decode=True)


user = 'mervinnmightystaff'

# set password with python -c 'import keyring; keyring.set_password("metro-email", "mervinnmightystaff", "*******")'
password = keyring.get_password('metro-email', user)

server = imaplib.IMAP4_SSL('imap.gmail.com')
server.login('%s' % user, password)
server.select('[Gmail]/All Mail')
resp, items = server.search(None, '(FROM "restaurant.062@metro-cc.de")')

messages = items[0].split()

mail = reversed(messages).next()
resp, data = server.fetch(mail, '(RFC822)')

filename = tempfile.mkstemp(suffix=".xlsx")[1]
file = open(filename, 'r+')
msg = email.message_from_string(data[0][1])
file.write(getAttachmentsInEmail(msg))
file.close()

book = xlrd.open_workbook(filename,formatting_info=True)
sheet = book.sheet_by_index(1)

lines = reduce(lambda r, v: (len(r) != 0 and r[-1].value == v.value) and r or r + [v], sheet.col_slice(1,9,40), [])
# lines = reduce(lambda r, v: (len(r) == 0 or r[-1].value == "") and r or r + [v], lines, [])

import json
menu = []
item = {}
item['description'] = []
for row in filter(lambda x: "Zusatz" not in x.value, lines):
    font_height = book.font_list[book.xf_list[row.xf_index].font_index].height

    if row.value != "":
        if font_height == 220:
           item['preamble'] = row.value
        if font_height == 480:
            item['title'] = row.value
        if font_height == 320 or font_height == 280:
            item['description'].append(row.value)
    elif row.value == "" and 'title' in item:
        menu.append(item)
        item = {}
        item['description'] = []

from jinja2 import Environment, PackageLoader, select_autoescape
env = Environment(loader=PackageLoader('menu', 'templates'),autoescape=select_autoescape(['html', 'xml']))
template = env.get_template('template.html')
from dateutil.parser import parse
date = parse(msg['Date'])
print template.render({ "menu": menu, "date": date.strftime('%A, %B %d') }).encode( "utf-8" )
