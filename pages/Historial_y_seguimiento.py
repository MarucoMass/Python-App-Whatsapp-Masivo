import streamlit as st
import pandas as pd
import os
import time
import random
import re
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from funciones.whatsapp_utils import iniciar_driver, enviar_mensajes, variar_inicio_mensajes
from selenium.webdriver.common.by import By


st.set_page_config(page_title="Historial", layout="wide")
st.title("📁 Historial de envíos de WhatsApp")

# Inicializar estado si no existe
if "whatsapp_abierto" not in st.session_state:
    st.session_state.whatsapp_abierto = False

carpeta_logs = "enviados"
archivos = [f for f in os.listdir(carpeta_logs) if f.endswith(".xlsx")]

if not archivos:
    st.warning("No se encontraron archivos de historial.")
    st.stop()

archivo_seleccionado = st.selectbox("Elegí un historial para revisar si hubo respuestas y hacer seguimiento o para reenviar un mensaje sin tener que volver a cargar el Excel.", sorted(archivos, reverse=True))
ruta_archivo = os.path.join(carpeta_logs, archivo_seleccionado)

df = pd.read_excel(ruta_archivo)

valores_posibles = ["Para revisar", "No respondió", "Sí respondió", "No enviado"]
# st.subheader("Charts del historial")

# conteo_actual = df["Status-Respuesta"].value_counts()

# conteo_completo = pd.Series({estado: conteo_actual.get(estado, 0) for estado in valores_posibles})

# st.bar_chart(conteo_completo)
st.subheader("📊 Estado general de respuestas")
conteo = df["Status-Respuesta"].value_counts().reindex(valores_posibles, fill_value=0)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de contactos", len(df.index))
col2.metric("🕓 Para revisar", conteo["Para revisar"])
col3.metric("❌ No respondió", conteo["No respondió"])
col4.metric("✅ Sí respondió", conteo["Sí respondió"])

st.markdown("Al hacer click acá va a revisar si hubo respuesta en todos los contactos que tengan estado 'Para revisar'")
boton_revisar = st.button("✅ Chequear quién respondió")

st.subheader("🔍 Vista previa del historial")
st.dataframe(df)

# st.markdown("Para agregar una nota en un contacto primero ingresá el número de índice (es el que está a la izquierda del nombre). De esa forma podés identificar al contacto.")
# index_nota = st.text_input("Índice", placeholder="Ejemplo: 1")
# nueva_nota = st.text_input("Nota", placeholder="Ejemplo: Mandarle más info sobre el programa...")

# if st.button("Guardar nota"):
#     try:
#         idx = int(index_nota)
#         if idx in df.index:
#             df.at[idx, "Notas"] = nueva_nota
#             df.to_excel(ruta_archivo, index=False)
#             st.success(f"Nota guardada en el contacto {idx}")
#             st.dataframe(df)
#         else:
#             st.error("Índice fuera de rango")
#     except ValueError:
#         st.error("El índice debe ser un número")
#     except PermissionError:
#         st.error("Cerrá el archivo Excel para poder guardar")


# --- Chequear respuestas ---
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

def revisar_mensajes():
    st.info("Abriendo WhatsApp Web y chequeando respuestas...")
    driver = iniciar_driver()
    driver.get("https://web.whatsapp.com")
    st.info("Escaneá el QR si es necesario y esperá a que cargue WhatsApp Web")
    time.sleep(15)  # tiempo para escanear QR y cargar

    revisar = df[
        (df["Status-Respuesta"] == "Para revisar") 
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
                df.at[index, "Última-Respuesta"] = texto
        try:
            df.to_excel(ruta_archivo, index=False)
            st.success(f"Archivo sobrescrito: {archivo_seleccionado}")
        except PermissionError:
            st.error("No se pudo guardar el archivo. Asegurate de que no esté abierto en Excel.")

    driver.quit()

if boton_revisar:
    revisar_mensajes()

# --- Reenviar mensajes ---

st.subheader("📝 Redactá un mensaje para los que todavía no respondieron o elige a quienes querés reenvíar un mensaje")

opciones_destinatarios = ["Todos", "Para revisar", "No respondió", "No respondió hace más de 2 días", "Sí respondió", "No enviado"]


destinatarios_seleccionados = st.selectbox(
    "Primero elegí un historial. Luego seleccioná a quiénes vas enviar el mensaje según su estado:",
    opciones_destinatarios
)

if destinatarios_seleccionados == "Todos":
    destinatarios_filtrados = df[["Nombre", "Numero"]]

elif destinatarios_seleccionados == "No respondió hace más de 2 días":
    fecha_ultima_respuesta = pd.to_datetime(df["Fecha-Última-Respuesta"], dayfirst=True, errors='coerce')
    hace_2_dias = datetime.now() - timedelta(days=2)
    destinatarios_filtrados = df[
        (df["Status-Respuesta"] == "No respondió") &
        (fecha_ultima_respuesta < hace_2_dias)
    ][["Nombre", "Numero"]]
else:
    destinatarios_filtrados = df[df["Status-Respuesta"] == destinatarios_seleccionados][["Nombre", "Numero"]]


if destinatarios_seleccionados:
    st.info(f"Hay {len(destinatarios_filtrados)} destinatarios seleccionados")
    # st.dataframe(destinatarios_filtrados)

mensaje_base = st.text_area(
            "✉️ Escribí el mensaje a enviar. El `Hola {nombre}, cómo éstas? (por ejemplo)` se agrega automáticamente.",
            height=200,
            placeholder="En seguimiento de mi mensaje anterior..."
        )

if st.button("👀 Mostrar vista previa"):
            if not mensaje_base.strip():
                st.warning("Por favor, escribí el cuerpo del mensaje.")
            else:
                # print(destinatarios_filtrados["Nombre"][len(destinatarios_filtrados) - 1])
                nombre = destinatarios_filtrados["Nombre"].sample(1).values[0]
                saludo = variar_inicio_mensajes(nombre)
                mensaje = saludo + " " + mensaje_base
                st.write(f"Ejemplo para {nombre}:")
                st.info(mensaje)

if not destinatarios_filtrados.empty:               
    if st.button("🚀 Iniciar WhatsApp Web"):
                    driver = iniciar_driver()
                    st.session_state.driver = driver
                    st.session_state.contactos = destinatarios_filtrados
                    st.session_state.mensaje_cuerpo = mensaje_base
                    st.session_state.whatsapp_abierto = True
                    st.success("WhatsApp Web abierto. Escaneá el QR si es la primera vez.")       

if st.session_state.whatsapp_abierto:
    if st.button("📤 Enviar los mensajes"):
        driver = st.session_state.driver
        destinatarios = st.session_state.contactos
        mensaje = st.session_state.mensaje_cuerpo

        for index, row in destinatarios.iterrows():
            nombre = str(row["Nombre"])
            numero = str(row["Numero"])

            url = f"https://web.whatsapp.com/send?phone={numero}"
            driver.get(url)
            st.write(f"Chequeando respuestas de {nombre}...")
            time.sleep(10)

            responded, texto, fecha_hora = check_respondio(driver)

            df.at[index, "Status-Respuesta"] = "Sí respondió" if responded else "No respondió"
            if responded:
                st.info(f"{nombre} acaba de responder o lo hizo hace poco. Primero revisá su respuesta en el excel una vez terminen los envíos.")
                df.at[index, "Fecha-Última-Respuesta"] = fecha_hora
                df.at[index, "Última-Respuesta"] = texto
            else:
                estado = enviar_mensajes(driver, nombre, numero, mensaje, index, destinatarios)
                df.at[index, "Estado"] = estado
                df.at[index, "Último-Mensaje-Enviado"] = mensaje
                df.at[index, "Fecha-Último-Envio"] = datetime.now().strftime("%d/%m/%Y %H:%M")

                if df.at[index, "Status-Respuesta"] != "Para revisar":
                    df.at[index, "Status-Respuesta"] = "Para revisar"

        driver.quit()

        print(ruta_archivo)

        try:
            df.to_excel(ruta_archivo, index=False)
            st.success(f"Datos actualizados correctamente en {ruta_archivo}")
        except PermissionError:
            st.error("No se pudo actualizar el archivo. Asegurate de que no esté abierto en Excel.")
