from datetime import datetime
import streamlit as st
import pandas as pd
import os

from funciones.whatsapp_utils import enviar_mensajes, normalizar_numero, variar_inicio_mensajes, iniciar_driver


# ------------- Streamlit -------------

st.set_page_config(page_title="Envío masivo de WhatsApp", page_icon="💬", layout="wide")
st.title("📲 Envío masivo de WhatsApp")
st.markdown("Subí un Excel con columnas **Nombre** y **Numero**, y escribí el cuerpo del mensaje.")

archivo = st.file_uploader("Subí tu Excel", type=["xlsx"])

# Inicializar estado si no existe
if "whatsapp_abierto" not in st.session_state:
    st.session_state.whatsapp_abierto = False

if "envios_completados" not in st.session_state:
    st.session_state.envios_completados = False

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
            "✔ Ponle un nombre a la lista. Cuando termines de enviar se guarda un excel con el status de los mensajes en una carpeta llamada 'enviados'",
            height=100,
            placeholder="Ejemplo: Lista de 2da aula abierta YPP"
        )
        
        mensaje_base = st.text_area(
            "✉️ Escribí el cuerpo del mensaje. El `Hola {nombre}, cómo éstas? (por ejemplo)` se agrega automáticamente.",
            height=200,
            placeholder="Te escribimos desde la fundación para recordarte..."
        )

        # pdf = st.file_uploader("Adjunta un pdf si lo necesitas", type=["pdf"])

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
                # st.session_state.mensaje_cuerpo = mensaje_base
                # st.session_state.nombre_lista = nombre_lista
                st.session_state.whatsapp_abierto = True
                st.success("WhatsApp Web abierto. Escaneá el QR si es la primera vez.")
        else:
            if not st.session_state.get("envios_completados", False):
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
        if "driver" in st.session_state and st.session_state.whatsapp_abierto and not st.session_state.get("envios_completados", False):
            st.session_state.mensaje_cuerpo = mensaje_base
            st.session_state.nombre_lista = nombre_lista
            if st.button("📤 Enviar los mensajes"):
                driver = st.session_state.driver
                contactos = st.session_state.contactos
                mensaje_cuerpo = st.session_state.mensaje_cuerpo
                historial = []

                for index, row in contactos.iterrows():
                    nombre = str(row["Nombre"])
                    numero = str(row["Numero"])
                    
                    estado = enviar_mensajes(driver, nombre, numero, mensaje_cuerpo, index, contactos)
                    
                    historial.append({
                        "Nombre": nombre,
                        "Numero": numero,
                        "Fecha-Último-Envio": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Último-Mensaje-Enviado": mensaje_cuerpo,
                        "Estado":"✅ Enviado" if estado else "❌ No enviado",
                        "Status-Respuesta":"Para revisar" if estado  else "No enviado",
                        "Fecha-Última-Respuesta": "---",
                        # "Reenviado": "No",
                        "Última-Respuesta": ""
                        # "Notas": ""
                    })

                st.session_state.envios_completados = True  
                st.session_state.whatsapp_abierto = False

                driver.quit()

                folder_path = "./enviados"
                os.makedirs(folder_path, exist_ok=True)

                df_log = pd.DataFrame(historial)
                nombre_archivo = st.session_state.nombre_lista + "-" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                archivo_log = os.path.join(folder_path, f"{nombre_archivo}.xlsx")

                df_log.to_excel(archivo_log, index=False)

                st.success("El proceso de envío terminó y se guardó un excel en la carpeta 'enviados'. La podés encontrar en el apartado 'Historial' o en la carpeta del proyecto.")

    else:
        st.error("❌ El Excel no tiene las columnas 'Nombre' o 'Numero'")
