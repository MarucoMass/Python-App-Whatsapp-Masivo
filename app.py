import streamlit as st
import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse
import io
import random
import os
import psutil

st.set_page_config(page_title="Envío masivo de WhatsApp", page_icon="💬")
st.title("📤 Envío Masivo de WhatsApp")
st.markdown("Subí un Excel con columnas **Nombre** y **Numero**, y escribí el cuerpo del mensaje.\n\nEl `Hola {nombre},` se agrega automáticamente.")

def is_profile_in_use(profile_path):
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if 'chrome' in proc.info['name'].lower():
                if profile_path in ' '.join(proc.info['cmdline']):
                    return True
        except Exception:
            continue
    return False

def iniciar_driver():
    profile_path = os.path.abspath("selenium_profile")
    if is_profile_in_use(profile_path):
        st.error("⚠️ Cerrá el Chrome que está usando la sesión guardada antes de continuar.")
        st.stop()

    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={profile_path}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Iniciar estado si no existe
if 'estado' not in st.session_state:
    st.session_state.estado = 'inicio'

# Subir archivo y mensaje
archivo = st.file_uploader("📄 Subí el archivo Excel (.xlsx)", type=["xlsx"])
mensaje_cuerpo = st.text_area("✏️ Escribí el cuerpo del mensaje (sin el 'Hola {nombre},')", height=200, placeholder="Te escribimos desde la fundación para recordarte...")

# Procesar archivo si se subió y aún no fue cargado
if archivo and 'contactos' not in st.session_state:
    try:
        df = pd.read_excel(archivo)
        contactos = df[["Nombre", "Numero"]]
        st.session_state.contactos = contactos
        st.session_state.mensaje_cuerpo = mensaje_cuerpo
    except Exception as e:
        st.error(f"❌ Error al leer el archivo: {e}")
        st.stop()

# Si los contactos ya están en memoria, mostrar cantidad
if 'contactos' in st.session_state:
    st.success(f"📊 Se cargaron {len(st.session_state.contactos)} contactos.")
else:
    st.info("📥 Subí un archivo Excel válido para comenzar.")
    st.stop()

if st.session_state.estado == 'inicio':
    if st.button("🚀 Iniciar sesión en WhatsApp Web"):
        st.session_state.driver = iniciar_driver()
        st.session_state.driver.get("https://web.whatsapp.com")
        st.session_state.estado = 'qr'

if st.session_state.estado == 'qr':
    st.warning("📷 Escaneá el código QR. Luego hacé clic en el botón de abajo para continuar.")
    if st.button("✅ Ya escaneé el código QR y quiero enviar los mensajes"):
        st.session_state.estado = 'enviando'

if st.session_state.estado == 'enviando':
    historial = []
    driver = st.session_state.driver
    contactos = st.session_state.contactos
    mensaje_cuerpo = st.session_state.mensaje_cuerpo

    for index, row in contactos.iterrows():
        nombre = str(row["Nombre"])
        numero = str(row["Numero"])
        mensaje = f"Hola {nombre}, {mensaje_cuerpo}"
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

        time.sleep(random.randint(18, 25))

    driver.quit()
    st.session_state.estado = 'completo'

    df_historial = pd.DataFrame(historial)
    st.success("🎉 Todos los mensajes fueron procesados.")
    st.markdown("## 📋 Historial de envíos")
    st.dataframe(df_historial)

    # Descargar CSV
    csv = df_historial.to_csv(index=False).encode("utf-8")
    fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_csv = f"historial_envios_{fecha_actual}.csv"
    st.download_button(
        label="⬇️ Descargar historial en CSV",
        data=csv,
        file_name=nombre_csv,
        mime="text/csv"
    )

    # Descargar Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_historial.to_excel(writer, index=False, sheet_name="Historial")
        # writer.save()
    excel_data = output.getvalue()
    nombre_excel = f"historial_envios_{fecha_actual}.xlsx"
    st.download_button(
        label="⬇️ Descargar historial en Excel",
        data=excel_data,
        file_name=nombre_excel,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

