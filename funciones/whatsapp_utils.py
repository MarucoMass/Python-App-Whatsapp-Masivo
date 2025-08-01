import os
import time
import random
import urllib.parse
import streamlit as st
import re
from datetime import datetime
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
        f"Hola! Cómo estás {nombre}? Gusto en saludarte.",
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

def enviar_mensajes(driver, nombre, numero, mensaje_cuerpo, index, lista):
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
            estado = True
            st.success(f"{nombre}: Mensaje enviado.")
        except Exception as e:
            estado = False
            st.error(f"{nombre}: Error al enviar.")

        if index != (len(lista)-1):
            st.info(f"Pasando a siguiente envío. Queda/n {(len(lista))-(index+1)} envío/s")
            time.sleep(random.randint(8, 20))

    except Exception as e:
        estado = False
        st.error(f"{nombre}: Error al enviar: {e}.")

    return estado  


def check_respondio(driver):
    time.sleep(5)
    mensajes = driver.find_elements(By.CSS_SELECTOR, "div[class*='message-']")

    index_ultimo_out = -1

    for i, mensaje in enumerate(mensajes):
        clases = mensaje.get_attribute("class")
        if "message-out" in clases:
            index_ultimo_out = i

    if index_ultimo_out == -1:
        return False, "", ""

    respuestas = []
    fecha_hora = ""

    for mensaje in mensajes[index_ultimo_out + 1:]:
        clases = mensaje.get_attribute("class")
        if "message-in" in clases:
            texto_completo = mensaje.text.strip()
            if texto_completo:
                respuestas.append(texto_completo)
                try:
                    elem_fecha = mensaje.find_element(By.CSS_SELECTOR, "div.copyable-text")
                    fecha_raw = elem_fecha.get_attribute("data-pre-plain-text")
                    if fecha_raw:
                        match = re.search(r'\[(.*?)\]', fecha_raw)
                        if match:
                            fecha_hora = formatear_fecha_hora(match.group(1))  # Actualiza siempre, guarda la última
                except:
                    pass

    if respuestas:
        texto = "\n".join(respuestas)
        return True, texto, fecha_hora
    else:
        return False, "", ""


def formatear_fecha_hora(fecha_hora_str):
    try:
        # formato esperado: "2:47, 27/7/2025"
        partes = fecha_hora_str.split(",")
        if len(partes) == 2:
            hora = partes[0].strip()
            fecha = partes[1].strip()
            dt = datetime.strptime(f"{hora} {fecha}", "%H:%M %d/%m/%Y")
            return dt.strftime("%d/%m/%Y %H:%M")
    except Exception as e:
        print("Error al formatear fecha_hora:", e)
    return fecha_hora_str