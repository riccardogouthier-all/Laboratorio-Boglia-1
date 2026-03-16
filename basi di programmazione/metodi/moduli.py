import requests

url = 'https://pokeapi.co/api/v2/pokemon/'


risposta = requests.get(url + 'pikachu')

print(risposta.status_code)