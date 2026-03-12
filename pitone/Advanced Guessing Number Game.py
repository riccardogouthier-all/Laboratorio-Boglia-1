import tkinter as tk
from tkinter import messagebox
import  random

# Variabili globali
sec = random.randint(1, 100)
tentativi = 0

# Funzione controllo
def controllo():
    global tentativi

    try:
        guess = int(entry.get())



def nuova_partita():
    global sec, tentativi
    sec = random.randint(1, 100)
    tentativi = 0
    label_feedback.config(text="")
    label_tentativi.config("Tentativi: 0")
    entry.delete(0, tk.END)

# GUI
root = tk.Tk()
root.title("Guessing Game base")
root.geometry("300x200")

label_title = tk.Label(root, text="Indovina il numero (1-100)")
label_title.pack(pady=10)

entry = tk.Entry(root)
entry.pack()

btn = tk.Button(root, text="Indovina", command=controlla)