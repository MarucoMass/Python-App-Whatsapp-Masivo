from datetime import datetime
import streamlit as st
import pandas as pd
import random
import time
import urllib.parse
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ------------- Funciones -------------

def variar_inicio_mensajes(nombre: str) -> str:
    opciones = [
        f"Hola {nombre}, cómo estás?",
        f"Hola! Cómo estás {nombre}?, gusto en saludarte.",
        f"Hola {nombre}, ¿qué tal?",
        f"Hola {nombre}!, ¿todo bien?",
    ]
    return random.choice(opciones)

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

# ------------- Streamlit -------------

st.set_page_config(page_title="Envío masivo de WhatsApp", page_icon="💬")
st.title("📲 Envío masivo de WhatsApp")
st.markdown("Subí un Excel con columnas **Nombre** y **Numero**, y escribí el cuerpo del mensaje.")

archivo = st.file_uploader("Subí tu Excel", type=["xlsx"])

# Inicializar estado si no existe
if "whatsapp_abierto" not in st.session_state:
    st.session_state.whatsapp_abierto = False

if archivo:
    df = pd.read_excel(archivo)

    if "Nombre" in df.columns and "Numero" in df.columns:
        contactos = df[["Nombre", "Numero"]].copy()

        # Limpieza de números
        contactos["Numero"] = contactos["Numero"].astype(str).apply(lambda x: "".join(filter(str.isdigit, x)))
        contactos["Numero"] = contactos["Numero"].apply(normalizar_numero)

        st.success(f"✅ Se cargaron {len(contactos)} contactos.")
        # st.dataframe(contactos)

        nombre_lista = st.text_area(
            "✔ Ponle un nombre a la lista. Cuando termines de enviar se guarda un excel con el status de los mensajes en una carpeta llamada 'Enviados'",
            height=100,
            placeholder="Ejemplo: Lista de 2da aula abierta YPP"
        )
        
        mensaje_base = st.text_area(
            "✉️ Escribí el cuerpo del mensaje. El `Hola {nombre}, cómo éstas? (por ejemplo),` se agrega automáticamente.",
            height=200,
            placeholder="Te escribimos desde la fundación para recordarte..."
        )

        if st.button("👀 Mostrar vista previa"):
            if not mensaje_base.strip():
                st.warning("Por favor, escribí el cuerpo del mensaje.")
            else:
                nombre = contactos["Nombre"][0]
                saludo = variar_inicio_mensajes(nombre)
                mensaje = saludo + " " + mensaje_base
                st.write(f"Ejemplo para {nombre}:")
                st.info(mensaje)

        # Botón para abrir/cerrar WhatsApp Web
        if not st.session_state.whatsapp_abierto:
            if st.button("🚀 Iniciar WhatsApp Web"):
                driver = iniciar_driver()
                st.session_state.driver = driver
                st.session_state.contactos = contactos
                st.session_state.mensaje_cuerpo = mensaje_base
                st.session_state.nombre_lista = nombre_lista
                st.session_state.whatsapp_abierto = True
                st.success("WhatsApp Web abierto. Escaneá el QR si es la primera vez.")
        else:
            st.info("✅ WhatsApp Web está abierto.")
            if st.button("❌ Cerrar WhatsApp Web"):
                try:
                    st.session_state.driver.quit()
                except Exception:
                    pass
                st.session_state.whatsapp_abierto = False
                del st.session_state.driver
                st.success("WhatsApp Web cerrado.")

        # Botón para enviar mensajes
        if "driver" in st.session_state and st.session_state.whatsapp_abierto and st.button("📤 Enviar los mensajes"):
            driver = st.session_state.driver
            contactos = st.session_state.contactos
            mensaje_cuerpo = st.session_state.mensaje_cuerpo
            historial = []

            for index, row in contactos.iterrows():
                nombre = str(row["Nombre"])
                numero = str(row["Numero"])
                mensaje = variar_inicio_mensajes(nombre) + " " + mensaje_cuerpo
                mensaje_url = urllib.parse.quote(mensaje)
                url = f"https://web.whatsapp.com/send?phone={numero}&text={mensaje_url}"

                ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                st.write(f"📨 Enviando a {nombre} ({numero})...")
                driver.get(url)
                time.sleep(10)

                try:
                    boton = driver.find_element(By.XPATH, '//button[@aria-label="Enviar"]')
                    boton.click()
                    estado = "✅ Enviado"
                    st.success(f"{nombre}: Mensaje enviado.")
                except Exception as e:
                    print(e)
                    estado = f"❌ Error: {e}"
                    st.error(f"{nombre}: Error al enviar.")

                historial.append({
                    "Nombre": nombre,
                    "Numero": numero,
                    "Fecha": ahora,
                    "Estado": estado
                })

                time.sleep(random.randint(8, 20))

            st.session_state.whatsapp_abierto = False
            driver.quit()

            folder_path = "./Enviados"
            os.makedirs(folder_path, exist_ok=True)

            df_log = pd.DataFrame(historial)

            nombre_archivo = nombre_lista + "-" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            archivo_log = os.path.join(folder_path, f"{nombre_archivo}.xlsx")

            df_log.to_excel(archivo_log, index=False)

            with open(archivo_log, "rb") as f:
                st.download_button("⬇️ Descargar registro de envíos", f, file_name=f"{nombre_archivo}.xlsx")

    else:
        st.error("❌ El Excel no tiene las columnas 'Nombre' o 'Numero'")
