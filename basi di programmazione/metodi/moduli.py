import requests

# url = 'https://pokeapi.co/api/v2/pokemon/'
url = 'https://api.tvmaze.com/singlesearch/shows?q='



cerca = input("Scrivi il titolo di tv-show: ")
risposta = requests.get(url + cerca)

if risposta.status_code == 200:
    show = risposta.json()

    titolo = show.get('name')
    rating = show.get('rating')
    img = show.get('image')
    # print(type(show))
    print(titolo, rating['average'], img['medium'])
    
# if risposta.status_code == 200:
#     pokemon = risposta.json()
#     print(type(pokemon))


#     for chiave, valore in pokemon.items():
#         print(f"{chiave}, {valore}")
#         print("----------------------------------------------------")

