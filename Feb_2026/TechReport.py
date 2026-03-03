import os
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns

# =========================================================================
# 1. CONFIGURACIÓN INICIAL Y DIRECTORIOS
# =========================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))
dir_txt = os.path.join(script_dir, "Analisis_Diagnostico")
dir_pdf = os.path.join(script_dir, "Reporte_Tecnico")

os.makedirs(dir_txt, exist_ok=True)
os.makedirs(dir_pdf, exist_ok=True)

archivo_pdf = os.path.join(dir_pdf, "Reporte_Tecnico_100_Completos.pdf")
archivo_txt_global = os.path.join(dir_txt, "Reporte_Completitud_100.txt")

global_totals = {
    'Matemática': {'Registrados': 0, '100%_Completos': 0},
    'Lengua': {'Registrados': 0, '100%_Completos': 0}
}
df_global_estand = pd.DataFrame()

with open(archivo_txt_global, 'w', encoding='utf-8') as f:
    f.write("=================================================================\n")
    f.write(" REPORTE DE COMPLETITUD Y FILTRADO 100% (ANÁLISIS INDEPENDIENTE)\n")
    f.write("=================================================================\n\n")

def print_txt(texto):
    print(texto, end='')
    with open(archivo_txt_global, 'a', encoding='utf-8') as f:
        f.write(texto)

# =========================================================================
# 2. FUNCIONES DE PROCESAMIENTO
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
    if 'Centro' in df.columns:
        df['Centro'] = df['Centro'].str.strip().replace('', 'DESCONOCIDO').fillna('DESCONOCIDO')
    else:
        df['Centro'] = 'DESCONOCIDO'
        
    df.dropna(subset=['Documento'], inplace=True)
    df = df[df['Documento'] != '']
    df.drop_duplicates(subset=['Documento'], keep='first', inplace=True)
    return df

def procesar_100_porciento(df, materia, prefijo):
    if df is None or df.empty: return None
        
    col_pt = [c for c in df.columns if 'Puntaje' in c and 'Total' in c]
    if not col_pt: return None
    col_pt = col_pt[0]
    
    item_cols = [c for c in df.columns if c.startswith(prefijo) and c[len(prefijo):].isdigit()]
    tot_items = len(item_cols)
    if tot_items == 0: return None
    
    valid_mask = df[item_cols].isin(['0', '1']).sum(axis=1) == tot_items
    df_100 = df[valid_mask].copy()
    
    df_100['Puntaje_Total'] = df_100[col_pt].str.replace(',', '.').astype(float)
    
    tot_inicial = len(df)
    tot_final = len(df_100)
    pct = (tot_final / tot_inicial) * 100 if tot_inicial > 0 else 0
    
    global_totals[materia]['Registrados'] += tot_inicial
    global_totals[materia]['100%_Completos'] += tot_final
    
    print_txt(f" [{materia.upper()}]\n")
    print_txt(f"   - Total de ítems en la prueba : {tot_items}\n")
    print_txt(f"   - Estudiantes Registrados     : {tot_inicial:,}\n")
    print_txt(f"   - Completaron el 100%         : {tot_final:,} ({pct:.1f}%)\n\n")
    
    participacion = {'Registrados': tot_inicial, 'Completos': tot_final, 'Pct': pct}
    return {'df': df_100, 'items': item_cols, 'participacion': participacion}

def extraer_metricas(datos_obj, materia, grado_num):
    global df_global_estand
    if datos_obj is None or datos_obj['df'].empty: return None
    
    df_100 = datos_obj['df']
    item_cols = datos_obj['items']
    participacion = datos_obj['participacion']
    
    media = df_100['Puntaje_Total'].mean()
    sd = df_100['Puntaje_Total'].std(ddof=1)
    if pd.isna(sd) or sd == 0: sd = 1
    
    df_100['Z_Score'] = (df_100['Puntaje_Total'] - media) / sd
    df_100['Puntaje_Transformado'] = df_100['Z_Score'] + 5
    
    df_temp = df_100[['Centro', 'Documento', 'Puntaje_Transformado']].copy()
    df_temp['Materia'] = materia
    df_temp['Grado_Num'] = grado_num
    df_global_estand = pd.concat([df_global_estand, df_temp], ignore_index=True)
    
    desc = pd.DataFrame([{
        'Materia': materia,
        'N (100%)': f"{len(df_100):,}",
        'Media': round(media, 2),
        'Mediana': df_100['Puntaje_Total'].median(),
        'DS': round(sd, 2),
        'Mínimo': df_100['Puntaje_Total'].min(),
        'Máximo': df_100['Puntaje_Total'].max()
    }])
    
    df_100['Quintil'] = pd.qcut(df_100['Puntaje_Total'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
    quint_list = []
    for q, g in df_100.groupby('Quintil', observed=True):
        quint_list.append({
            'Materia': materia,
            'Quintil': q,
            'Rango': f"{g['Puntaje_Total'].min():.1f} - {g['Puntaje_Total'].max():.1f}",
            'N': f"{len(g):,}",
            '%': f"{(len(g) / len(df_100) * 100):.1f}%"
        })
    quint = pd.DataFrame(quint_list)
    
    esc_z = df_100.groupby('Centro')['Puntaje_Total'].mean().reset_index()
    esc_mean = esc_z['Puntaje_Total'].mean()
    esc_sd = esc_z['Puntaje_Total'].std(ddof=1)
    if pd.isna(esc_sd) or esc_sd == 0: esc_sd = 1
    esc_z['Z_Score'] = (esc_z['Puntaje_Total'] - esc_mean) / esc_sd
    
    dif_series = (df_100[item_cols] == '1').mean() * 100
    dif = pd.DataFrame({'Item': dif_series.index, 'Pct': dif_series.values})
    
    return {'desc': desc, 'quint': quint, 'esc_z': esc_z, 'dif': dif, 'part': participacion}

# =========================================================================
# 3. CREACIÓN DEL PDF CON DISEÑO CORREGIDO
# =========================================================================
def format_table(ax, df, title):
    ax.axis('tight')
    ax.axis('off')
    ax.set_title(title, fontweight='bold', pad=12, fontsize=12)
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.7) 
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor('darkblue')
            cell.get_text().set_color('white')
            cell.get_text().set_fontweight('bold')

print("\nIniciando Análisis 100% Independiente y compilación de PDF...\n")

with PdfPages(archivo_pdf) as pdf:
    # --- PORTADA ---
    fig = plt.figure(figsize=(11, 8.5))
    plt.axis('off')
    plt.text(0.5, 0.65, "RESULTADOS DE LA APLICACIÓN CONOCIENDO MIS LOGROS", ha='center', va='center', fontsize=24, fontweight='bold', color='darkblue')
    plt.text(0.5, 0.55, "APLICACIÓN FEBRERO DE 2026", ha='center', va='center', fontsize=16)
    plt.text(0.5, 0.48, "Matemática y Lengua Analizadas para estudiantes con el 100%_ de ítems completados", ha='center', va='center', fontsize=14, style='italic')
    fecha_str = datetime.datetime.now().strftime("%d de %B, %Y")
    plt.text(0.5, 0.35, f"Generado el: {fecha_str}", ha='center', va='center', fontsize=12, color='gray')
    pdf.savefig(fig)
    plt.close()

    grados_data = {}

    for grado_num in range(3, 12):
        archivo_mat = os.path.join(script_dir, f"Mat_{grado_num}.txt")
        archivo_lec = os.path.join(script_dir, f"Lec_{grado_num}.txt")
        
        df_mat_raw = leer_y_limpiar(archivo_mat) if os.path.exists(archivo_mat) else None
        df_lec_raw = leer_y_limpiar(archivo_lec) if os.path.exists(archivo_lec) else None
        
        if df_mat_raw is None and df_lec_raw is None: continue
            
        print_txt(f"-> Procesando Grado {grado_num}...\n")
        print_txt(f">>> GRADO {grado_num} <<<\n")
        
        datos_mat = procesar_100_porciento(df_mat_raw, "Matemática", "MAT")
        datos_lec = procesar_100_porciento(df_lec_raw, "Lengua", "LEC")
        print_txt("-----------------------------------------------------------------\n")
        
        met_mat = extraer_metricas(datos_mat, "Matemática", grado_num)
        met_lec = extraer_metricas(datos_lec, "Lengua", grado_num)
        
        if not met_mat and not met_lec: continue
        grados_data[grado_num] = {'mat': met_mat, 'lec': met_lec}

    # --- RESUMEN EJECUTIVO NACIONAL ---
    fig = plt.figure(figsize=(11, 8.5))
    # Título más arriba para evitar superposición
    fig.suptitle("RESUMEN EJECUTIVO NACIONAL", fontsize=16, fontweight='bold', color='darkblue', y=0.96)
    
    # Tabla global ligeramente más abajo
    ax_table = fig.add_axes([0.1, 0.72, 0.8, 0.12])
    ax_table.axis('off')
    global_df = pd.DataFrame([
        {'Materia': 'Matemática', 'Total Registrados': f"{global_totals['Matemática']['Registrados']:,}", 'Completaron 100%': f"{global_totals['Matemática']['100%_Completos']:,}", 'Porcentaje': f"{(global_totals['Matemática']['100%_Completos']/max(1, global_totals['Matemática']['Registrados']))*100:.1f}%"},
        {'Materia': 'Lengua', 'Total Registrados': f"{global_totals['Lengua']['Registrados']:,}", 'Completaron 100%': f"{global_totals['Lengua']['100%_Completos']:,}", 'Porcentaje': f"{(global_totals['Lengua']['100%_Completos']/max(1, global_totals['Lengua']['Registrados']))*100:.1f}%"}
    ])
    format_table(ax_table, global_df, "Tasa de Participación Global (Todos los Grados)")

    # Boxplots ajustados en tamaño y posición
    if not df_global_estand.empty:
        materias_presentes = df_global_estand['Materia'].unique()
        num_mats = len(materias_presentes)
        # Ajuste de coordenadas: [Izquierda, Abajo, Ancho, Alto]
        axes = [fig.add_axes([0.1, 0.38, 0.8, 0.24]), fig.add_axes([0.1, 0.06, 0.8, 0.24])] if num_mats == 2 else [fig.add_axes([0.1, 0.1, 0.8, 0.5])]
        
        for i, mat in enumerate(materias_presentes):
            ax = axes[i]
            df_plot = df_global_estand[df_global_estand['Materia'] == mat]
            sns.boxplot(data=df_plot, x='Grado_Num', y='Puntaje_Transformado', hue='Grado_Num', palette='viridis', ax=ax, legend=False)
            ax.set_title(f"Distribución {mat.upper()} (Z+5)", fontweight='bold')
            ax.set_xlabel("Grado Analizado")
            ax.set_ylabel("Puntaje Estandarizado")
            ax.set_ylim(0, 10)
            ax.grid(axis='y', linestyle='--', alpha=0.7)

    pdf.savefig(fig)
    plt.close()

    # --- REPORTE DETALLADO POR GRADO ---
    for grado_num, data in grados_data.items():
        mat_data = data['mat']
        lec_data = data['lec']
        
        # PÁGINA A: Participación y Tablas
        fig = plt.figure(figsize=(11, 8.5))
        fig.suptitle(f"INFORME DEL GRADO {grado_num} - ESTADÍSTICAS Y QUINTILES", fontsize=16, fontweight='bold', color='darkblue', y=0.96)
        
        # Caja de texto más arriba para evitar choque
        part_text = "TASA DE COMPLETITUD DEL GRADO:\n\n"
        if lec_data:
            part_text += f"LENGUA: Registrados: {lec_data['part']['Registrados']:,}  |  100% Completos: {lec_data['part']['Completos']:,} ({lec_data['part']['Pct']:.1f}%)\n"
        if mat_data:
            part_text += f"MATEMÁTICA: Registrados: {mat_data['part']['Registrados']:,}  |  100% Completos: {mat_data['part']['Completos']:,} ({mat_data['part']['Pct']:.1f}%)\n"
        
        fig.text(0.5, 0.87, part_text, ha='center', va='center', fontsize=11, bbox=dict(facecolor='whitesmoke', edgecolor='gray', boxstyle='round,pad=0.5'))

        # GridSpec más abajo y con más separación (top=0.70 da un respiro enorme arriba)
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 2], top=0.70, bottom=0.08, hspace=0.5)
        
        ax_desc = fig.add_subplot(gs[0])
        desc_dfs = []
        if lec_data: desc_dfs.append(lec_data['desc'])
        if mat_data: desc_dfs.append(mat_data['desc'])
        if desc_dfs: format_table(ax_desc, pd.concat(desc_dfs, ignore_index=True), "Estadísticas Descriptivas (Alumnos 100%)")
            
        ax_quint = fig.add_subplot(gs[1])
        quint_dfs = []
        if lec_data: quint_dfs.append(lec_data['quint'])
        if mat_data: quint_dfs.append(mat_data['quint'])
        if quint_dfs: format_table(ax_quint, pd.concat(quint_dfs, ignore_index=True), "Distribución Exacta por Quintiles")

        pdf.savefig(fig)
        plt.close()

        # PÁGINA B: Histogramas Separados
        fig = plt.figure(figsize=(11, 8.5))
        fig.suptitle(f"GRADO {grado_num} - DISTRIBUCIÓN DE ESCUELAS", fontsize=16, fontweight='bold', color='darkblue', y=0.95)
        
        gs_hist = fig.add_gridspec(1, 2, wspace=0.2, top=0.85, bottom=0.15)
        if lec_data:
            ax_hist_lec = fig.add_subplot(gs_hist[0])
            sns.histplot(lec_data['esc_z']['Z_Score'], bins=20, color='#e34a33', edgecolor='black', ax=ax_hist_lec)
            ax_hist_lec.axvline(0, color='black', linestyle='--')
            ax_hist_lec.set_title("Z-score Escuelas: Lengua")
            ax_hist_lec.set_xlabel("Z-score (Media=0, DE=1)")
            ax_hist_lec.set_ylabel("Cantidad de Escuelas")

        if mat_data:
            ax_hist_mat = fig.add_subplot(gs_hist[1] if lec_data else gs_hist[0])
            sns.histplot(mat_data['esc_z']['Z_Score'], bins=20, color='#2c7fb8', edgecolor='black', ax=ax_hist_mat)
            ax_hist_mat.axvline(0, color='black', linestyle='--')
            ax_hist_mat.set_title("Z-score Escuelas: Matemática")
            ax_hist_mat.set_xlabel("Z-score (Media=0, DE=1)")
            ax_hist_mat.set_ylabel("Cantidad de Escuelas")

        pdf.savefig(fig)
        plt.close()

        # PÁGINA C: Barras de Dificultad
        materias_validas = sum([1 for x in [lec_data, mat_data] if x is not None])
        if materias_validas > 0:
            fig, axes = plt.subplots(materias_validas, 1, figsize=(11, 8.5))
            fig.suptitle(f"GRADO {grado_num} - ANÁLISIS DE DIFICULTAD DE ÍTEMS", fontsize=16, fontweight='bold', color='darkblue', y=0.95)
            
            if materias_validas == 1: axes = [axes]
            
            idx = 0
            def plot_bars(ax, df, mat_name, color):
                sns.barplot(data=df, x='Item', y='Pct', color=color, ax=ax)
                ax.set_title(f"Porcentaje de Aciertos por Ítem: {mat_name}", fontweight='bold')
                ax.set_ylabel("Correctas (%)")
                ax.set_xlabel("")
                ax.set_ylim(0, 115) 
                ax.set_yticks(np.arange(0, 101, 20))
                ax.tick_params(axis='x', rotation=90, labelsize=7)
                for container in ax.containers:
                    ax.bar_label(container, fmt='%.1f%%', padding=3, rotation=90, size=7, fontweight='bold')

            if lec_data: 
                plot_bars(axes[idx], lec_data['dif'], "Lengua", "#e34a33")
                idx += 1
            if mat_data: 
                plot_bars(axes[idx], mat_data['dif'], "Matemática", "#2c7fb8")

            plt.tight_layout(rect=[0, 0, 1, 0.9])
            pdf.savefig(fig)
            plt.close()

# TXT OUTPUT
print_txt("=================================================================\n")
print_txt(" RESUMEN GLOBAL DE PARTICIPACIÓN (TODOS LOS GRADOS)\n")
print_txt("=================================================================\n")
for mat in ['Matemática', 'Lengua']:
    reg = global_totals[mat]['Registrados']
    com = global_totals[mat]['100%_Completos']
    pct = (com / reg) * 100 if reg > 0 else 0
    print_txt(f" {mat.upper()}:\n")
    print_txt(f"   - Gran Total Estudiantes Registrados : {reg:,}\n")
    print_txt(f"   - Gran Total con Prueba al 100%      : {com:,} ({pct:.1f}%)\n")
print_txt("=================================================================\n")

print("✅ PROCESO MAESTRO COMPLETADO EXITOSAMENTE.")