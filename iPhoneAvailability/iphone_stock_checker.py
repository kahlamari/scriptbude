#!/usr/bin/python

'''iPhone Availability Checker
This tiny script checks if certain iPhone models are available for pickup in the
Apple stores of your choice (as long as they are in the same country). If the
models of your choice are available the script will send you an email. By
setting up a cronjob, you can be immediately alerted once the iPhone is
available.

You will need to customize the script to your needs. I.e. county, iPhone model,
store etc.
'''

import requests
import json
import smtplib

#######################
# Begin customization #
#######################

# The country of the Apple store you are looking to pickup the phone from.
country = 'UK'

# The IDs of the Apple stores you are looking to pickup the phone from.
# You can find the ID of the Apple store by viewing the source of the store
# homepage. In the meta-tag you'll see the ID starting with R.
stores = ['R245', # Covent Garden
          'R092', # Regent Street
          'R369'
          ]

# Finding the ID of the model you are looking for is a bit harder. Apple has
# different IDs for each model in each country. So doublecheck that you have
# picked the correct ID.
models = ['MN4P2B/A', # iPhone 7+ Silver 128 GB (UK)
          'MN5F2LL/A', # iPhone 7+ JetBlack 256 GB (US-AT&T)
          'MN912VC/A',
          'MN972VC/A']

# Add here the email addresses that you want to inform about the availablility.
receipients = ['some@email.me']

# Your gmail address. The availability notification will be send from this
# account.
sender = 'some@gmail.com'

# The password of the gmail account.
sender_passwd = ''

#####################
# End customization #
#####################
country_codes = {'AE': ['AE', 'en_AE'],
                 'AU': ['AU', 'en_AU'],
                 'CA': ['CA', 'en_CA'],
                 'CH': ['CH', 'de_CH'],
                 'CN': ['CN', 'en_CN'],
                 'DE': ['DE', 'de_DE'],
                 'ES': ['ES', 'es_ES'],
                 'FR': ['FR', 'fr_FR'],
                 'IT': ['IT', 'it_IT'],
                 'JP': ['JP', 'jp_JP'],
                 'SE': ['SE', 'se_SE'],
                 'TR': ['TR', 'tr_TR'],
                 'UK': ['GB', 'en_GB'],
                 'US': ['US', 'en_US']}

url = 'https://reserve.cdn-apple.com/{0}/{1}/reserve/iPhone/availability.json'

def getCurrentStockData():
  '''Loads Apple's current iPhone stock.

  Returns:
      A dict with the choosen stores and with these stores' current stock. For
      example:

      {'R245': {}, 'R369': {'MN912VC/A': 'ALL'}, 'R092': {}}
  '''
  response = requests.get(url.format(country_codes[country][0],
                                     country_codes[country][1]))

  stock_unfiltered = response.json()
  stock = {}

  # filtering the stock to stores of interest
  for store in stores:
    phones = {}
    if store in stock_unfiltered:
      # and models of interest
      for model in models:
        if model in stock_unfiltered[store]:
          phones[model] = stock_unfiltered[store][model]

    stock[store] = phones

  print(stock)
  return stock

def loadPreviousStockData():
  try:
    with open('previous_state.temp') as data_file:
      previous_stock = json.load(data_file)
  except:
    previous_stock = {}

  return previous_stock

def saveCurrentStockData(stock):
  # save results to file
  with open('previous_state.temp', 'w') as data_file:
    json.dump(stock, data_file)

def checkForNewAvailabilities(stock, previous_stock):
  '''Identifies if new stock has become available.

  Takes current and previous stock and returns a dictionary will all newly
  available stock.

  Args:
      stock: the current stock of the stores.
      previous_stock: the stock of the previous run.

  Returns:
      A dict of newly available stock. Example:

      {'R369': {'MN912VC/A': 'ALL'}}
  '''
  available_stock = {}

  for store in stock:
    for model in stock[store]:
      # Apple uses different codes for available, e.g. "ALL" or "UNLOCKED"
      if stock[store][model] != 'NONE':
        print(stock[store][model])
        if store not in previous_stock or model not in previous_stock[store]:
          if store in available_stock:
            available_stock[store].update({model: 'ALL'})
          else:
            available_stock[store] = {model: 'ALL'}
        elif previous_stock[store][model] == 'NONE':
          if store in available_stock:
            available_stock[store].update({model: 'ALL'})
          else:
            available_stock[store] = {model: 'ALL'}

  print(available_stock)
  return available_stock

def sendMail(sender, password, receipients, stock):
  '''Formats and sends the mail when new stock is available.

  Args:
      sender: gmail account used to send email.
      password: gmail account's password. Might be a application specific.
      receipients: email addresses of to whom to send the email.
      stock: dict of stores with available iphones.
  '''
  msg = ''
  for store in stock:
    for model in stock[store]:
      msg += '* ' + model + ' in ' + store + '\r\n'

  msg = 'Hi, new iPhones available' + '\r\n' + msg

  server = smtplib.SMTP('smtp.gmail.com:587')
  server.ehlo()
  server.starttls()
  server.login(sender,password)
  server.sendmail(sender, receipients, msg)
  server.quit()

stock = getCurrentStockData()
p_stock = loadPreviousStockData()

new_stock = checkForNewAvailabilities(stock, p_stock)
if len(new_stock) > 0:
  sendMail(sender, sender_passwd, receipients, new_stock)
saveCurrentStockData(stock)
