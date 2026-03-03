import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import scipy.stats as stats

# =========================================================================
# 1. CONFIGURACIÓN INICIAL Y DIRECTORIOS
# =========================================================================
script_dir = os.path.dirname(os.path.abspath(__file__))

# Archivos de salida solicitados
archivo_txt = os.path.join(script_dir, "Raw_Results.txt")
archivo_pdf = os.path.join(script_dir, "Raw_Results.pdf")

global_totals = {
    'Matemática': {'Registrados': 0, '100%_Completos': 0},
    'Lengua': {'Registrados': 0, '100%_Completos': 0}
}
df_global_estand = pd.DataFrame()

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
    
    participacion = {'Registrados': tot_inicial, 'Completos': tot_final, 'Pct': pct, 'Items': tot_items}
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
    
    try:
        simetria = float(np.round(stats.skew(df_100['Puntaje_Total'].dropna()), 2))
        if np.isnan(simetria): simetria = 0.0
    except:
        simetria = 0.0
        
    try:
        curtosis = float(np.round(stats.kurtosis(df_100['Puntaje_Total'].dropna()), 2))
        if np.isnan(curtosis): curtosis = 0.0
    except:
        curtosis = 0.0
    
    # Estandarización: Z*1 + 5
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
        'Máximo': df_100['Puntaje_Total'].max(),
        'Simetría': simetria,
        'Curtosis': curtosis
    }])
    
    # Manejo de Quintiles
    quint_list = []
    if len(df_100) >= 5:
        df_100['Quintil'] = pd.qcut(df_100['Puntaje_Total'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
        for q, g in df_100.groupby('Quintil', observed=True):
            quint_list.append({
                'Materia': materia,
                'Quintil': q,
                'Rango': f"{g['Puntaje_Total'].min():.1f} - {g['Puntaje_Total'].max():.1f}",
                'Número Estudiantes': f"{len(g):,}",
                'Porcentaje (%)': f"{(len(g)/len(df_100))*100:.1f}%"
            })
    else:
        quint_list.append({
            'Materia': materia,
            'Quintil': 'Todos',
            'Rango': f"{df_100['Puntaje_Total'].min():.1f} - {df_100['Puntaje_Total'].max():.1f}",
            'Número Estudiantes': f"{len(df_100):,}",
            'Porcentaje (%)': "100.0%"
        })
    quint = pd.DataFrame(quint_list)
    
    esc_z = df_100.groupby('Centro')['Puntaje_Total'].mean().reset_index()
    esc_mean = esc_z['Puntaje_Total'].mean()
    esc_sd = esc_z['Puntaje_Total'].std(ddof=1)
    if pd.isna(esc_sd) or esc_sd == 0: esc_sd = 1
    esc_z['Z_Score'] = (esc_z['Puntaje_Total'] - esc_mean) / esc_sd
    
    dif_series = (df_100[item_cols] == '1').mean() * 100
    # AQUÍ ESTÁ EL ERROR CORREGIDO (np.round en lugar de round):
    dif = pd.DataFrame({'Item': dif_series.index, 'Pct': np.round(dif_series.values, 2)})
    
    return {'desc': desc, 'quint': quint, 'esc_z': esc_z, 'dif': dif, 'part': participacion, 'df_scores': df_100['Z_Score']}

# =========================================================================
# 3. EXTRAER DATOS MAESTROS
# =========================================================================
print("Analizando bases de datos y procesando filtrado 100%...")
grados_data = {}
for grado_num in range(3, 12):
    archivo_mat = os.path.join(script_dir, f"Mat_{grado_num}.txt")
    archivo_lec = os.path.join(script_dir, f"Lec_{grado_num}.txt")
    
    df_mat_raw = leer_y_limpiar(archivo_mat) if os.path.exists(archivo_mat) else None
    df_lec_raw = leer_y_limpiar(archivo_lec) if os.path.exists(archivo_lec) else None
    
    if df_mat_raw is None and df_lec_raw is None: continue
        
    print(f"-> Procesando Grado {grado_num}...")
    datos_mat = procesar_100_porciento(df_mat_raw, "Matemática", "MAT")
    datos_lec = procesar_100_porciento(df_lec_raw, "Lengua", "LEC")
    
    met_mat = extraer_metricas(datos_mat, "Matemática", grado_num)
    met_lec = extraer_metricas(datos_lec, "Lengua", grado_num)
    
    if not met_mat and not met_lec: continue
    grados_data[grado_num] = {'mat': met_mat, 'lec': met_lec}

# =========================================================================
# 4. EXPORTAR DATOS NUMÉRICOS Y TABLAS A TXT (Raw_Results.txt)
# =========================================================================
print(f"\nGuardando tablas numéricas en: {archivo_txt}")
with open(archivo_txt, 'w', encoding='utf-8') as f:
    f.write("=================================================================\n")
    f.write(" RESUMEN GLOBAL DE PARTICIPACIÓN (TODOS LOS GRADOS)\n")
    f.write("=================================================================\n")
    for mat in ['Matemática', 'Lengua']:
        reg = global_totals[mat]['Registrados']
        com = global_totals[mat]['100%_Completos']
        pct = (com / reg) * 100 if reg > 0 else 0
        f.write(f" {mat.upper()}:\n")
        f.write(f"   - Gran Total Registrados : {reg:,}\n")
        f.write(f"   - Completaron al 100%    : {com:,} ({pct:.1f}%)\n")
    
    f.write("\n=================================================================\n")
    f.write(" RESULTADOS DETALLADOS POR GRADO\n")
    f.write("=================================================================\n")
    
    for grado_num, data in grados_data.items():
        f.write(f"\n{'#'*60}\n")
        f.write(f" GRADO {grado_num}\n")
        f.write(f"{'#'*60}\n")
        
        for key, mat_name in [('lec', 'LENGUA'), ('mat', 'MATEMÁTICA')]:
            mat_data = data[key]
            if mat_data:
                f.write(f"\n--- {mat_name} ---\n")
                
                # Participación
                part = mat_data['part']
                f.write(f"Participación: {part['Registrados']} registrados | {part['Completos']} completos ({part['Pct']:.1f}%)\n")
                f.write(f"Total de ítems: {part['Items']}\n\n")
                
                # Estadísticas Descriptivas
                f.write("1. ESTADÍSTICAS DESCRIPTIVAS:\n")
                f.write(mat_data['desc'].to_string(index=False) + "\n\n")
                
                # Quintiles
                f.write("2. DISTRIBUCIÓN POR QUINTILES:\n")
                f.write(mat_data['quint'].to_string(index=False) + "\n\n")
                
                # Dificultad Ítems
                f.write("3. PORCENTAJE DE ACIERTOS POR ÍTEM (%):\n")
                f.write(mat_data['dif'].to_string(index=False) + "\n\n")

# =========================================================================
# 5. EXPORTAR TODOS LOS GRÁFICOS A PDF (Raw_Results.pdf)
# =========================================================================
print(f"Guardando gráficos generados en: {archivo_pdf}")
with PdfPages(archivo_pdf) as pdf:
    
    # --- Gráfico 1: Boxplot Global Estandarizado ---
    if not df_global_estand.empty:
        materias_presentes = df_global_estand['Materia'].unique()
        fig, axes = plt.subplots(len(materias_presentes), 1, figsize=(11, 4 * len(materias_presentes)))
        if len(materias_presentes) == 1: axes = [axes]
        
        fig.suptitle("Boxplots Globales Estandarizados (Z+5) por Grado y Materia", fontsize=14, fontweight='bold')
        for i, mat in enumerate(materias_presentes):
            sns.boxplot(data=df_global_estand[df_global_estand['Materia'] == mat], x='Grado_Num', y='Puntaje_Transformado', color='lightgray', ax=axes[i])
            axes[i].set_title(f"Distribución {mat.upper()}")
            axes[i].set_ylabel("Puntaje Estandarizado")
            axes[i].set_ylim(0, 10)
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

    # --- Gráficos por Grado ---
    for grado_num, data in grados_data.items():
        mat_data = data['mat']
        lec_data = data['lec']
        materias_validas = sum([1 for x in [lec_data, mat_data] if x is not None])
        
        if materias_validas == 0: continue
            
        # 1. Histogramas de Estudiantes (Z-Score)
        fig, axes = plt.subplots(1, materias_validas, figsize=(11, 5))
        fig.suptitle(f"GRADO {grado_num} - Distribución de Estudiantes (Z-Score)", fontsize=14, fontweight='bold')
        if materias_validas == 1: axes = [axes]
        
        idx = 0
        if lec_data:
            sns.histplot(lec_data['df_scores'], bins=20, color='#e34a33', edgecolor='black', ax=axes[idx])
            axes[idx].axvline(0, color='black', linestyle='--')
            axes[idx].set_title("Lengua")
            idx += 1
        if mat_data:
            sns.histplot(mat_data['df_scores'], bins=20, color='#2c7fb8', edgecolor='black', ax=axes[idx])
            axes[idx].axvline(0, color='black', linestyle='--')
            axes[idx].set_title("Matemática")
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        # 2. Histogramas de Escuelas (Z-Score)
        fig, axes = plt.subplots(1, materias_validas, figsize=(11, 5))
        fig.suptitle(f"GRADO {grado_num} - Distribución de Escuelas (Z-Score Promedio)", fontsize=14, fontweight='bold')
        if materias_validas == 1: axes = [axes]
        
        idx = 0
        if lec_data:
            sns.histplot(lec_data['esc_z']['Z_Score'], bins=20, color='#e34a33', edgecolor='black', ax=axes[idx])
            axes[idx].axvline(0, color='black', linestyle='--')
            axes[idx].set_title("Lengua")
            idx += 1
        if mat_data:
            sns.histplot(mat_data['esc_z']['Z_Score'], bins=20, color='#2c7fb8', edgecolor='black', ax=axes[idx])
            axes[idx].axvline(0, color='black', linestyle='--')
            axes[idx].set_title("Matemática")
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        # 3. Gráficos de Barras (Dificultad de Ítems)
        fig, axes = plt.subplots(materias_validas, 1, figsize=(11, 4 * materias_validas))
        fig.suptitle(f"GRADO {grado_num} - Porcentaje de Aciertos por Ítem", fontsize=14, fontweight='bold')
        if materias_validas == 1: axes = [axes]
        
        idx = 0
        def plot_bars(ax, df, mat_name, color):
            sns.barplot(data=df, x='Item', y='Pct', color=color, ax=ax)
            ax.set_title(mat_name)
            ax.set_ylabel("Correctas (%)")
            ax.set_ylim(0, 115) 
            ax.tick_params(axis='x', rotation=90, labelsize=7)
            for container in ax.containers:
                ax.bar_label(container, fmt='%.1f%%', padding=3, rotation=90, size=7)

        if lec_data: 
            plot_bars(axes[idx], lec_data['dif'], "Lengua", "#e34a33")
            idx += 1
        if mat_data: 
            plot_bars(axes[idx], mat_data['dif'], "Matemática", "#2c7fb8")
        plt.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

print("\n✅ PROCESO COMPLETADO EXITOSAMENTE.")