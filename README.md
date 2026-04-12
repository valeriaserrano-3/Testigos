# 🚗 Testigos — Competencia Automotriz

Esta aplicación de **Streamlit** permite automatizar la descarga y organización de testigos publicitarios (OFF/ Online ) por marca, medio y mes.

## ✨ Funciones principales
- **Detección automática:** Identifica si el reporte es online / Offline .
- **Filtro de Marcas:** Procesa solo las marcas seleccionadas en el panel lateral.
- **Análisis de Ofertas:** Detecta automáticamente palabras clave como "bonos", "tasa" o "mensualidades".
- **Descarga Consolidada:** Genera un archivo **ZIP** organizado por carpetas para descargar directamente a tu computadora.

## 🚀 Cómo usar la App
1. **Acceso:** Entra al link de Streamlit desplegado (o corre `streamlit run app_testigos.py` localmente).
2. **Selección:** En el panel izquierdo, selecciona las marcas de competencia que deseas procesar.
3. **Carga:** Sube tus archivos Excel (.xlsx) en el área central.
4. **Procesar:** Haz clic en el botón **"Procesar y Descargar"**. Verás una animación de un coche mientras se descargan las imágenes.
5. **Descarga:** Una vez terminado, aparecerá un botón color rojo vino: **"📁 DESCARGAR TODOS LOS TESTIGOS (ZIP)"**. Haz clic para guardar los resultados.

## 🔒 Privacidad y Seguridad
Este repositorio ha sido configurado para ser seguro:
- **Sin rutas locales:** No se exponen correos electrónicos ni rutas de carpetas personales.
- **Almacenamiento temporal:** Los archivos se procesan en el servidor y se borran automáticamente al cerrar la sesión.
- **Sin datos sensibles:** El código no almacena contraseñas ni información privada de la empresa.

## 🛠️ Requisitos técnico (Uso local)
Si deseas ejecutarlo en tu computadora, asegúrate de instalar las dependencias:
```bash
pip install streamlit pandas requests openpyxl
