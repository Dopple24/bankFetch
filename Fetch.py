import requests

x = requests.get('https://fioapi.fio.cz/v1/rest/last/MY177IQdqygGXpSqschQMIdcVx9DVCOdeLY59qUL9mTVJfhz1cMx8rcx7E16DoUe/transactions.json')

print(x.text)