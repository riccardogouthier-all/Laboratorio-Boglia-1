# print(__name__)


def addizione(a:int, b:int):
    return a+b

def main():
    print("sono il metodo main del modulo1")
    print(addizione(4,5))


if __name__=="__main__":
    main()