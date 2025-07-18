# Python-App-Whatsapp-Masivo

# 🟢 INSTRUCCIONES DE INSTALACIÓN
1. Descargar el repo o clonarlo.
2. Si ya tienes python instalado ir directamente al paso 4. De lo contrario debes descargar python o una versión embebida de python y meterlo en la carpeta del proyecto. Yo usé python 3.11.4.
3. Instalar pip en la carpeta de python embebido.
4. Instalar las dependencias que figuran en requirements.txt de manera o en un entorno virtual con venv
5. Si ya tenia python instalado en su sistema debe modificar archivo `masivo.bat` para que corra este comando `streamlit run app.py`. Si va a usar una carpeta con python embebido debe mover el `app.py` a esa carpeta y en el `masvio.bat` deje el comando `.\python\python.exe -m streamlit run .\python\app.py`.

# 🟢 INSTRUCCIONES DE USO 

## 📁 1. ABRIR LA APLICACIÓN

1. Abrí la carpeta llamada: `whatsapp_masivo`.
2. Hacé doble clic sobre el archivo: `masivo.bat`.
3. Se abrirá una ventana negra (consola) y automáticamente se abrirá la app en tu navegador.  
4. Si no se abre sola, abrí el navegador y pegá esto:  
   👉 [http://localhost:8501](http://localhost:8501)

5. Cuando termines, podés cerrar el navegador y la ventana negra.

> ⚠️ No borres ni muevas los archivos dentro de la carpeta `python`.  
> No necesitás instalar nada, todo está incluido.  
> **IMPORTANTE:** Asegurate de tener **Google Chrome** como navegador predeterminado.

---

## 🧠 ¿CÓMO FUNCIONA LA APP?

### 1. 📄 Subís un archivo Excel

El Excel debe tener estas 2 columnas obligatorias (**con estos nombres exactos**):

- `Nombre` → el nombre de la persona  
- `Numero` → el número de WhatsApp con código de país (sin el `+`)  
  (Ejemplo: `5491123456789`)

---

### 2. 💬 Redactás el mensaje

Escribís el texto que querés mandar.  
La app **automáticamente agrega** al inicio: `Hola {nombre}`

Solo tenés que escribir el resto del mensaje.

---

### 3. 🧭 Iniciás sesión en WhatsApp Web

Tocás el botón **"Iniciar sesión con WhatsApp Web"**.  
Se abrirá otra ventana del navegador con un perfil nuevo donde podés escanear el QR.

> ⚠️ Este perfil se guarda. La próxima vez **no necesitás volver a escanear**.  
> Se abre con otro perfil de Chrome para que puedas usar tu WhatsApp normal sin interferencias.

---

### 4. ✅ Mandás los mensajes

Una vez que iniciaste sesión, tocá:

**"Ya escaneé el QR y quiero mandar los mensajes"**

Los mensajes se envían uno por uno y la app te muestra el progreso en tiempo real.

---

### 5. 📥 Descargás el resultado

Al finalizar, podés ver el estado de cada envío y descargar un archivo `.csv` con el resumen.

---

## ❓¿TENÉS PROBLEMAS?

- Cerrá todo y volvé a ejecutar el archivo `masivo.bat`.
- Asegurate de tener Google Chrome instalado y como navegador predeterminado.
