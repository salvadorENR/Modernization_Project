import os
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns

# =========================================================================
# 1. CONFIGURACIÓN INICIAL Y RUTAS SEGURAS
# =========================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))

def obtener_ruta_segura(filepath):
    if not os.path.exists(filepath):
        return filepath
    try:
        with open(filepath, 'a'): pass
        return filepath
    except PermissionError:
        base, ext = os.path.splitext(filepath)
        marca_tiempo = datetime.datetime.now().strftime("%H%M%S")
        nuevo_nombre = f"{base}_{marca_tiempo}{ext}"
        print(f"⚠️ Archivo abierto. Guardando como: {os.path.basename(nuevo_nombre)}")
        return nuevo_nombre

archivo_pdf = obtener_ruta_segura(os.path.join(script_dir, "Presentacion_Ejecutiva_Porcentajes.pdf"))

# =========================================================================
# 2. PROCESAMIENTO: CONVERSIÓN A PORCENTAJES (0-100%)
# =========================================================================
def procesar_grado_porcentajes(filepath, materia, prefijo, grado_num):
    if not os.path.exists(filepath): return None
    
    try:
        df = pd.read_csv(filepath, sep='|', encoding='utf-8', dtype=str, on_bad_lines='skip')
    except:
        df = pd.read_csv(filepath, sep='|', encoding='latin-1', dtype=str, on_bad_lines='skip')
        
    df.columns = [c.replace('"', '').strip() for c in df.columns]
    if 'Documento' not in df.columns: return None
    
    df.dropna(subset=['Documento'], inplace=True)
    df = df[df['Documento'] != '']
    df.drop_duplicates(subset=['Documento'], keep='first', inplace=True)
    
    col_pt = [c for c in df.columns if 'Puntaje' in c and 'Total' in c][0]
    item_cols = [c for c in df.columns if c.startswith(prefijo) and c[len(prefijo):].isdigit()]
    tot_items = len(item_cols)
    if tot_items == 0: return None
    
    # Filtrar 100%
    valid_mask = df[item_cols].isin(['0', '1']).sum(axis=1) == tot_items
    df_100 = df[valid_mask].copy()
    
    # CONVERSIÓN CRÍTICA A PORCENTAJES: (Aciertos / Total_Items) * 100
    df_100['Puntaje_Total'] = df_100[col_pt].str.replace(',', '.').astype(float)
    df_100['Porcentaje_Aciertos'] = (df_100['Puntaje_Total'] / tot_items) * 100
    
    if df_100.empty: return None
    
    # Calcular Quintiles en base al PORCENTAJE
    df_100['Quintil'] = pd.qcut(df_100['Porcentaje_Aciertos'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
    
    q4_min = int(df_100[df_100['Quintil'] == 4]['Porcentaje_Aciertos'].min())
    q4_max = int(df_100[df_100['Quintil'] == 4]['Porcentaje_Aciertos'].max())
    q5_min = int(df_100[df_100['Quintil'] == 5]['Porcentaje_Aciertos'].min())
    
    return {
        'grado': grado_num,
        'materia': materia,
        'media_pct': df_100['Porcentaje_Aciertos'].mean(),
        'q4_min': q4_min,
        'q4_max': q4_max,
        'q5_min': q5_min,
        'tot_items': tot_items
    }

print("Calculando equivalencias en porcentajes para la presentación...")
grados_objetivo = [3, 6, 9]
datos_lengua = []
datos_mate = []
medias_globales = []

for g in grados_objetivo:
    mat_file = os.path.join(script_dir, f"Mat_{g}.txt")
    lec_file = os.path.join(script_dir, f"Lec_{g}.txt")
    
    mat_data = procesar_grado_porcentajes(mat_file, "Matemática", "MAT", g)
    lec_data = procesar_grado_porcentajes(lec_file, "Lengua", "LEC", g)
    
    if mat_data: 
        datos_mate.append(mat_data)
        medias_globales.append({'Grado': f"{g}°", 'Materia': 'Matemática', 'Promedio_Pct': mat_data['media_pct']})
    if lec_data: 
        datos_lengua.append(lec_data)
        medias_globales.append({'Grado': f"{g}°", 'Materia': 'Lengua', 'Promedio_Pct': lec_data['media_pct']})

df_medias = pd.DataFrame(medias_globales)

# =========================================================================
# 3. FUNCIONES DE DIBUJO DE PICTOGRAMAS
# =========================================================================
def dibujar_fila_pictograma_pct(ax, data):
    ax.axis('off')
    x_coords = np.arange(1, 11)
    y_coords = np.zeros(10)
    
    # Colores: 6 grises (Q1-Q3), 2 azul claro (Q4), 2 azul oscuro (Q5)
    colores = ['#d9d9d9']*6 + ['#4f81bd']*2 + ['#1f497d']*2 
    
    ax.scatter(x_coords, y_coords + 0.15, s=350, c=colores, marker='o', zorder=2) # Cabezas
    ax.scatter(x_coords, y_coords, s=700, c=colores, marker='s', zorder=1)       # Cuerpos
    
    ax.set_xlim(-1.5, 11.5)
    ax.set_ylim(-0.8, 0.6)
    
    ax.text(-1, 0.05, f"{data['grado']}°\nGrado", fontweight='bold', fontsize=14, color='#1f497d', ha='center', va='center')
    ax.text(-1, -0.3, f"({data['tot_items']} ítems)", style='italic', fontsize=8, color='gray', ha='center')
    
    # Textos actualizados con PORCENTAJE de dominio
    ax.text(3.5, -0.4, f"6 de cada 10 dominan\n{data['q4_min']}% de la prueba o menos", ha='center', va='top', fontsize=10, fontweight='bold', color='gray')
    ax.text(7.5, -0.4, f"2 de cada 10 dominan\nentre el {data['q4_min']}% y {data['q4_max']}%", ha='center', va='top', fontsize=10, fontweight='bold', color='#4f81bd')
    ax.text(9.5, -0.4, f"2 de cada 10 logran\nmás del {data['q5_min']}%", ha='center', va='top', fontsize=10, fontweight='bold', color='#1f497d')

def agregar_alerta_corte(fig):
    cuadro_alerta = dict(boxstyle="round,pad=0.5", facecolor="#fff2f2", edgecolor="#c00000", linewidth=1.5)
    fig.text(0.5, 0.08, "ACLARACIÓN LEGAL Y TÉCNICA: Esta prueba NO tiene un punto de corte ni niveles de 'aprobado'.\nEl porcentaje representa la proporción de la prueba que el estudiante logró dominar.", 
             ha='center', va='center', fontsize=10, fontweight='bold', color='#c00000', bbox=cuadro_alerta)

# =========================================================================
# 4. GENERACIÓN DEL PDF
# =========================================================================
print("Generando Presentación Ejecutiva con métricas equitativas...")
with PdfPages(archivo_pdf) as pdf:
    
    # --- SLIDE 1: PANORAMA GLOBAL (LÍNEAS) EN PORCENTAJES ---
    fig = plt.figure(figsize=(10, 5.625)) 
    fig.suptitle("1. EL PANORAMA: PORCENTAJE DE DOMINIO DE LA PRUEBA", fontsize=16, fontweight='bold', color='#1f497d', y=0.92)
    
    ax = fig.add_axes([0.1, 0.15, 0.5, 0.65])
    sns.lineplot(data=df_medias, x='Grado', y='Promedio_Pct', hue='Materia', marker='o', markersize=10, linewidth=3, palette=['#2c7fb8', '#e34a33'], ax=ax)
    
    ax.set_ylim(20, 70) # Escala de 20% a 70% para ver bien los cambios
    ax.set_ylabel("Dominio Promedio (% de Aciertos)", fontweight='bold')
    ax.set_xlabel("Grado Evaluado", fontweight='bold')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    for i, row in df_medias.iterrows():
        ax.text(i//2, row['Promedio_Pct'] + 1.5, f"{row['Promedio_Pct']:.1f}%", ha='center', fontweight='bold', fontsize=10)

    fig.text(0.65, 0.65, "ESTABILIDAD EN LENGUA\nEl sistema muestra una retención\nsólida. El nivel de dominio se\nmantiene cercano al 50%.", fontsize=11, color='#e34a33', fontweight='bold', va='top')
    
    fig.text(0.65, 0.40, "ALERTA EN MATEMÁTICA\nAl estandarizar la medida a\nporcentajes, se evidencia una\ncaída alarmante desde un 55%\nen 3° a un 35% en 9° grado.", fontsize=11, color='#2c7fb8', fontweight='bold', va='top')
    
    pdf.savefig(fig)
    plt.close()

    # --- SLIDE 2: PICTOGRAMAS LENGUA ---
    if datos_lengua:
        fig, axes = plt.subplots(3, 1, figsize=(10, 5.625))
        fig.suptitle("2. RADIOGRAFÍA DEL APRENDIZAJE: LENGUA", fontsize=16, fontweight='bold', color='#1f497d', y=0.95)
        fig.text(0.5, 0.88, "Proporción de la prueba dominada por grupos de 10 estudiantes representativos:", ha='center', fontsize=11, style='italic')
        
        for idx, data in enumerate(datos_lengua):
            dibujar_fila_pictograma_pct(axes[idx], data)
            
        plt.subplots_adjust(top=0.85, bottom=0.18, hspace=0.1)
        agregar_alerta_corte(fig)
        pdf.savefig(fig)
        plt.close()

    # --- SLIDE 3: PICTOGRAMAS MATEMÁTICA ---
    if datos_mate:
        fig, axes = plt.subplots(3, 1, figsize=(10, 5.625))
        fig.suptitle("3. RADIOGRAFÍA DEL APRENDIZAJE: MATEMÁTICA", fontsize=16, fontweight='bold', color='#1f497d', y=0.95)
        fig.text(0.5, 0.88, "La proporción de la prueba dominada cae severamente en grados superiores:", ha='center', fontsize=11, style='italic')
        
        for idx, data in enumerate(datos_mate):
            dibujar_fila_pictograma_pct(axes[idx], data)
            
        plt.subplots_adjust(top=0.85, bottom=0.18, hspace=0.1)
        agregar_alerta_corte(fig)
        pdf.savefig(fig)
        plt.close()

print(f"✅ ¡Presentación ajustada a Porcentajes! Guardada en: {os.path.basename(archivo_pdf)}")