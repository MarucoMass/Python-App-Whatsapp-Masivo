import streamlit as st 
import pandas as pd 
import os
import time
import re
from datetime import datetime, timedelta
from funciones.whatsapp_utils import iniciar_driver, enviar_mensajes, variar_inicio_mensajes, check_respondio, formatear_fecha_hora
from selenium.webdriver.common.by import By 


st.set_page_config(page_title="Historial", layout="wide")
st.title("📤 Reenvíos de WhatsApp")

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

archivo_seleccionado = st.selectbox("Elegí un historial para reenviarles un mensaje a los contactos sin tener que volver a cargar el Excel.", sorted(archivos, reverse=True))
ruta_archivo = os.path.join(carpeta_logs, archivo_seleccionado)

df = pd.read_excel(ruta_archivo)



# --- Reenviar mensajes ---

st.subheader("📝 Redactá el mensaje y elegí a los destinatarios")

opciones_destinatarios = ["Todos", "Para revisar", "No respondió", "No respondió hace más de 2 días", "Sí respondió", "No enviado"]


destinatarios_seleccionados = st.selectbox(
    "Una vez elegido el historial, seleccioná a quiénes vas enviar el mensaje según el status del mismo o su estado:",
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
        st.info(f"Hay {cantidad} destinatarios seleccionados")

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
                            # st.session_state.contactos = destinatarios_filtrados
                            # st.session_state.mensaje_cuerpo = mensaje_base
                            st.session_state.whatsapp_abierto = True
                            st.success("WhatsApp Web abierto. Escaneá el QR si es la primera vez.")       



        if st.session_state.whatsapp_abierto:
            st.session_state.contactos = destinatarios_filtrados
            st.session_state.mensaje_cuerpo = mensaje_base
            st.info("Cuando comience el proceso de envío primero verificará si hubo respuesta en el caso de los que tenían status 'Para revisar' o 'No respondió'. Si el contacto tenia ese status se cambiará a status 'Sí respondió' y no se enviará el mensaje ya que quizás el mensaje no se corresponde con la respuesta reciente.") 
            if st.button("📤 Enviar los mensajes"):
                driver = st.session_state.driver
                destinatarios = st.session_state.contactos
                mensaje = st.session_state.mensaje_cuerpo

                for index, row in destinatarios.iterrows():
                    nombre = str(row["Nombre"])
                    numero = str(row["Numero"])
                    status = df.at[index, "Status-Respuesta"]

                    if status in ["No respondió", "Para revisar"]:
                        url = f"https://web.whatsapp.com/send?phone={numero}"
                        driver.get(url)
                        st.write(f"🔍 Chequeando respuestas de {nombre}...")
                        time.sleep(10)

                        responded, texto, fecha_hora = check_respondio(driver)

                        if responded:
                            st.info(f"✅ {nombre} acaba de responder o lo hizo hace poco. No se le enviará el mensaje.")
                            df.at[index, "Status-Respuesta"] = "Sí respondió"
                            df.at[index, "Fecha-Última-Respuesta"] = fecha_hora
                            df.at[index, "Última-Respuesta"] = texto
                            continue  

                    # Se llega acá si:
                    # - No se chequeó respuesta (porque tenía "Sí respondió")
                    # - Se chequeó pero no respondió

                    url = f"https://web.whatsapp.com/send?phone={numero}"
                    driver.get(url)
                    estado = enviar_mensajes(driver, nombre, numero, mensaje, index, destinatarios)

                    df.at[index, "Estado"] = "✅ Enviado" if estado else "❌ No enviado"
                    df.at[index, "Último-Mensaje-Enviado"] = mensaje
                    df.at[index, "Fecha-Último-Envio"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    df.at[index, "Status-Respuesta"] =  "Para revisar" if estado  else "No enviado"
                    # Si no respondió (o no fue chequeado), queda como "Para revisar"
                    # if status != "Sí respondió":
                    #     df.at[index, "Status-Respuesta"] = "Para revisar"

                driver.quit()
                st.session_state.whatsapp_abierto = False

                try:
                    df.to_excel(ruta_archivo, index=False)
                    st.success(f"Datos actualizados correctamente en {ruta_archivo}")
                except PermissionError:
                    st.error("No se pudo actualizar el archivo. Asegurate de que no esté abierto en Excel.")

    else:
        st.warning("No hay destinatarios que cumplan con los criterios seleccionados.")


