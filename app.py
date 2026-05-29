import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import tempfile
import subprocess
import re
import numpy as np
from fpdf import FPDF
import tempfile
from PIL import Image

# =====================================================
# CONFIGURACIÓN
# =====================================================
st.set_page_config(
    page_title="Analizador de resultados Milton Ochoa",
    layout="wide"
)

logo = Image.open("logo.png")
st.image(logo, width=180)

st.title("📊 Analizador de resultados Milton Ochoa")


# =====================================================
# CONVERTIR XLS -> XLSX
# =====================================================
def convertir_xls_si_es_necesario(ruta):

    ruta = Path(ruta)

    if ruta.suffix.lower() == ".xlsx":
        return str(ruta)

    nuevo_archivo = ruta.with_suffix(".xlsx")

    comando = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "xlsx",
        str(ruta),
        "--outdir",
        str(ruta.parent)
    ]

    subprocess.run(comando)

    return str(nuevo_archivo)


# =====================================================
# DETECTAR COLUMNAS
# =====================================================
def detectar_columnas(df, fila_inicio):

    fila_superior = (
        df.iloc[fila_inicio - 1]
        .fillna("")
        .astype(str)
        .tolist()
    )

    fila_actual = (
        df.iloc[fila_inicio]
        .fillna("")
        .astype(str)
        .tolist()
    )

    columnas = {}

    for i in range(len(fila_actual)):

        superior = str(
            fila_superior[i]
        ).strip().lower()

        actual = str(
            fila_actual[i]
        ).strip().lower()

        # =================================================
        # ESTUDIANTE
        # =================================================
        if "nombre estudiante" in actual:

            columnas[i] = "Estudiante"

        # =================================================
        # MATEMÁTICAS
        # =================================================
        elif (
            "gené" in actual
            or "gene" in actual
            or "cuantitativo" in actual
        ):

            columnas[i] = "Matematicas_Genericos"

        elif (
            "no gené" in actual
            or "no gene" in actual
            or "específico" in actual
            or "especifico" in actual
        ):

            columnas[i] = "Matematicas_NoGenericos"

        # =================================================
        # QUÍMICA
        # =================================================
        elif (
            "química" in actual
            or "quimica" in actual
        ):

            columnas[i] = "Quimica"

        # =================================================
        # FÍSICA
        # =================================================
        elif (
            "física" in actual
            or "fisica" in actual
        ):

            columnas[i] = "Fisica"

        # =================================================
        # BIOLOGÍA
        # =================================================
        elif (
            "biología" in actual
            or "biologia" in actual
        ):

            columnas[i] = "Biologia"

        # =================================================
        # CTS
        # =================================================
        elif (
            "c.t.s" in actual
            or "cts" in actual
        ):

            columnas[i] = "CTS"

        # =================================================
        # SOCIALES
        # =================================================
        elif "sociales" in actual:

            columnas[i] = "Sociales"

        # =================================================
        # CIUDADANAS
        # =================================================
        elif (
            "ciudada" in actual
            or "ciudadanas" in actual
        ):

            columnas[i] = "Ciudadanas"

        # =================================================
        # LECTURA CRÍTICA
        # =================================================
        elif (
            "lenguaje" in actual
            or "lectura crítica" in superior
            or "lectura critica" in superior
        ):

            columnas[i] = "LecturaCritica"

        # =================================================
        # INGLÉS
        # =================================================
        elif (
            "inglés" in superior
            or "ingles" in superior
        ):

            columnas[i] = "Ingles"

        # =================================================
        # DEFINITIVA
        # =================================================
        elif "def" in actual:

            columnas[i] = "Definitiva"

        # =================================================
        # GLOBAL
        # =================================================
        elif "global" in actual:

            columnas[i] = "Global"

    return columnas


# =====================================================
# CARGAR DATOS
# =====================================================
def cargar_datos(archivo):

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=Path(archivo.name).suffix
    ) as tmp:

        tmp.write(archivo.getbuffer())

        ruta_temp = tmp.name

    ruta_final = convertir_xls_si_es_necesario(
        ruta_temp
    )

    df = pd.read_excel(
        ruta_final,
        header=None
    )

    # =================================================
    # DETECTAR TIPO
    # =================================================
    es_martes_prueba = False

    for i in range(min(20, len(df))):

        fila_texto = " ".join(
            df.iloc[i]
            .fillna("")
            .astype(str)
            .tolist()
        ).lower()

        if "martes de prueba" in fila_texto:

            es_martes_prueba = True
            break

    # =================================================
    # DETECTAR NOMBRE PRUEBA
    # =================================================
    nombre_prueba = Path(
        archivo.name
    ).stem

    for i in range(len(df)):

        fila = (
            df.iloc[i]
            .fillna("")
            .astype(str)
            .tolist()
        )

        texto = " ".join(fila)

        match = re.search(
            r"Prueba\s*No\s*(\d+)",
            texto,
            re.IGNORECASE
        )

        if match:

            numero = int(
                match.group(1)
            )

            nombre_prueba = (
                f"Prueba No {numero:02d}"
            )

            break

        match_go = re.search(
            r"\bGO\s*([0-9]+)\b",
            texto,
            re.IGNORECASE
        )

        if match_go:

            numero = int(
                match_go.group(1)
            )

            nombre_prueba = f"GO {numero}"

    # =================================================
    # BUSCAR ENCABEZADO
    # =================================================
    fila_inicio = None

    for i in range(len(df)):

        fila = (
            df.iloc[i]
            .fillna("")
            .astype(str)
            .tolist()
        )

        texto = " ".join(fila)

        if "Nombre Estudiante" in texto:

            fila_inicio = i
            break

    if fila_inicio is None:

        st.error(
            f"No se encontró encabezado en {archivo.name}"
        )

        return None

    # =================================================
    # DETECTAR COLUMNAS
    # =================================================
    columnas = detectar_columnas(
        df,
        fila_inicio
    )

    # =================================================
    # EXTRAER DATOS
    # =================================================
    datos = df.iloc[
        fila_inicio + 1:
    ].copy()

    datos_limpios = pd.DataFrame()

    # =================================================
    # POSICIONES REALES
    # =================================================
    if es_martes_prueba:

        posiciones_reales = {

            "Estudiante": 6,

            "Matematicas_Genericos": 16,
            "Matematicas_NoGenericos": 17,

            "Quimica": 19,

            "Fisica": 22,

            "Biologia": 23,

            "CTS": 24,

            "Sociales": 27,

            "Ciudadanas": 30,

            "LecturaCritica": 33,

            "Ingles": 38,

            "Definitiva": 40,

            "Global": 43
        }

    else:

        posiciones_reales = {

            "Estudiante": 7,

            "Matematicas_Genericos": 18,
            "Matematicas_NoGenericos": 20,

            "Quimica": 22,

            "Fisica": 23,

            "Biologia": 26,

            "CTS": 29,

            "Sociales": 32,

            "Ciudadanas": 36,

            "LecturaCritica": 41,

            "Ingles": 44,

            "Definitiva": 46,

            "Global": 49
        }

    # =================================================
    # EXTRAER COLUMNAS
    # =================================================
    for nombre, indice_real in posiciones_reales.items():

        if indice_real < len(datos.columns):

            datos_limpios[nombre] = (
                datos.iloc[:, indice_real]
            )

    # =================================================
    # LIMPIAR
    # =================================================
    if "Estudiante" in datos_limpios.columns:

        datos_limpios = datos_limpios.dropna(
            subset=["Estudiante"]
        )

    # =================================================
    # NUMÉRICAS
    # =================================================
    columnas_numericas = [

        "Matematicas_Genericos",
        "Matematicas_NoGenericos",

        "Quimica",
        "Fisica",
        "Biologia",
        "CTS",

        "Sociales",
        "Ciudadanas",

        "LecturaCritica",

        "Ingles",

        "Definitiva",

        "Global"
    ]

    for col in columnas_numericas:

        if col in datos_limpios.columns:

            datos_limpios[col] = pd.to_numeric(
                datos_limpios[col],
                errors="coerce"
            )

    # =================================================
    # SIMULACRO
    # =================================================
    datos_limpios["Simulacro"] = nombre_prueba

    return datos_limpios


# =====================================================
# SUBIR ARCHIVOS
# =====================================================
archivos = st.file_uploader(
    "📂 Sube archivos Excel",
    type=["xls", "xlsx"],
    accept_multiple_files=True
)


# =====================================================
# PROCESAR
# =====================================================
if archivos:

    todos = []

    barra = st.progress(0)

    for i, archivo in enumerate(archivos):

        df_temp = cargar_datos(
            archivo
        )

        if df_temp is not None:

            todos.append(df_temp)

        barra.progress(
            (i + 1) / len(archivos)
        )

    if len(todos) > 0:

        df = pd.concat(
            todos,
            ignore_index=True
        )

        # =================================================
        # CALCULAR POSICIÓN POR PRUEBA
        # =================================================
        df["Posicion"] = (

            df.groupby("Simulacro")["Global"]

            .rank(
                ascending=False,
                method="min"
            )

        )

        # =================================================
        # ORDEN
        # =================================================
        df["NumeroPrueba"] = (

            df["Simulacro"]
            .astype(str)
            .str.extract(r"(\d+)")

        )

        df["NumeroPrueba"] = pd.to_numeric(
            df["NumeroPrueba"],
            errors="coerce"
        )

        df = df.sort_values(
            by=[
                "NumeroPrueba",
                "Simulacro"
            ]
        )

        st.success(
            "✅ Archivos cargados correctamente"
        )

        # =================================================
        # VER BASE
        # =================================================
        with st.expander("📋 Ver Base Completa"):

            st.dataframe(df)

        # =================================================
        # ESTUDIANTES
        # =================================================
        estudiantes = sorted(

            df["Estudiante"]
            .astype(str)
            .unique()

        )

        estudiante = st.selectbox(
            "👨‍🎓 Selecciona un estudiante",
            estudiantes
        )

        estudiante_df = df[
            df["Estudiante"]
            .astype(str)
            == estudiante
        ]

        st.subheader(
            f"📌 Resultados de {estudiante}"
        )

        # =================================================
        # TABLA LIMPIA
        # =================================================
        columnas_mostrar = [

            "Simulacro",

            "Posicion",

            "Matematicas_Genericos",
            "Matematicas_NoGenericos",

            "Quimica",
            "Fisica",
            "Biologia",
            "CTS",

            "Sociales",
            "Ciudadanas",

            "LecturaCritica",

            "Ingles",

            "Definitiva",

            "Global"
        ]

        columnas_existentes = [

            c for c in columnas_mostrar

            if c in estudiante_df.columns
        ]

        tabla_estudiante = estudiante_df[
            columnas_existentes
        ]

        st.dataframe(
            tabla_estudiante,
            hide_index=True
        )

        # =================================================
        # ASIGNATURAS
        # =================================================
        asignaturas = [

            "Matematicas_Genericos",
            "Matematicas_NoGenericos",

            "Quimica",
            "Fisica",
            "Biologia",
            "CTS",

            "Sociales",
            "Ciudadanas",

            "LecturaCritica",

            "Ingles"
        ]

        asignaturas_disponibles = [

            col for col in asignaturas

            if col in estudiante_df.columns
        ]

        # =================================================
        # EVOLUCIÓN
        # =================================================
        st.subheader(
            "📈 Evolución por Asignatura"
        )

        asignatura = st.selectbox(
            "Selecciona una asignatura",
            asignaturas_disponibles
        )

        datos_grafica = estudiante_df[
            ["Simulacro", asignatura]
        ].dropna()

        if len(datos_grafica) > 0:

            fig1, ax1 = plt.subplots(
                figsize=(10, 5)
            )

            ax1.plot(

                datos_grafica["Simulacro"],

                datos_grafica[asignatura],

                marker="o"

            )

            ax1.set_title(
                f"Evolución en {asignatura}"
            )

            ax1.set_ylabel(
                "Puntaje"
            )

            ax1.set_xlabel(
                "Prueba"
            )

            plt.xticks(rotation=25)

            st.pyplot(fig1)

        # =================================================
        # MEJOR DESEMPEÑO
        # =================================================
        st.subheader(
            "🏆 Mejor Desempeño"
        )

        mejores = []

        for materia in asignaturas:

            if materia not in estudiante_df.columns:
                continue

            serie = estudiante_df[
                materia
            ].dropna()

            if len(serie) == 0:
                continue

            indice = serie.idxmax()

            fila = estudiante_df.loc[
                indice
            ]

            mejores.append({

                "Asignatura":
                materia,

                "Mejor Puntaje":
                round(
                    fila[materia],
                    2
                ),

                "Prueba":
                fila["Simulacro"]
            })

        mejores_df = pd.DataFrame(
            mejores
        )

        st.dataframe(
            mejores_df,
            hide_index=True
        )

        # =================================================
        # DESEMPEÑO POR ÁREAS
        # =================================================
        st.subheader(
            "📊 Desempeño por Áreas"
        )

        simulacros = estudiante_df[
            "Simulacro"
        ].unique()

        simulacro_sel = st.selectbox(
            "Selecciona una prueba",
            simulacros
        )

        datos_filtrados = estudiante_df[
            estudiante_df["Simulacro"]
            == simulacro_sel
        ]

        if len(datos_filtrados) > 0:

            datos_sim = (
                datos_filtrados.iloc[0]
            )

            materias_grafica = []
            notas_grafica = []

            for materia in asignaturas:

                if materia not in datos_sim.index:
                    continue

                valor = datos_sim[materia]

                if pd.notna(valor):

                    materias_grafica.append(
                        materia
                    )

                    notas_grafica.append(
                        valor
                    )

            fig2, ax2 = plt.subplots(
                figsize=(12, 5)
            )

            ax2.bar(
                materias_grafica,
                notas_grafica
            )

            ax2.set_ylim(0, 100)

            ax2.set_ylabel(
                "Puntaje"
            )

            ax2.set_title(
                f"Resultados - {simulacro_sel}"
            )

            plt.xticks(rotation=30)

            st.pyplot(fig2)

        # =================================================
        # FORTALEZAS Y DEBILIDADES
        # =================================================
        st.subheader(
            "🔥 Fortalezas y Debilidades"
        )

        fortalezas = []
        debilidades = []

        materias_analisis = [

            "Matematicas_Genericos",
            "Matematicas_NoGenericos",

            "Quimica",
            "Fisica",
            "Biologia",
            "CTS",

            "Sociales",
            "Ciudadanas",

            "LecturaCritica",

            "Ingles"
        ]

        for materia in materias_analisis:

            if materia not in estudiante_df.columns:
                continue

            promedio = estudiante_df[
                materia
            ].mean()

            if pd.isna(promedio):
                continue

            if promedio >= 70:

                fortalezas.append(
                    f"{materia} ({round(promedio,2)})"
                )

            elif promedio < 55:

                debilidades.append(
                    f"{materia} ({round(promedio,2)})"
                )

        col1, col2 = st.columns(2)

        with col1:

            st.success("✅ Fortalezas")

            if fortalezas:

                for f in fortalezas:

                    st.write(f"• {f}")

            else:

                st.write(
                    "No se detectaron fortalezas."
                )

        with col2:

            st.error("⚠️ Debilidades")

            if debilidades:

                for d in debilidades:

                    st.write(f"• {d}")

            else:

                st.write(
                    "No se detectaron debilidades."
                )

        # =================================================
        # PREDICCIÓN ICFES
        # =================================================
        st.subheader(
            "🎯 Predicción Siguiente Prueba"
        )

        datos_pred = estudiante_df[
            ["NumeroPrueba", "Global"]
        ].dropna()

        if len(datos_pred) >= 2:

            x = datos_pred[
                "NumeroPrueba"
            ]

            y = datos_pred[
                "Global"
            ]

            pendiente, intercepto = np.polyfit(
                x,
                y,
                1
            )

            siguiente_prueba = (
                x.max() + 1
            )

            prediccion = (
                pendiente *
                siguiente_prueba
            ) + intercepto

            st.metric(

                label="Puntaje Global Estimado",

                value=round(
                    prediccion,
                    1
                )
            )

            # =============================
            # GRÁFICA
            # =============================
            fig3, ax3 = plt.subplots(
                figsize=(8, 4)
            )

            ax3.plot(
                x,
                y,
                marker="o"
            )

            ax3.plot(

                siguiente_prueba,

                prediccion,

                marker="X",
                markersize=12

            )

            ax3.set_title(
                "Predicción Global"
            )

            ax3.set_xlabel(
                "Prueba"
            )

            ax3.set_ylabel(
                "Global"
            )

            st.pyplot(fig3)

        else:

            st.warning(
                "Se necesitan al menos 2 pruebas para generar predicción."
            )

        # =================================================
        # GENERAR PDF
        # =================================================
        st.subheader(
            "📄 Generar Reporte PDF"
        )

        if st.button(
            "📥 Descargar Reporte"
        ):

            pdf = FPDF()

            pdf.add_page()

            pdf.set_font(
                "Arial",
                "B",
                16
            )

            pdf.cell(
                200,
                10,
                txt="Reporte Academico",
                ln=True,
                align="C"
            )

            pdf.ln(10)

            pdf.set_font(
                "Arial",
                "",
                12
            )

            pdf.cell(
                200,
                10,
                txt=f"Estudiante: {estudiante}",
                ln=True
            )

            pdf.ln(5)

            # =============================
            # TABLA
            # =============================
            for i, row in tabla_estudiante.iterrows():

                texto = (
                    f"{row['Simulacro']} | "
                    f"Global: {row.get('Global','')} | "
                    f"Posicion: {row.get('Posicion','')}"
                )

                pdf.cell(
                    200,
                    8,
                    txt=texto,
                    ln=True
                )

            pdf.ln(10)

            # =============================
            # FORTALEZAS
            # =============================
            pdf.set_font(
                "Arial",
                "B",
                13
            )

            pdf.cell(
                200,
                10,
                txt="Fortalezas",
                ln=True
            )

            pdf.set_font(
                "Arial",
                "",
                12
            )

            for f in fortalezas:

                pdf.cell(
                    200,
                    8,
                    txt=f,
                    ln=True
                )

            pdf.ln(5)

            # =============================
            # DEBILIDADES
            # =============================
            pdf.set_font(
                "Arial",
                "B",
                13
            )

            pdf.cell(
                200,
                10,
                txt="Debilidades",
                ln=True
            )

            pdf.set_font(
                "Arial",
                "",
                12
            )

            for d in debilidades:

                pdf.cell(
                    200,
                    8,
                    txt=d,
                    ln=True
                )

            pdf.ln(5)

            # =============================
            # PREDICCIÓN
            # =============================
            pdf.set_font(
                "Arial",
                "B",
                13
            )

            pdf.cell(
                200,
                10,
                txt="Prediccion Siguiente Prueba",
                ln=True
            )

            pdf.set_font(
                "Arial",
                "",
                12
            )

            if len(datos_pred) >= 2:

                pdf.cell(
                    200,
                    8,
                    txt=f"Puntaje estimado: {round(prediccion,1)}",
                    ln=True
                )

            # =============================
            # GUARDAR
            # =============================
            ruta_pdf = (
                f"Reporte_{estudiante}.pdf"
            )

            pdf.output(
                ruta_pdf
            )

            with open(
                ruta_pdf,
                "rb"
            ) as archivo_pdf:

                st.download_button(

                    label="⬇️ Descargar PDF",

                    data=archivo_pdf,

                    file_name=ruta_pdf,

                    mime="application/pdf"
                )


else:

    st.info(
        "👆 Sube archivos Excel para comenzar"
    )
