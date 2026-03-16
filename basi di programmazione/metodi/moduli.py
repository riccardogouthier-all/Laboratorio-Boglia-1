import requests

url = 'https://pokeapi.co/api/v2/pokemon/'


risposta = requests.get(url + 'pichu')


if risposta.status_code == 200:
    pokemon = risposta.json()
    print(type(pokemon))


    for chiave, valore in pokemon.items():
        print(f"{chiave}, {valore}")
        print("----------------------------------------------------")

