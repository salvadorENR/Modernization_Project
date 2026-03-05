import os
import pandas as pd

# =========================================================================
# 1. CONFIGURACIÓN INICIAL Y DIRECTORIOS
# =========================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))

# --- DICCIONARIO DE ÍTEMS A OMITIR (Los que fallaron en el análisis psicométrico) ---
ITEMS_A_ELIMINAR = {
    'Matemática': {
        3: ['MAT3992'],
        4: ['MAT3998', 'MAT4025', 'MAT4027'],
        5: ['MAT4039', 'MAT4043', 'MAT4044', 'MAT4050', 'MAT4055'],
        6: ['MAT4077'],
        7: ['MAT4112'],
        10: ['MAT4198', 'MAT4199', 'MAT4200', 'MAT4202', 'MAT4215'],
        11: ['MAT4228']
    },
    'Lengua': {
        3: ['LEC3154', 'LEC3157', 'LEC3168'],
        4: ['LEC3193', 'LEC3207'],
        6: ['LEC3262', 'LEC3267'],
        8: ['LEC3312'],
        10: ['LEC3366']
    }
}

# --- DISEÑO DE LA PRUEBA (Blueprint Oficial: Cantidad de ítems a evaluar por grado) ---
ITEMS_ORIGINALES = {
    'Matemática': {3: 25, 4: 25, 5: 30, 6: 30, 7: 30, 8: 30, 9: 30, 10: 30, 11: 30},
    'Lengua': {3: 25, 4: 25, 5: 30, 6: 30, 7: 30, 8: 30, 9: 30, 10: 30, 11: 30}
}

# =========================================================================
# 2. FUNCIONES DE LECTURA Y PROCESAMIENTO
# =========================================================================
def leer_y_limpiar(filepath):
    if not os.path.exists(filepath): return None
    try:
        df = pd.read_csv(filepath, sep='|', encoding='utf-8', dtype=str, on_bad_lines='skip')
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, sep='|', encoding='latin-1', dtype=str, on_bad_lines='skip')
    df.columns = [c.replace('"', '').strip() for c in df.columns]
    if 'Documento' not in df.columns: return None
    df['Documento'] = df['Documento'].str.strip()
    df.dropna(subset=['Documento'], inplace=True)
    df = df[df['Documento'] != '']
    df.drop_duplicates(subset=['Documento'], keep='first', inplace=True)
    return df

def procesar_desempeno_grado(df_raw, materia, prefijo, grado_num):
    if df_raw is None or df_raw.empty: return None
    
    # 1. Identificar TODAS las columnas de ítems en el archivo bruto
    item_cols_raw = [c for c in df_raw.columns if c.startswith(prefijo) and c[len(prefijo):].isdigit()]
    
    # 2. Recortar a la longitud oficial (ignora ítems piloto/ancla al final de la base de datos)
    max_items = ITEMS_ORIGINALES.get(materia, {}).get(grado_num, len(item_cols_raw))
    item_cols_oficiales = item_cols_raw[:max_items]
    
    # 3. Quitar los ítems que mostraron problemas psicométricos
    items_elim = ITEMS_A_ELIMINAR.get(materia, {}).get(grado_num, [])
    item_cols_validos = [c for c in item_cols_oficiales if c not in items_elim]
    
    tot_items_validos = len(item_cols_validos)
    if tot_items_validos == 0: return None
    
    # 4. Filtrar solo a los estudiantes que completaron el 100% de los ítems VÁLIDOS
    valid_mask = df_raw[item_cols_validos].isin(['0', '1']).sum(axis=1) == tot_items_validos
    df_100 = df_raw[valid_mask].copy()
    
    tot_100_completos = len(df_100)
    if tot_100_completos == 0: return None

    # 5. Calcular puntajes y superación del umbral
    df_100['Puntaje_Total'] = df_100[item_cols_validos].astype(int).sum(axis=1)
    
    umbral_60_num = tot_items_validos * 0.6
    
    # Verificación matemática estricta: Puntaje / Válidos >= 60%
    pct_aciertos = df_100['Puntaje_Total'] / tot_items_validos
    estudiantes_60_mas = (pct_aciertos >= 0.5999).sum() 
    
    tasa_exito = (estudiantes_60_mas / tot_100_completos) * 100
    
    # 6. Proporción de cada 10
    x_de_10 = int(round(tasa_exito / 10))
    if x_de_10 == 0 and tasa_exito > 0: x_de_10 = 1 
    
    frase_desempeno = f"{x_de_10} de cada 10 estudiantes"
    
    return {
        'Grado': f"{grado_num}°",
        'Ítems Válidos': tot_items_validos,
        'Umbral 60%': f"{umbral_60_num:.1f}",
        'Estudiantes 100% Completos': f"{tot_100_completos:,}",
        'Aciertos >= 60%': f"{estudiantes_60_mas:,}",
        'Tasa (>= 60%)': f"{tasa_exito:.1f}%",
        'Lectura de Desempeño': frase_desempeno
    }

# =========================================================================
# 3. PROCESAMIENTO DE DATOS Y SALIDA POR CONSOLA
# =========================================================================
print("Procesando archivos de texto aplicando Blueprint oficial...\n")
datos_desempeno_mat = []
datos_desempeno_lec = []

for grado_num in range(3, 12):
    archivo_mat = os.path.join(script_dir, f"Mat_{grado_num}.txt")
    archivo_lec = os.path.join(script_dir, f"Lec_{grado_num}.txt")
    
    df_mat_raw = leer_y_limpiar(archivo_mat)
    df_lec_raw = leer_y_limpiar(archivo_lec)
    
    datos_mat = procesar_desempeno_grado(df_mat_raw, "Matemática", "MAT", grado_num)
    if datos_mat: datos_desempeno_mat.append(datos_mat)
        
    datos_lec = procesar_desempeno_grado(df_lec_raw, "Lengua", "LEC", grado_num)
    if datos_lec: datos_desempeno_lec.append(datos_lec)

# =========================================================================
# 4. IMPRESIÓN DE TABLAS EN CONSOLA
# =========================================================================
# Ajustar la visualización de Pandas para que las columnas se vean completas en consola
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', None)

print("="*120)
print(" " * 40 + "MATEMÁTICA: ANÁLISIS DE SUPERACIÓN DEL UMBRAL")
print("="*120)
if datos_desempeno_mat:
    df_mat = pd.DataFrame(datos_desempeno_mat)
    print(df_mat.to_string(index=False, justify='center'))
else:
    print("No se encontraron datos procesables para Matemática.")

print("\n\n" + "="*120)
print(" " * 42 + "LENGUA: ANÁLISIS DE SUPERACIÓN DEL UMBRAL")
print("="*120)
if datos_desempeno_lec:
    df_lec = pd.DataFrame(datos_desempeno_lec)
    print(df_lec.to_string(index=False, justify='center'))
else:
    print("No se encontraron datos procesables para Lengua.")

print("\n" + "="*120)
print("✅ Cálculos de desempeño procesados correctamente según la estructura oficial.")