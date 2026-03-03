import os
import pandas as pd

# =========================================================================
# 1. CONFIGURACIÓN INICIAL
# =========================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
archivo_excel = os.path.join(script_dir, "Participacion_Mayor_60_Porciento.xlsx")

def calcular_participacion_60(filepath, materia, prefijo, grado_num):
    if not os.path.exists(filepath): return None
    
    # 1. Leer el archivo original
    try:
        df = pd.read_csv(filepath, sep='|', encoding='utf-8', dtype=str, on_bad_lines='skip')
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, sep='|', encoding='latin-1', dtype=str, on_bad_lines='skip')
        
    df.columns = [c.replace('"', '').strip() for c in df.columns]
    if 'Documento' not in df.columns: return None
    
    # 2. Limpieza básica para tener los Registrados Reales
    df.dropna(subset=['Documento'], inplace=True)
    df = df[df['Documento'] != '']
    df.drop_duplicates(subset=['Documento'], keep='first', inplace=True)
    
    total_registrados = len(df)
    if total_registrados == 0: return None
    
    # 3. Identificar SOLO las columnas de los ítems (las preguntas)
    item_cols = [c for c in df.columns if c.startswith(prefijo) and c[len(prefijo):].isdigit()]
    tot_items = len(item_cols)
    if tot_items == 0: return None
    
    # ==========================================
    # 4. CÁLCULO DE PREGUNTAS RESPONDIDAS (Sin importar si están bien o mal)
    # ==========================================
    min_respuestas_60 = tot_items * 0.60
    
    # Contar cuántas preguntas respondió cada estudiante. 
    # (Un '0' es incorrecta y '1' es correcta, pero en ambos casos significa que SÍ la respondió)
    preguntas_respondidas_por_alumno = df[item_cols].isin(['0', '1']).sum(axis=1)
    
    # Filtrar a los estudiantes que respondieron esa cantidad mínima de preguntas
    estudiantes_60_mas = len(df[preguntas_respondidas_por_alumno >= min_respuestas_60])
    
    # Calcular porcentaje sobre el UNIVERSO TOTAL DE REGISTRADOS
    porcentaje_participacion = (estudiantes_60_mas / total_registrados) * 100
    
    return {
        'Grado': f"{grado_num}°",
        'Materia': materia,
        'Total Ítems en Prueba': tot_items,
        'Mínimo a Responder (60%)': round(min_respuestas_60, 1),
        'Total Estudiantes Registrados': total_registrados,
        'Estudiantes que Respondieron >= 60%': estudiantes_60_mas,
        'Porcentaje de Participación (%)': f"{porcentaje_participacion:.1f}%"
    }

# =========================================================================
# 2. PROCESAR TODOS LOS GRADOS
# =========================================================================
print("Procesando datos para calcular estudiantes que RESPONDIERON al menos el 60%...\n")
resultados = []

for grado in range(3, 12):
    mat_file = os.path.join(script_dir, f"Mat_{grado}.txt")
    lec_file = os.path.join(script_dir, f"Lec_{grado}.txt")
    
    # Evaluar Matemática
    if os.path.exists(mat_file):
        res_mat = calcular_participacion_60(mat_file, "Matemática", "MAT", grado)
        if res_mat: resultados.append(res_mat)
            
    # Evaluar Lengua
    if os.path.exists(lec_file):
        res_lec = calcular_participacion_60(lec_file, "Lengua", "LEC", grado)
        if res_lec: resultados.append(res_lec)

# =========================================================================
# 3. GENERAR REPORTE EN EXCEL
# =========================================================================
if resultados:
    df_resultados = pd.DataFrame(resultados)
    
    print("=========================================================================================")
    print("      ESTUDIANTES QUE RESPONDIERON >= 60% DE LA PRUEBA (SOBRE MATRÍCULA REGISTRADA)")
    print("=========================================================================================")
    print(df_resultados.to_string(index=False))
    print("=========================================================================================\n")
    
    try:
        with pd.ExcelWriter(archivo_excel, engine='openpyxl') as writer:
            df_resultados.to_excel(writer, sheet_name='Participacion_60_Porciento', index=False)
        print(f"✅ Archivo Excel exportado con éxito en: {os.path.basename(archivo_excel)}")
    except PermissionError:
        print("⚠️ Error: El archivo Excel está abierto. Ciérralo y vuelve a correr el script.")
    except ModuleNotFoundError:
        print("⚠️ Falta 'openpyxl'. Instálalo con: pip install openpyxl")
else:
    print("❌ No se encontraron bases de datos (txt) para procesar.")