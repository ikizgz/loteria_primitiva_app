#!/bin/bash

# Este script activa el entorno virtual, inicia la aplicación de Streamlit en segundo plano,
# y luego la cierra cuando el usuario lo solicite.
echo "Activando el entorno virtual..."
source venv/bin/activate

echo "Iniciando la aplicación de lotería en segundo plano..."
streamlit run src/loteria_app.py &

# Capturar el ID del proceso de Streamlit para poder cerrarlo después
STREAMLIT_PID=$!

echo ""
echo "¡La aplicación se ha iniciado! Puedes verla en tu navegador."
echo "Cuando hayas terminado, vuelve a esta terminal y presiona la tecla [Enter] para cerrarla."

# Esperar a que el usuario presione Enter
read -r

echo "Cerrando la aplicación (PID: $STREAMLIT_PID)..."
kill "$STREAMLIT_PID"

echo "Desactivando el entorno virtual..."
deactivate