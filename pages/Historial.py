import streamlit as st 
import pandas as pd 
import os
import time
import re
from datetime import datetime, timedelta
from funciones.whatsapp_utils import iniciar_driver, enviar_mensajes, variar_inicio_mensajes, check_respondio, formatear_fecha_hora
from selenium.webdriver.common.by import By 


st.set_page_config(page_title="Seguimiento", layout="wide")
st.title("📁 Seguimiento de envíos de WhatsApp")

# Inicializar estado si no existe
if "whatsapp_abierto" not in st.session_state:
    st.session_state.whatsapp_abierto = False

carpeta_logs = "./enviados"
if not os.path.exists(carpeta_logs):
    st.warning("Aún no has hecho envíos")
    st.stop()
else:
    carpeta_enviados = os.listdir(carpeta_logs)
    archivos = [f for f in carpeta_enviados if f.endswith(".xlsx")]
    if not archivos:
        st.warning("No se encontraron archivos de historial.")
        st.stop()

archivo_seleccionado = st.selectbox("Elegí un historial para revisar si hubo respuestas y hacer seguimiento o para reenviar un mensaje sin tener que volver a cargar el Excel.", sorted(archivos, reverse=True))
ruta_archivo = os.path.join(carpeta_logs, archivo_seleccionado)

df = pd.read_excel(ruta_archivo)

valores_posibles = ["Para revisar", "No respondió", "Sí respondió", "No enviado"]

st.subheader("📊 Estado general de respuestas de esta lista")
conteo = df["Status-Respuesta"].value_counts().reindex(valores_posibles, fill_value=0)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de contactos", len(df.index))
col2.metric("🕓 Para revisar", conteo["Para revisar"])
col3.metric("❌ No respondió", conteo["No respondió"])
col4.metric("✅ Sí respondió", conteo["Sí respondió"])

st.info("Al hacer click en el botón va a revisar si hubo respuesta en todos los contactos que tengan status 'Para revisar' o 'No respondió'")
boton_revisar = st.button("✅ Chequear quién respondió")


def revisar_mensajes():
    st.info("Abriendo WhatsApp Web y chequeando respuestas...")
    driver = iniciar_driver()
    driver.get("https://web.whatsapp.com")
    st.info("Escaneá el QR si es necesario y esperá a que cargue WhatsApp Web")
    time.sleep(15)  # tiempo para escanear QR y cargar

    revisar = df[
      (df["Status-Respuesta"] == "Para revisar") | (df["Status-Respuesta"] == "No respondió")
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

            responded, texto, fecha_hora = check_respondio(driver)
            df.at[i, "Status-Respuesta"] = "Sí respondió" if responded else "No respondió"
            st.write(f"{nombre} {'sí respondió' if responded else 'no respondió'}")
            if responded:
                df.at[i, "Fecha-Última-Respuesta"] = fecha_hora
                df.at[i, "Última-Respuesta"] = texto
        try:
            df.to_excel(ruta_archivo, index=False)
            st.success(f"Archivo sobrescrito: {archivo_seleccionado}")
        except PermissionError:
            st.error("No se pudo guardar el archivo. Asegurate de que no esté abierto en Excel.")

    driver.quit()

if boton_revisar:
    revisar_mensajes()



# --- Reenviar mensajes ---

# st.subheader("📝 Redactá un mensaje para los que todavía no respondieron o elige a quienes querés reenvíar un mensaje")

opciones_destinatarios = ["Todos", "Para revisar", "No respondió", "No respondió hace más de 2 días", "Sí respondió", "No enviado"]


destinatarios_seleccionados = st.selectbox(
    "Vista previa de la lista. Filtrá según el status:",
    opciones_destinatarios
)

if destinatarios_seleccionados:
    if destinatarios_seleccionados == "Todos":
        destinatarios_filtrados = df[["Nombre", "Numero"]]
        df_filtrado_mostrar = df
    elif destinatarios_seleccionados == "No respondió hace más de 2 días":
        if (df["Fecha-Última-Respuesta"] != "---").any():
            fecha_ultima_respuesta = pd.to_datetime(df["Fecha-Última-Respuesta"], dayfirst=True, errors='coerce')
        else:
            fecha_ultima_respuesta = pd.to_datetime(df["Fecha-Último-Envío"], dayfirst=True, errors='coerce')

        hace_2_dias = datetime.now() - timedelta(days=2)
        filtro = (df["Status-Respuesta"] == "No respondió") & (fecha_ultima_respuesta < hace_2_dias)
        destinatarios_filtrados = df.loc[filtro, ["Nombre", "Numero"]]
        df_filtrado_mostrar = df.loc[filtro]
    else:
        filtro = df["Status-Respuesta"] == destinatarios_seleccionados
        destinatarios_filtrados = df.loc[filtro, ["Nombre", "Numero"]]
        df_filtrado_mostrar = df.loc[filtro]

    cantidad = len(destinatarios_filtrados)

    if cantidad > 0:
        st.dataframe(df_filtrado_mostrar)
    else:
        st.warning("No hay destinatarios que cumplan con los criterios seleccionados.")


