#!/usr/bin/env python3
"""
    __titulo__ importar_datos.py

Importación de datos inicial desde el archivo ODS a una base de datos SQLite

    Copyright (C) 2025 Iñaki Izaguerri <igizca @ gmail.com>
    License GPL-3.0 or later
    You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import calendar
import sqlite3

import pandas as pd

DB_FILE = "../src/loteria.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS combinaciones")  # Resetea la tabla si ya existe
    c.execute(
        """
        CREATE TABLE combinaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            dia_sem TEXT,
            n1 INTEGER, n2 INTEGER, n3 INTEGER,
            n4 INTEGER, n5 INTEGER, n6 INTEGER, n7 INTEGER
        )
    """
    )
    conn.commit()
    return conn


def importar_ods(conn, archivo="Loto.ods", hoja="Combinaciones"):
    df = pd.read_excel(archivo, sheet_name=hoja, engine="odf")

    for _, row in df.iterrows():
        fecha = pd.to_datetime(row["fecha"])
        dia_sem = calendar.day_name[fecha.weekday()]  # Ejemplo: Lunes, Martes...
        numeros = [int(row[f"n{i}"]) for i in range(1, 8)]
        conn.execute(
            """
            INSERT INTO combinaciones (fecha, dia_sem, n1, n2, n3, n4, n5, n6, n7)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (fecha.strftime("%Y-%m-%d"), dia_sem, *numeros),
        )

    conn.commit()
    print("✅ Datos importados correctamente a loteria.db")


if __name__ == "__main__":
    conn = init_db()
    importar_ods(conn)
    conn.close()
