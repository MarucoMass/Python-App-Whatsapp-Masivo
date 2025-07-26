import os
import time
import random
from datetime import datetime
import urllib.parse
import pandas as pd
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def iniciar_driver():
    profile_path = os.path.abspath("perfil_whatsapp")
    options = webdriver.ChromeOptions()
    options.add_argument(f'--user-data-dir={profile_path}')
    options.add_argument("--profile-directory=Default")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://web.whatsapp.com")
    return driver

def variar_inicio_mensajes(nombre: str) -> str:
    opciones = [
        f"Hola {nombre}, cómo estás?",
        f"Hola! Cómo estás {nombre}?, gusto en saludarte.",
        f"Hola {nombre}, ¿qué tal?",
        f"Hola {nombre}!, ¿todo bien?",
    ]
    return random.choice(opciones)

def normalizar_numero(num: str, CODIGO_PAIS="54") -> str:
    if num.startswith(CODIGO_PAIS):
        return f"+{num}"
    elif num.startswith("0" + CODIGO_PAIS):
        return f"+{num[1:]}"
    elif num.startswith("0"):
        return f"+{CODIGO_PAIS}{num[1:]}"
    elif num.startswith("15") or len(num) <= 10:
        return f"+{CODIGO_PAIS}{num}"
    else:
        return f"+{CODIGO_PAIS}{num}"

def enviar_mensajes(driver, nombre, numero, mensaje_cuerpo):
    try:
        mensaje = variar_inicio_mensajes(nombre) + " " + mensaje_cuerpo
        mensaje_url = urllib.parse.quote(mensaje)
        url = f"https://web.whatsapp.com/send?phone={numero}&text={mensaje_url}"
        st.write(f"📨 Enviando a {nombre} ({numero})...")
        driver.get(url)
        time.sleep(10)

        try:
            boton = driver.find_element(By.XPATH, '//button[@aria-label="Enviar"]')
            boton.click()
            estado = "✅ Enviado"
            st.success(f"{nombre}: Mensaje enviado.")
        except Exception as e:
            estado = f"❌ Error al hacer clic: {e}"
            st.error(f"{nombre}: Error al enviar.")

        time.sleep(random.randint(8, 20))
    except Exception as e:
        estado = f"❌ Error general: {e}"
        st.error(f"{nombre}: Error al enviar.")

    return estado  


