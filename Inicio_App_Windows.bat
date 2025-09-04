@echo off
REM Este script activa el entorno virtual y ejecuta la aplicación de Streamlit.
REM Ofrece instrucciones para cerrar todo de forma segura.

echo Activando el entorno virtual...
call .venv\Scripts\activate.bat

echo.
echo Iniciando la aplicación de lotería. Se abrirá en una nueva ventana de navegador.
echo.

REM Iniciar la app en una nueva ventana. La terminal actual seguirá activa.
start "Lotería App" streamlit run loteria_app.py

echo La aplicación se esta ejecutando. Para cerrarla de forma segura,
echo primero cierra la pestana del navegador.
echo.
echo Luego, presiona Ctrl+C en esta terminal para detener el servidor de Streamlit.
echo Y finalmente, escribe "deactivate" para salir del entorno virtual.

pause