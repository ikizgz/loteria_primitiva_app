# Informe del Código: Aplicación de Lotería

## 1. Código Definitivo (loteria_app.py)

A continuación se presenta la versión final del código de la aplicación de lotería, que integra las funcionalidades de análisis de datos, generación de combinaciones y gestión de la base de datos.

```python
#!/usr/bin/env python3
"""
    __titulo__ loteria_app.py

Iniciar con: streamlit run loteria_app.py
    @param:
    @return: app web para introducir combinaciones nuevas en la BD
             y generar combinaciones de Lotería Primitiva

    Copyright (C) 2025 Iñaki Izaguerri <igizca @ gmail.com>
    License GPL-3.0 or later
    You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import io
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

DB_FILE = "loteria.db"


def cargar_combinaciones():
    conn = sqlite3.connect(DB_FILE)
    # Seleccionar explícitamente las columnas y ordenar por fecha descendente
    df = pd.read_sql(
        "SELECT fecha, n1, n2, n3, n4, n5, n6, n7 FROM combinaciones ORDER BY fecha DESC",
        conn,
    )
    conn.close()

    # Convertir las columnas de números a tipo int para evitar errores
    for i in range(1, 8):
        df[f"n{i}"] = pd.to_numeric(df[f"n{i}"], errors="coerce").fillna(0).astype(int)

    return df


def calcular_estadisticas(df):
    """
    Calcula las veces y ausencia de cada número, y su probabilidad.
    """
    # Ordenar por fecha ascendente para garantizar que la última aparición sea correcta
    df_sorted = df.sort_values(by="fecha", ascending=True)

    stats = {n: {"Veces": 0, "ultima_aparicion": -1} for n in range(1, 50)}

    # Iteramos sobre el DataFrame ordenado
    for index, row in df_sorted.iterrows():
        fecha_sorteo = datetime.strptime(row["fecha"], "%Y-%m-%d").date()
        dias_desde_sorteo = (datetime.now().date() - fecha_sorteo).days

        for i in range(1, 8):
            num = int(row[f"n{i}"])
            if num in stats:
                stats[num]["Veces"] += 1
                stats[num]["ultima_aparicion"] = dias_desde_sorteo

    # Convertimos el diccionario de estadísticas a un DataFrame
    stats_df = pd.DataFrame.from_dict(stats, orient="index")
    stats_df.index.name = "Número"
    stats_df = stats_df.reset_index()
    stats_df["Ausencia (días)"] = stats_df["ultima_aparicion"]
    stats_df = stats_df.drop(columns=["ultima_aparicion"])

    # --- Nuevo cálculo de probabilidad basado en normalización ---
    # Normalizar Ausencia (días)
    ausencia_min = stats_df["Ausencia (días)"].min()
    ausencia_max = stats_df["Ausencia (días)"].max()
    if ausencia_max > ausencia_min:
        stats_df["Prob_Ausencia"] = (stats_df["Ausencia (días)"] - ausencia_min) / (
            ausencia_max - ausencia_min
        )
    else:
        stats_df["Prob_Ausencia"] = 0

    # Normalizar Frecuencia (inverso, los menos frecuentes tienen más probabilidad)
    frecuencia_min = stats_df["Veces"].min()
    frecuencia_max = stats_df["Veces"].max()
    if frecuencia_max > frecuencia_min:
        stats_df["Prob_Frecuencia"] = 1 - (
            (stats_df["Veces"] - frecuencia_min) / (frecuencia_max - frecuencia_min)
        )
    else:
        stats_df["Prob_Frecuencia"] = 0

    # Ponderar y sumar para obtener la Probabilidad Total
    # Pesos (ajustables): 60% para ausencia y 40% para frecuencia
    stats_df["Probabilidad"] = (stats_df["Prob_Ausencia"] * 0.6) + (
        stats_df["Prob_Frecuencia"] * 0.4
    )

    # Formatear la probabilidad como porcentaje
    stats_df["Probabilidad"] = (stats_df["Probabilidad"] * 100).round(2).astype(
        str
    ) + "%"

    # Limpiar columnas temporales
    stats_df = stats_df.drop(columns=["Prob_Ausencia", "Prob_Frecuencia"])
    stats_df.sort_values(by="Número", ascending=True, inplace=True)

    return stats_df


def generar_combinaciones_equilibradas(stats_df, cantidad=7):
    """
    Genera 'cantidad' combinaciones con 6 números únicos cada una,
    basadas en la probabilidad, asegurando que no se repitan entre sí.
    """
    # Ordenar el DataFrame por probabilidad para la selección de números
    stats_df.sort_values(by="Probabilidad", ascending=False, inplace=True)

    # Obtener los números de la lista ordenada por sus probabilidades
    ordenados = stats_df["Número"].tolist()

    grupo1 = ordenados[:14]  # top 14
    grupo2 = ordenados[14:35]  # siguientes 21
    grupo3 = ordenados[35:]  # últimos 14

    rng = np.random.default_rng()
    usados = set()
    combinaciones = []

    for _ in range(cantidad):
        # Seleccionar 2 del grupo 1, 3 del grupo 2 y 1 del grupo 3
        c1 = rng.choice([n for n in grupo1 if n not in usados], 2, replace=False)
        c2 = rng.choice([n for n in grupo2 if n not in usados], 3, replace=False)
        c3 = rng.choice([n for n in grupo3 if n not in usados], 1, replace=False)

        # Unir y ordenar los números para formar la combinación de 6 números
        comb = np.sort(np.concatenate([c1, c2, c3]))
        combinaciones.append(comb)
        usados.update(comb)

    return np.array(combinaciones)


def insertar_combinacion(fecha, nums):
    """
    Inserta una nueva combinación en la base de datos.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Verificar si la combinación ya existe para esa fecha
        cursor.execute("SELECT * FROM combinaciones WHERE fecha=?", (fecha,))
        if cursor.fetchone():
            return False, "La combinación para esta fecha ya existe."
        # Construir la consulta de inserción dinámicamente
        columnas = ["fecha"] + [f"n{i}" for i in range(1, 8)]
        sql_insert = f"""
            INSERT INTO combinaciones ({", ".join(columnas)})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        valores = [fecha] + nums
        cursor.execute(sql_insert, valores)
        conn.commit()
        return True, "Combinación añadida con éxito."
    except Exception as e:
        return False, str(e)
    finally:
        if conn:
            conn.close()


def crear_db():
    """
    Crea la base de datos y la tabla de combinaciones si no existen.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS combinaciones (
            fecha TEXT NOT NULL UNIQUE,
            n1 INTEGER,
            n2 INTEGER,
            n3 INTEGER,
            n4 INTEGER,
            n5 INTEGER,
            n6 INTEGER,
            n7 INTEGER
        )
    """
    )
    conn.commit()
    conn.close()


def main():
    # Usar el ancho completo de la página
    st.set_page_config(layout="wide")

    crear_db()
    st.title("Generador de combinaciones de lotería")

    # --- Sección de Análisis de datos ---
    st.header("Análisis de datos")

    # Creamos dos columnas con anchos relativos
    # (la segunda el doble de ancha que la primera)
    col1, col2 = st.columns([1, 2])

    with col1:
        # Sub-sección de estadísticas por número
        st.subheader("Estadísticas por número (1–49)")
        df_combinaciones = cargar_combinaciones()
        if not df_combinaciones.empty:
            stats = calcular_estadisticas(df_combinaciones)
            st.dataframe(stats.set_index("Número"), width="content")
        else:
            st.info("No hay sorteos registrados aún.")

    with col2:
        # Sub-sección para ver todas las combinaciones
        st.subheader("Historial de combinaciones")
        if not df_combinaciones.empty:
            st.dataframe(df_combinaciones.set_index("fecha"), width="content")
        else:
            st.info("No hay combinaciones registradas aún.")

    # --- Sección de Operaciones ---
    st.header("Operaciones")
    tab_insertar, tab_generar = st.tabs(["Añadir sorteo", "Generar combinación"])

    with tab_insertar:
        st.subheader("Añadir nuevo sorteo")
        st.info("Introduce los 7 números separados por comas. (1-49)")
        fecha_input = st.date_input(
            "Fecha del sorteo",
            datetime.now(),
            max_value=datetime.now(),
            help="Elige la fecha del sorteo, por defecto la de hoy.",
        )
        numeros_input = st.text_input(
            "Números", help="Ejemplo: 1, 23, 45, 10, 3, 2, 49"
        )
        if st.button("Añadir sorteo"):
            try:
                nums = [int(n.strip()) for n in numeros_input.split(",")]
                if len(nums) == 7:
                    fecha = fecha_input.strftime("%Y-%m-%d")
                    exito, mensaje = insertar_combinacion(fecha, nums)
                    if exito:
                        st.success(f"Sorteo añadido: {nums}")
                    else:
                        st.error(f"Error: {mensaje}")
                else:
                    st.error("Debes introducir exactamente 7 números")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab_generar:
        st.subheader("Generar combinaciones")
        num_combs = st.number_input(
            "¿Cuántas combinaciones quieres generar? (1-8)",
            min_value=1,
            max_value=8,
            value=7,
            step=1,
        )
        if st.button("Generar combinaciones"):
            stats = calcular_estadisticas(df_combinaciones)
            combs = generar_combinaciones_equilibradas(stats, cantidad=int(num_combs))
            if len(combs) > 0:
                st.success("Combinaciones generadas:")
                combinaciones_str = "\n".join(
                    [",".join(map(str, comb)) for comb in combs]
                )
                b = io.BytesIO()
                b.write(combinaciones_str.encode("utf-8"))
                b.seek(0)
                for i, fila in enumerate(combs, 1):
                    st.write(f"Combinación {i}: {fila}")
                st.download_button(
                    label="Descargar combinaciones",
                    data=b,
                    file_name="combinaciones.txt",
                    mime="text/plain",
                )
            else:
                st.error(
                    "No se pudieron generar combinaciones. Asegúrate de que hay "
                    "suficientes números disponibles para elegir sin repetir."
                )


if __name__ == "__main__":
    main()
```

## 2. Explicación Detallada del Código

### Estructura General

El programa es una aplicación web interactiva construida con la librería **Streamlit**. Su objetivo principal es ayudarte a gestionar y analizar los sorteos de la Lotería Primitiva, y a generar nuevas combinaciones basadas en un algoritmo de probabilidad.

### Componentes Clave

#### Manejo de la Base de Datos (sqlite3)

- **DB_FILE** = "loteria.db": Define el nombre del archivo de la base de datos SQLite.

- **crear_db()**: Esta función crea una tabla llamada combinaciones si no existe. La tabla almacena la fecha del sorteo y los 7 números (6 principales y 1 complementario).

- **cargar_combinaciones()**: Lee todos los registros de la tabla combinaciones y los carga en un DataFrame de Pandas, ordenándolos por fecha de forma descendente. Esto es lo que se muestra en la sección de "Historial de combinaciones".

- **insertar_combinacion()**: Se encarga de guardar un nuevo sorteo en la base de datos. Antes de insertar, verifica que la combinación para esa fecha no exista para evitar duplicados.

#### Cálculo de Estadísticas y Probabilidades (pandas, numpy)

- **calcular_estadisticas(df)**: Esta es la función central del algoritmo.
  - Calcula el número de veces que cada número ha salido y la cantidad de días que lleva sin aparecer.
  - Aplica la normalización para convertir la "Ausencia" y la "Frecuencia" de cada número en valores entre 0 y 1. Esto permite compararlos en una escala común.
  - Calcula la "Probabilidad" final de cada número como una media ponderada: P(total)=(P(ausencia)
times0.6)+(P(frecuencia)
times0.4). Puedes ajustar los pesos 0.6 y 0.4 para darle más o menos importancia a la ausencia o a la frecuencia.

#### Generación de Combinaciones (numpy)

- **generar_combinaciones_equilibradas(stats_df, cantidad)**: Esta función crea las combinaciones de 6 números basándose en las probabilidades calculadas.
  - Primero, ordena todos los números del 1 al 49 de mayor a menor probabilidad.
  - Divide estos 49 números en tres grupos:
    - Grupo 1 (14 números): Los más probables (top 14).
    - Grupo 2 (21 números): Los de probabilidad media.
    - Grupo 3 (14 números): Los menos probables.  
  - Para cada combinación a generar, selecciona 2 números del Grupo 1, 3 del Grupo 2 y 1 del Grupo 3, asegurándose de que no haya números repetidos entre las combinaciones generadas. Esto garantiza un equilibrio entre los números más y menos probables, basándose en tu historial.

#### Interfaz de Usuario (streamlit)

- **main()**: Es la función principal que organiza la interfaz.
  - Usa `st.set_page_config(layout="wide")` para que la página ocupe todo el ancho de la pantalla.
  - Utiliza `st.columns()` para organizar las estadísticas y el historial en dos columnas.
  - Define dos pestañas (`st.tabs`):
    - **"Añadir sorteo"**: Permite introducir manualmente una combinación, validando que se ingresen 7 números y que la fecha no esté duplicada.
    - **"Generar combinación"**: Muestra el campo para elegir la cantidad de combinaciones (de 1 a 8) y el botón para generarlas.
  - Una vez generadas, las muestra y ofrece la opción de descargarlas en un archivo de texto.

*Este informe abarca la funcionalidad completa de la aplicación, desde la gestión de datos hasta la lógica del algoritmo de probabilidad y la interfaz de usuario.*
