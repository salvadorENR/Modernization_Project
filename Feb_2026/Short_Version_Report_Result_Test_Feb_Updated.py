import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns

# =========================================================================
# 1. CONFIGURACIÓN INICIAL Y DIRECTORIOS
# =========================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
dir_pdf = os.path.join(script_dir, "Reporte_Focalizado")
os.makedirs(dir_pdf, exist_ok=True)

archivo_pdf = os.path.join(dir_pdf, "Reporte_3_6_9_Verde.pdf")
archivo_matricula = os.path.join(script_dir, "Matricula_Est_Modernizacion.txt")

# Grados a analizar
GRADOS_FOCO = [3, 6, 9]
COLOR_ALCANZO = '#ADD8E6' # Celeste
COLOR_NO_ALCANZO = '#22c55e' # Verde

# --- DICCIONARIO DE ÍTEMS A OMITIR ---
ITEMS_A_ELIMINAR = {
    'Matemática': {
        3: ['MAT3992'],
        6: ['MAT4077'],
        9: [] 
    },
    'Lengua': {
        3: ['LEC3154', 'LEC3157', 'LEC3168'],
        6: ['LEC3262', 'LEC3267'],
        9: []
    }
}

# =========================================================================
# 2. FUNCIONES DE DIBUJO Y FORMATO (PICTOGRAMAS Y TABLAS)
# =========================================================================
def draw_silhouette(ax, x_offset, y_offset, face_color, edge_color, line_width):
    head = patches.Circle((x_offset, y_offset + 1.6), 0.2, linewidth=line_width, 
                          edgecolor=edge_color, facecolor=face_color, zorder=2)
    ax.add_patch(head)
    body_coords = [
        (x_offset - 0.2, y_offset + 0.5), 
        (x_offset + 0.2, y_offset + 0.5), 
        (x_offset + 0.25, y_offset + 1.4), 
        (x_offset - 0.25, y_offset + 1.4), 
    ]
    body = patches.Polygon(body_coords, closed=True, linewidth=line_width, 
                           edgecolor=edge_color, facecolor=face_color, 
                           joinstyle='round', zorder=1)
    ax.add_patch(body)

def format_table_cobertura(ax, df, title=""):
    ax.axis('tight')
    ax.axis('off')
    if title:
        ax.set_title(title, fontweight='bold', pad=20, fontsize=16, color='darkblue')
    
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 3.5) 
    
    col_widths = [0.08, 0.18, 0.18, 0.18, 0.19, 0.19] 
    for (row, col), cell in table.get_celld().items():
        cell.set_width(col_widths[col])
        if row == 0:
            cell.set_facecolor('darkblue')
            cell.get_text().set_color('white')
            cell.get_text().set_fontweight('bold')

# =========================================================================
# 3. FUNCIONES DE LECTURA Y PROCESAMIENTO
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

def procesar_foco(df_raw, materia, prefijo, grado_num):
    if df_raw is None or df_raw.empty: return None, 0
    items_elim = ITEMS_A_ELIMINAR.get(materia, {}).get(grado_num, [])
    if items_elim:
        cols_to_drop = [c for c in items_elim if c in df_raw.columns]
        if cols_to_drop:
            df_raw.drop(columns=cols_to_drop, inplace=True)

    item_cols = [c for c in df_raw.columns if c.startswith(prefijo) and c[len(prefijo):].isdigit()]
    tot_items_validos = len(item_cols)
    if tot_items_validos == 0: return None, 0
    
    valid_mask = df_raw[item_cols].isin(['0', '1']).sum(axis=1) == tot_items_validos
    df_100 = df_raw[valid_mask].copy()
    if df_100.empty: return None, 0
    
    df_100['Puntaje_Total'] = df_100[item_cols].astype(int).sum(axis=1)
    umbral_60 = tot_items_validos * 0.6
    pct_60 = (df_100['Puntaje_Total'] >= umbral_60).mean() * 100
    x_de_10 = int(round(pct_60 / 10))
    if x_de_10 == 0 and pct_60 > 0: x_de_10 = 1 
    
    media = df_100['Puntaje_Total'].mean()
    sd = df_100['Puntaje_Total'].std(ddof=1)
    if pd.isna(sd) or sd == 0: sd = 1
    
    df_100['Z_Score'] = (df_100['Puntaje_Total'] - media) / sd
    df_100['Puntaje_Transformado'] = df_100['Z_Score'] + 5
    
    df_temp = df_100[['Documento', 'Puntaje_Transformado']].copy()
    df_temp['Materia'] = materia
    df_temp['Grado_Num'] = grado_num
    
    return df_temp, x_de_10

# =========================================================================
# 4. PROCESAMIENTO DE DATOS DE PRUEBA
# =========================================================================
print("\nIniciando Análisis Focalizado VERDE (3°, 6°, 9°)...")

df_global_estand = pd.DataFrame()
datos_pictogramas = {'Matemática': {}, 'Lengua': {}}

for grado in GRADOS_FOCO:
    archivo_mat = os.path.join(script_dir, f"Mat_{grado}.txt")
    archivo_lec = os.path.join(script_dir, f"Lec_{grado}.txt")
    
    df_mat_raw = leer_y_limpiar(archivo_mat)
    df_mat_clean, aprobados_mat = procesar_foco(df_mat_raw, "Matemática", "MAT", grado)
    if df_mat_clean is not None:
        df_global_estand = pd.concat([df_global_estand, df_mat_clean], ignore_index=True)
        datos_pictogramas['Matemática'][grado] = aprobados_mat

    df_lec_raw = leer_y_limpiar(archivo_lec)
    df_lec_clean, aprobados_lec = procesar_foco(df_lec_raw, "Lengua", "LEC", grado)
    if df_lec_clean is not None:
        df_global_estand = pd.concat([df_global_estand, df_lec_clean], ignore_index=True)
        datos_pictogramas['Lengua'][grado] = aprobados_lec

# =========================================================================
# 5. PROCESAMIENTO DE MATRÍCULA DEL PROYECTO
# =========================================================================
df_cobertura = pd.DataFrame()
if os.path.exists(archivo_matricula):
    try:
        df_matricula = pd.read_csv(archivo_matricula, sep='\t', encoding='utf-8')
    except UnicodeDecodeError:
        df_matricula = pd.read_csv(archivo_matricula, sep='\t', encoding='latin-1')
        
    df_matricula.columns = [str(c).strip() for c in df_matricula.columns]
    
    datos_cob = []
    for grado in GRADOS_FOCO:
        # Calcular el total de estudiantes matriculados en ESTE proyecto contando las filas por Grade
        if 'Grade' in df_matricula.columns:
            total_matriculados = len(df_matricula[df_matricula['Grade'].astype(str) == str(grado)])
        else:
            total_matriculados = 0
            
        completos_mat = len(df_global_estand[(df_global_estand['Grado_Num'] == grado) & (df_global_estand['Materia'] == 'Matemática')])
        completos_lec = len(df_global_estand[(df_global_estand['Grado_Num'] == grado) & (df_global_estand['Materia'] == 'Lengua')])
        
        tasa_mat = (completos_mat / total_matriculados * 100) if total_matriculados > 0 else 0
        tasa_lec = (completos_lec / total_matriculados * 100) if total_matriculados > 0 else 0
        
        datos_cob.append({
            'Grado': f"{grado}°",
            'Total de estudiantes\nmatriculados': f"{int(total_matriculados):,}",
            '100% Completos\n(Matemática)': f"{completos_mat:,}",
            '100% Completos\n(Lengua)': f"{completos_lec:,}",
            'Tasa de Cobertura\nMatemática': f"{tasa_mat:.1f}%",
            'Tasa de Cobertura\nLengua': f"{tasa_lec:.1f}%"
        })
        
    df_cobertura = pd.DataFrame(datos_cob)
else:
    print(f"Advertencia: No se encontró {archivo_matricula}.")

# =========================================================================
# 6. GENERACIÓN DEL PDF
# =========================================================================
print("Generando PDF Verde...")

with PdfPages(archivo_pdf) as pdf:
    
    # ---------------------------------------------------------------------
    # SLIDE 1: BOXPLOTS 
    # ---------------------------------------------------------------------
    fig = plt.figure(figsize=(11, 8.5))
    fig.suptitle("DISTRIBUCIÓN DE PUNTAJES: 3°, 6° Y 9° GRADO", fontsize=22, fontweight='bold', color='darkblue', y=0.95)
    
    txt_bp = ("El gráfico muestra los resultados de los estudiantes en una escala ajustada donde 5 es el puntaje promedio.\n"
              "Cada caja gris señala dónde se concentra la mayor parte de las calificaciones de quienes completaron toda la prueba.")
    fig.text(0.5, 0.88, txt_bp, ha='center', va='center', fontsize=12)
    
    if not df_global_estand.empty:
        axes = [fig.add_axes([0.1, 0.50, 0.8, 0.30]), fig.add_axes([0.1, 0.08, 0.8, 0.30])]
        
        for i, mat in enumerate(['Matemática', 'Lengua']):
            ax = axes[i]
            df_plot = df_global_estand[df_global_estand['Materia'] == mat]
            if not df_plot.empty:
                sns.boxplot(data=df_plot, x='Grado_Num', y='Puntaje_Transformado', color='gray', ax=ax, order=GRADOS_FOCO)
                ax.set_title(f"Distribución {mat.upper()} (Z+5)", fontweight='bold', pad=10)
                ax.set_xlabel("Grado Analizado")
                ax.set_ylabel("Puntaje Estandarizado")
                ax.set_ylim(0, 10)
                ax.grid(axis='y', linestyle='--', alpha=0.7)
                
    pdf.savefig(fig)
    plt.close()

    # ---------------------------------------------------------------------
    # SLIDE 2: PICTOGRAMAS (VERDE)
    # ---------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 8.5))
    fig.suptitle("REPRESENTACIÓN GRÁFICA DE DESEMPEÑO (60%+)", fontsize=20, fontweight='bold', color='darkblue', y=0.96)
    
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 20) 
    ax.axis('off')
    
    legend_y = 17.5 
    draw_silhouette(ax, x_offset=2.5, y_offset=legend_y, face_color=COLOR_ALCANZO, edge_color='black', line_width=1)
    ax.text(3.0, legend_y + 1.15, "Alcanzó al menos el 60% de ítems válidos", va='center', ha='left', fontsize=10)
    draw_silhouette(ax, x_offset=11.0, y_offset=legend_y, face_color=COLOR_NO_ALCANZO, edge_color='black', line_width=1)
    ax.text(11.5, legend_y + 1.15, "No alcanzó el 60%", va='center', ha='left', fontsize=10)
    
    def dibujar_bloque_materia(ax, materia, y_title, y_rows):
        ax.text(0.5, y_title, f"ÁREA: {materia.upper()}", fontsize=14, fontweight='bold', color='#b91c1c', ha='left')
        for idx, grado in enumerate(GRADOS_FOCO):
            y_pos = y_rows[idx]
            ax.text(1.2, y_pos + 1.15, f"Grado {grado}°", va='center', ha='right', fontsize=11, fontweight='bold', color='#1e293b')
            aprobados = datos_pictogramas[materia].get(grado, 0)
            
            for j in range(10):
                x_off = 2.0 + j * 0.8
                color = COLOR_ALCANZO if j < aprobados else COLOR_NO_ALCANZO
                draw_silhouette(ax, x_offset=x_off, y_offset=y_pos, face_color=color, edge_color='black', line_width=1)
            
            frase = f"{aprobados} de cada 10 estudiantes\nfueron capaces de responder\ncorrectamente al menos el\n60% de los ítems válidos."
            ax.text(10.2, y_pos + 1.15, frase, va='center', ha='left', fontsize=9, color='#002d5a', style='italic')

    dibujar_bloque_materia(ax, "Matemática", y_title=15.5, y_rows=[13.5, 11.5, 9.5])
    ax.hlines(y=8.2, xmin=0.5, xmax=15.5, color='#cbd5e1', linewidth=1.5, linestyle='-')
    dibujar_bloque_materia(ax, "Lengua", y_title=6.8, y_rows=[4.8, 2.8, 0.8])

    pdf.savefig(fig)
    plt.close()

    # ---------------------------------------------------------------------
    # SLIDE 3: TASA DE COBERTURA
    # ---------------------------------------------------------------------
    fig = plt.figure(figsize=(11, 8.5))
    fig.suptitle("TASA DE COBERTURA DE LA EVALUACIÓN", fontsize=22, fontweight='bold', color='darkblue', y=0.92)
    
    txt_cob = ("Comparativa entre el total de estudiantes matriculados en el proyecto\n"
               "y el total de estudiantes que respondieron el 100% de los ítems válidos en cada prueba.")
    fig.text(0.5, 0.83, txt_cob, ha='center', va='center', fontsize=12)

    if not df_cobertura.empty:
        ax_cob = fig.add_axes([0.02, 0.30, 0.96, 0.40])
        format_table_cobertura(ax_cob, df_cobertura, "Análisis de Cobertura (Matemática y Lengua)")
    else:
        fig.text(0.5, 0.5, "Archivo de matrícula no encontrado.", ha='center', va='center', fontsize=14, color='red')

    pdf.savefig(fig)
    plt.close()

print(f"✅ Proceso completado. PDF focalizado guardado en: {archivo_pdf}")