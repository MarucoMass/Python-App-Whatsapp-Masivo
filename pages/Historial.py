import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from funciones.whatsapp_utils import iniciar_driver, enviar_mensajes
from selenium.webdriver.common.by import By

st.set_page_config(page_title="Historial", layout="wide")
st.title("📁 Historial de envíos de WhatsApp")

carpeta_logs = "enviados"
archivos = [f for f in os.listdir(carpeta_logs) if f.endswith(".xlsx")]

if not archivos:
    st.warning("No se encontraron archivos de historial.")
    st.stop()

archivo_seleccionado = st.selectbox("Elegí un historial para revisar si hubo respuestas y hacer seguimiento o para reenviar un mensaje sin tener que volver a cargar el Excel.", sorted(archivos, reverse=True))
ruta_archivo = os.path.join(carpeta_logs, archivo_seleccionado)

df = pd.read_excel(ruta_archivo)
st.subheader("Vista previa del historial")
st.dataframe(df)

# fallidos = df[~df["Estado"].str.contains("Enviado", na=False)]
# st.markdown(f"📌 Contactos fallidos encontrados: **{len(fallidos)}**")


# if st.button("🔁 Reenviar mensajes a los que no respondieron"):
#     if mensaje.strip() == "":
#         st.warning("Escribí un mensaje para reenviar.")
#     else:
#         st.info("Iniciando WhatsApp Web...")
#         driver = iniciar_driver()
#         df_resultado, nuevo_archivo = enviar_mensajes(driver, fallidos, mensaje)
#         st.success(f"Mensajes reenviados. Guardado como {nuevo_archivo}")
#         st.dataframe(df_resultado)

# --- NUEVO: Chequear respuestas ---

def check_respondio(driver):
    time.sleep(5)  # esperar que carguen mensajes
    mensajes_recibidos = driver.find_elements(By.CSS_SELECTOR, "div.message-in")
    return len(mensajes_recibidos) > 0

if st.button("✅ Chequear quién respondió"):
    st.info("Abriendo WhatsApp Web y chequeando respuestas...")
    driver = iniciar_driver()
    driver.get("https://web.whatsapp.com")
    st.info("Escaneá el QR si es necesario y esperá a que cargue WhatsApp Web")
    time.sleep(15)  # tiempo para escanear QR y cargar

    revisar = df[
        (df["Respondió"].astype(str).str.lower() == "revisar") 
        # | (df["Respondió"].astype(str).str.lower() == "no")
    ]

    if revisar.empty:
        st.info("No hay contactos pendientes para revisar.")
    else:
        for i, row in revisar.iterrows():
            numero = row["Numero"]
            nombre = row["Nombre"]
            url = f"https://web.whatsapp.com/send?phone={numero}"
            driver.get(url)
            st.write(f"Chequeando respuestas de {nombre}...")
            time.sleep(8)

            responded = check_respondio(driver)
            df.at[i, "Respondió"] = "Sí" if responded else "No"
            st.write(f"{nombre} respondió: {'Sí' if responded else 'No'}")
            if responded:
                df.at[i, "Fecha-Última-Respuesta"] = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Guardar todo al final
        df.to_excel(ruta_archivo, index=False)
        st.success(f"Archivo sobrescrito: {archivo_seleccionado}")
        st.dataframe(df)

    driver.quit()

st.subheader("Redactá un mensaje para los que todavía no respondieron o elige a quienes querés reenvíar un mensaje")
st.info("Primero elegí un historial del selector. Después podés enviar mensaje masivamente a todos los que no respondieron, o podés elegir vos a mano marcando los respectivos casilleros.")
mensaje = st.text_area(
            "✉️ Escribí el mensaje para enviar. El `Hola {nombre}, cómo éstas? (por ejemplo),` se agrega automáticamente.",
            height=200,
            placeholder="En seguimiento de mi mensaje anterior..."
        )