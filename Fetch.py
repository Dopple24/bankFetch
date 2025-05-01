import requests

x = requests.get('https://fioapi.fio.cz/v1/rest/last//transactions.json')

print(x.text)