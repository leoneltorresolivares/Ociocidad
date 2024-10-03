import pyautogui as py, webbrowser as web
from time import sleep

# telefono = input("Ingresar numero telefono (con el codigo del pais): ")

# 56990555027, Isidora

# 56948999959, Francisca

web.open("https://web.whatsapp.com/send?phone=56948999959")

sleep(10)

for i in range(100):
    py.write("La vida de un critico es dificil en muchos aspectos\n"
                 "Arriesgamos mucho y no tenemos control en las desiciones o futuros ajenos")
    py.press("enter")