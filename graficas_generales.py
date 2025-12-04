import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['lines.linewidth'] = 2.5
plt.rcParams['lines.markersize'] = 8

# Colores
COLORES_N = {
    10000000000: '#e74c3c',
    20000000000: '#3498db',
    40000000000: '#2ecc71',
    60000000000: '#f39c12'
}

ETIQUETAS_N = {
    10000000000: 'N = 10G',
    20000000000: 'N = 20G',
    40000000000: 'N = 40G',
    60000000000: 'N = 60G'
}

COLORES_SIM = {
    'roquer': '#e74c3c',
    'orca': '#3498db',
    'teen': '#2ecc71'
}

def parsear_log_paralelo(archivo_log):
    """Parsea logs de simulaciones paralelas."""
    datos = {}
    
    with open(archivo_log, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    patron = r'Configuración: \[(\w+)\|(\d+)CPUs\] param1=(\d+), param2=(\d+)\s+' \
             r'Código de salida: (\d+)\s+' \
             r'STDOUT:\s+N=(\d+)\s+Threads=(\d+)\s+' \
             r'Integral = ([\d.]+)\s+error = ([\d.e+-]+)\s+' \
             r'Time = ([\d.]+) sec'
    
    matches = re.finditer(patron, contenido)
    
    for match in matches:
        simulador = match.group(1)
        cpus = int(match.group(2))
        N = int(match.group(3))
        nThreads = int(match.group(4))
        codigo_salida = int(match.group(5))
        time = float(match.group(10))
        error = float(match.group(9))
        
        if codigo_salida == 0:
            if simulador not in datos:
                datos[simulador] = {'cpus': cpus, 'data': {}}
            if N not in datos[simulador]['data']:
                datos[simulador]['data'][N] = {}
            
            datos[simulador]['data'][N][nThreads] = {'time': time, 'error': error}
    
    return datos

def grafica_panoramica_general(datos, directorio):
    """
    Vista panorámica: todos los simuladores, todos los N, todos los threads.
    """
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    fig.suptitle('PANORÁMICA GENERAL DE RENDIMIENTO\nTodos los Simuladores y Configuraciones',
                 fontsize=18, fontweight='bold', y=0.98)
    
    # 1. Tiempos de ejecución (todas las configuraciones)
    ax1 = fig.add_subplot(gs[0, :2])
    for simulador in sorted(datos.keys()):
        for N in sorted(datos[simulador]['data'].keys()):
            threads = sorted(datos[simulador]['data'][N].keys())
            tiempos = [datos[simulador]['data'][N][t]['time'] for t in threads]
            
            ax1.plot(threads, tiempos, 'o-', 
                    color=COLORES_N[N],
                    alpha=0.7 if simulador == list(datos.keys())[0] else 0.4,
                    label=f"{simulador.upper()} - {ETIQUETAS_N[N]}" if simulador == list(datos.keys())[0] else "",
                    linewidth=2.5 if simulador == list(datos.keys())[0] else 1.5,
                    markersize=6)
    
    ax1.set_xlabel('Número de Threads', fontweight='bold')
    ax1.set_ylabel('Tiempo (s)', fontweight='bold')
    ax1.set_title('Tiempo de Ejecución - Todas las Configuraciones', fontweight='bold', fontsize=13)
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log', base=2)
    ax1.set_yscale('log')
    
    # 2. Mejor configuración por N
    ax2 = fig.add_subplot(gs[0, 2])
    N_values = sorted(list(datos[list(datos.keys())[0]]['data'].keys()))
    mejores_tiempos = []
    labels_mejores = []
    
    for N in N_values:
        mejor_tiempo = float('inf')
        mejor_config = ""
        
        for simulador in datos.keys():
            if N in datos[simulador]['data']:
                for t in datos[simulador]['data'][N].keys():
                    tiempo = datos[simulador]['data'][N][t]['time']
                    if tiempo < mejor_tiempo:
                        mejor_tiempo = tiempo
                        mejor_config = f"{simulador.upper()}\n{t}t"
        
        mejores_tiempos.append(mejor_tiempo)
        labels_mejores.append(mejor_config)
    
    bars = ax2.bar(range(len(N_values)), mejores_tiempos, 
                   color=[COLORES_N[n] for n in N_values], alpha=0.8, edgecolor='black')
    
    for i, (bar, label) in enumerate(zip(bars, labels_mejores)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{label}\n{height:.2f}s',
                ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    ax2.set_xticks(range(len(N_values)))
    ax2.set_xticklabels([ETIQUETAS_N[n] for n in N_values], fontsize=9)
    ax2.set_ylabel('Mejor Tiempo (s)', fontweight='bold')
    ax2.set_title('Mejor Configuración por N', fontweight='bold', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Speedup comparativo (base: 2 threads de cada simulador)
    ax3 = fig.add_subplot(gs[1, 0])
    for simulador in sorted(datos.keys()):
        # Promedio de speedup para cada número de threads
        threads_unicos = set()
        for N in datos[simulador]['data'].keys():
            threads_unicos.update(datos[simulador]['data'][N].keys())
        
        threads_sorted = sorted(threads_unicos)
        speedups_promedio = []
        
        for t in threads_sorted:
            speedups = []
            for N in datos[simulador]['data'].keys():
                if t in datos[simulador]['data'][N] and 2 in datos[simulador]['data'][N]:
                    t_base = datos[simulador]['data'][N][2]['time']
                    t_actual = datos[simulador]['data'][N][t]['time']
                    speedups.append(t_base / t_actual)
            
            if speedups:
                speedups_promedio.append(np.mean(speedups))
            else:
                speedups_promedio.append(0)
        
        ax3.plot(threads_sorted, speedups_promedio, 'o-',
                color=COLORES_SIM.get(simulador, '#666'),
                label=simulador.upper(),
                linewidth=3, markersize=8)
    
    # Línea ideal
    ax3.plot(threads_sorted, [t/2 for t in threads_sorted], 'k--',
            label='Ideal', linewidth=2, alpha=0.6)
    ax3.axhline(y=1, color='red', linestyle=':', linewidth=2, alpha=0.6)
    
    ax3.set_xlabel('Threads', fontweight='bold')
    ax3.set_ylabel('Speedup Promedio', fontweight='bold')
    ax3.set_title('Speedup Promedio por Simulador', fontweight='bold', fontsize=12)
    ax3.legend(loc='best', fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_xscale('log', base=2)
    
    # 4. Eficiencia comparativa
    ax4 = fig.add_subplot(gs[1, 1])
    for simulador in sorted(datos.keys()):
        threads_sorted = sorted(set(t for N in datos[simulador]['data'].keys() 
                                   for t in datos[simulador]['data'][N].keys()))
        eficiencias_promedio = []
        
        for t in threads_sorted:
            eficiencias = []
            for N in datos[simulador]['data'].keys():
                if t in datos[simulador]['data'][N] and 2 in datos[simulador]['data'][N]:
                    t_base = datos[simulador]['data'][N][2]['time']
                    t_actual = datos[simulador]['data'][N][t]['time']
                    speedup = t_base / t_actual
                    eficiencia = (speedup / t) * 100
                    eficiencias.append(eficiencia)
            
            if eficiencias:
                eficiencias_promedio.append(np.mean(eficiencias))
        
        ax4.plot(threads_sorted, eficiencias_promedio, 'o-',
                color=COLORES_SIM.get(simulador, '#666'),
                label=simulador.upper(),
                linewidth=3, markersize=8)
    
    ax4.axhline(y=100, color='k', linestyle='--', linewidth=2, alpha=0.6)
    ax4.set_xlabel('Threads', fontweight='bold')
    ax4.set_ylabel('Eficiencia (%)', fontweight='bold')
    ax4.set_title('Eficiencia Promedio por Simulador', fontweight='bold', fontsize=12)
    ax4.legend(loc='best', fontsize=9)
    ax4.grid(True, alpha=0.3)
    ax4.set_xscale('log', base=2)
    ax4.set_ylim(0, 110)
    
    # 5. Precisión (errores)
    ax5 = fig.add_subplot(gs[1, 2])
    for simulador in sorted(datos.keys()):
        for N in sorted(datos[simulador]['data'].keys()):
            threads = sorted(datos[simulador]['data'][N].keys())
            errores = [datos[simulador]['data'][N][t]['error'] for t in threads]
            
            ax5.plot(threads, errores, 'o-',
                    color=COLORES_N[N],
                    alpha=0.7 if simulador == list(datos.keys())[0] else 0.4,
                    linewidth=2 if simulador == list(datos.keys())[0] else 1,
                    markersize=5)
    
    ax5.set_xlabel('Threads', fontweight='bold')
    ax5.set_ylabel('Error (menor = mejor)', fontweight='bold')
    ax5.set_title('Precisión del Cálculo', fontweight='bold', fontsize=12)
    ax5.grid(True, alpha=0.3)
    ax5.set_xscale('log', base=2)
    ax5.set_yscale('log')
    ax5.invert_yaxis()
    
    # 6. Escalabilidad por simulador
    ax6 = fig.add_subplot(gs[2, :])
    
    width = 0.15
    x = np.arange(len(threads_sorted))
    
    for idx, simulador in enumerate(sorted(datos.keys())):
        # Para N=60G (el más grande)
        N_grande = max(datos[simulador]['data'].keys())
        threads = sorted(datos[simulador]['data'][N_grande].keys())
        tiempos = [datos[simulador]['data'][N_grande][t]['time'] for t in threads]
        
        offset = width * (idx - len(datos.keys())/2)
        ax6.bar(x + offset, tiempos, width,
               label=f"{simulador.upper()} ({datos[simulador]['cpus']} CPUs)",
               color=COLORES_SIM.get(simulador, '#666'),
               alpha=0.8, edgecolor='black')
    
    ax6.set_xlabel('Número de Threads', fontweight='bold')
    ax6.set_ylabel('Tiempo (s)', fontweight='bold')
    ax6.set_title(f'Comparación Directa - {ETIQUETAS_N[N_grande]} (Tamaño Máximo)', 
                 fontweight='bold', fontsize=13)
    ax6.set_xticks(x)
    ax6.set_xticklabels(threads)
    ax6.legend(loc='best')
    ax6.grid(True, alpha=0.3, axis='y')
    ax6.set_yscale('log')
    
    plt.savefig(directorio / 'panoramica_general.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: panoramica_general.png")
    plt.close()

def grafica_matriz_rendimiento(datos, directorio):
    """
    Matriz de rendimiento: mejor configuración para cada combinación N x Threads.
    """
    simuladores = sorted(datos.keys())
    N_values = sorted(list(datos[simuladores[0]]['data'].keys()))
    threads_list = sorted(set(t for sim in datos.values() 
                             for N in sim['data'].values() 
                             for t in N.keys()))
    
    fig, axes = plt.subplots(1, len(simuladores), figsize=(6*len(simuladores), 8))
    if len(simuladores) == 1:
        axes = [axes]
    
    fig.suptitle('MATRIZ DE RENDIMIENTO\nTiempo de Ejecución (segundos)',
                 fontsize=16, fontweight='bold')
    
    for idx, simulador in enumerate(simuladores):
        ax = axes[idx]
        
        # Crear matriz de tiempos
        matriz = []
        for N in N_values:
            fila = []
            for t in threads_list:
                if t in datos[simulador]['data'][N]:
                    fila.append(datos[simulador]['data'][N][t]['time'])
                else:
                    fila.append(np.nan)
            matriz.append(fila)
        
        matriz = np.array(matriz)
        
        # Normalizar para el color (log scale)
        matriz_log = np.log10(matriz + 1)
        
        im = ax.imshow(matriz_log, cmap='RdYlGn_r', aspect='auto')
        
        # Configurar ejes
        ax.set_xticks(np.arange(len(threads_list)))
        ax.set_yticks(np.arange(len(N_values)))
        ax.set_xticklabels(threads_list)
        ax.set_yticklabels([ETIQUETAS_N[n] for n in N_values])
        
        ax.set_xlabel('Número de Threads', fontweight='bold')
        ax.set_ylabel('Tamaño del Problema', fontweight='bold')
        ax.set_title(f'{simulador.upper()} ({datos[simulador]["cpus"]} CPUs)',
                    fontweight='bold', fontsize=13)
        
        # Añadir valores en las celdas
        for i in range(len(N_values)):
            for j in range(len(threads_list)):
                if not np.isnan(matriz[i, j]):
                    text = ax.text(j, i, f'{matriz[i, j]:.1f}',
                                 ha="center", va="center", 
                                 color="black", fontweight='bold', fontsize=9)
        
        # Barra de color
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('log₁₀(Tiempo)', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(directorio / 'matriz_rendimiento.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: matriz_rendimiento.png")
    plt.close()

def grafica_ranking_configuraciones(datos, directorio):
    """
    Ranking de las 20 mejores configuraciones globales.
    """
    # Recopilar todas las configuraciones
    configuraciones = []
    
    for simulador in datos.keys():
        for N in datos[simulador]['data'].keys():
            for t in datos[simulador]['data'][N].keys():
                tiempo = datos[simulador]['data'][N][t]['time']
                configuraciones.append({
                    'simulador': simulador,
                    'N': N,
                    'threads': t,
                    'tiempo': tiempo,
                    'cpus': datos[simulador]['cpus']
                })
    
    # Ordenar por tiempo (menor es mejor)
    configuraciones.sort(key=lambda x: x['tiempo'])
    
    # Top 20
    top20 = configuraciones[:20]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # Gráfica 1: Barras horizontales de las mejores 20
    labels = [f"{c['simulador'].upper()}\n{ETIQUETAS_N[c['N']]}\n{c['threads']}t" 
             for c in top20]
    tiempos = [c['tiempo'] for c in top20]
    colores = [COLORES_SIM.get(c['simulador'], '#666') for c in top20]
    
    y_pos = np.arange(len(labels))
    bars = ax1.barh(y_pos, tiempos, color=colores, alpha=0.8, edgecolor='black')
    
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels, fontsize=8)
    ax1.invert_yaxis()
    ax1.set_xlabel('Tiempo (segundos)', fontweight='bold', fontsize=12)
    ax1.set_title('TOP 20 Configuraciones Más Rápidas', fontweight='bold', fontsize=14)
    ax1.grid(True, alpha=0.3, axis='x')
    
    # Añadir valores
    for i, (bar, tiempo) in enumerate(zip(bars, tiempos)):
        width = bar.get_width()
        ax1.text(width, bar.get_y() + bar.get_height()/2,
                f' {tiempo:.2f}s',
                ha='left', va='center', fontweight='bold', fontsize=8)
    
    # Gráfica 2: Distribución de mejores configuraciones por simulador
    conteo_simuladores = {}
    for c in top20:
        sim = c['simulador'].upper()
        conteo_simuladores[sim] = conteo_simuladores.get(sim, 0) + 1
    
    sims = list(conteo_simuladores.keys())
    conteos = list(conteo_simuladores.values())
    colores_pie = [COLORES_SIM.get(s.lower(), '#666') for s in sims]
    
    wedges, texts, autotexts = ax2.pie(conteos, labels=sims, autopct='%1.1f%%',
                                        colors=colores_pie, startangle=90,
                                        textprops={'fontweight': 'bold', 'fontsize': 12})
    
    ax2.set_title('Distribución en TOP 20\npor Simulador', 
                 fontweight='bold', fontsize=14)
    
    # Añadir conteos
    for i, (text, count) in enumerate(zip(texts, conteos)):
        text.set_text(f'{text.get_text()}\n({count} configs)')
    
    plt.tight_layout()
    plt.savefig(directorio / 'ranking_configuraciones.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: ranking_configuraciones.png")
    plt.close()

def grafica_escalabilidad_fuerte_comparativa(datos, directorio):
    """
    Escalabilidad fuerte: todos los simuladores en una sola gráfica por cada N.
    """
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('ESCALABILIDAD FUERTE COMPARATIVA\nTodos los Simuladores',
                 fontsize=16, fontweight='bold')
    
    N_values = sorted(list(datos[list(datos.keys())[0]]['data'].keys()))
    
    for idx, N in enumerate(N_values):
        ax = axes[idx // 2, idx % 2]
        
        for simulador in sorted(datos.keys()):
            if N in datos[simulador]['data']:
                threads = sorted(datos[simulador]['data'][N].keys())
                tiempos = [datos[simulador]['data'][N][t]['time'] for t in threads]
                
                ax.plot(threads, tiempos, 'o-',
                       color=COLORES_SIM.get(simulador, '#666'),
                       label=f"{simulador.upper()} ({datos[simulador]['cpus']} CPUs)",
                       linewidth=3, markersize=10)
        
        ax.set_xlabel('Número de Threads', fontsize=12, fontweight='bold')
        ax.set_ylabel('Tiempo (segundos)', fontsize=12, fontweight='bold')
        ax.set_title(f'{ETIQUETAS_N[N]}', fontsize=13, fontweight='bold')
        ax.legend(loc='best', frameon=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xscale('log', base=2)
        ax.set_yscale('log')
        ax.set_xticks(threads)
        ax.set_xticklabels([str(t) for t in threads])
    
    plt.tight_layout()
    plt.savefig(directorio / 'escalabilidad_fuerte_comparativa.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: escalabilidad_fuerte_comparativa.png")
    plt.close()

def generar_informe_resumen(datos, directorio):
    """
    Genera un informe de texto con estadísticas clave.
    """
    archivo = directorio / 'informe_general.txt'
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write("INFORME GENERAL DE RENDIMIENTO\n")
        f.write("="*100 + "\n\n")
        
        # Configuraciones disponibles
        f.write("CONFIGURACIONES ANALIZADAS:\n")
        f.write("-"*100 + "\n")
        for simulador in sorted(datos.keys()):
            f.write(f"\n{simulador.upper()}:\n")
            f.write(f"  - CPUs disponibles: {datos[simulador]['cpus']}\n")
            f.write(f"  - Valores de N probados: {len(datos[simulador]['data'])}\n")
            total_ejecuciones = sum(len(datos[simulador]['data'][N]) 
                                   for N in datos[simulador]['data'])
            f.write(f"  - Total de ejecuciones: {total_ejecuciones}\n")
        
        # Mejor configuración global
        f.write("\n\nMEJOR CONFIGURACIÓN GLOBAL:\n")
        f.write("-"*100 + "\n")
        
        mejor_tiempo = float('inf')
        mejor_config = None
        
        for simulador in datos.keys():
            for N in datos[simulador]['data'].keys():
                for t in datos[simulador]['data'][N].keys():
                    tiempo = datos[simulador]['data'][N][t]['time']
                    if tiempo < mejor_tiempo:
                        mejor_tiempo = tiempo
                        mejor_config = {
                            'simulador': simulador,
                            'N': N,
                            'threads': t,
                            'tiempo': tiempo,
                            'error': datos[simulador]['data'][N][t]['error']
                        }
        
        if mejor_config:
            f.write(f"Simulador: {mejor_config['simulador'].upper()}\n")
            f.write(f"Tamaño del problema: {ETIQUETAS_N[mejor_config['N']]}\n")
            f.write(f"Número de threads: {mejor_config['threads']}\n")
            f.write(f"Tiempo: {mejor_config['tiempo']:.6f} segundos\n")
            f.write(f"Error: {mejor_config['error']:.3e}\n")
        
        # Peor configuración global
        f.write("\n\nPEOR CONFIGURACIÓN GLOBAL:\n")
        f.write("-"*100 + "\n")
        
        peor_tiempo = 0
        peor_config = None
        
        for simulador in datos.keys():
            for N in datos[simulador]['data'].keys():
                for t in datos[simulador]['data'][N].keys():
                    tiempo = datos[simulador]['data'][N][t]['time']
                    if tiempo > peor_tiempo:
                        peor_tiempo = tiempo
                        peor_config = {
                            'simulador': simulador,
                            'N': N,
                            'threads': t,
                            'tiempo': tiempo
                        }
        
        if peor_config:
            f.write(f"Simulador: {peor_config['simulador'].upper()}\n")
            f.write(f"Tamaño del problema: {ETIQUETAS_N[peor_config['N']]}\n")
            f.write(f"Número de threads: {peor_config['threads']}\n")
            f.write(f"Tiempo: {peor_config['tiempo']:.6f} segundos\n")
        
        # Mejor speedup promedio por simulador
        f.write("\n\nSPEEDUP PROMEDIO MÁXIMO (Base: 2 threads):\n")
        f.write("-"*100 + "\n")
        
        for simulador in sorted(datos.keys()):
            speedups_max = []
            
            for N in datos[simulador]['data'].keys():
                if 2 in datos[simulador]['data'][N]:
                    t_base = datos[simulador]['data'][N][2]['time']
                    
                    for t in datos[simulador]['data'][N].keys():
                        if t > 2:
                            t_actual = datos[simulador]['data'][N][t]['time']
                            speedup = t_base / t_actual
                            speedups_max.append(speedup)
            
            if speedups_max:
                f.write(f"{simulador.upper()}: {max(speedups_max):.2f}x (promedio: {np.mean(speedups_max):.2f}x)\n")
        
        f.write("\n")
    
    print(f"✓ Informe guardado: {archivo.name}")

def main():
    """
    Función principal.
    """
    print("="*80)
    print("ANÁLISIS VISUAL COMPLETO - SIMULACIONES GENERALES")
    print("="*80 + "\n")
    
    # Buscar archivos log paralelos
    logs_paralelo = list(Path('.').glob('resultados_simulaciones_*.log'))
    
    if not logs_paralelo:
        print("✗ No se encontraron logs de simulaciones")
        return
    
    # Parsear datos
    print("Parseando logs...")
    datos = {}
    for log in logs_paralelo:
        print(f"  - {log}")
        data = parsear_log_paralelo(log)
        datos.update(data)
    
    if not datos:
        print("✗ No se pudieron parsear datos")
        return
    
    print(f"\nSimuladores encontrados: {', '.join([s.upper() for s in datos.keys()])}")
    
    # Crear directorio de salida
    directorio = Path('graficas_generales')
    directorio.mkdir(exist_ok=True)
    
    print(f"\n{'='*60}")
    print("Generando gráficas visuales...")
    print(f"{'='*60}\n")
    
    # Generar todas las gráficas
    grafica_panoramica_general(datos, directorio)
    grafica_matriz_rendimiento(datos, directorio)
    grafica_ranking_configuraciones(datos, directorio)
    grafica_escalabilidad_fuerte_comparativa(datos, directorio)
    generar_informe_resumen(datos, directorio)
    
    print("\n" + "="*80)
    print(f"✓ ANÁLISIS COMPLETADO - Resultados en: {directorio}/")
    print("="*80)
    print("\nGráficas generadas:")
    print("  1. panoramica_general.png - Vista completa de todo")
    print("  2. matriz_rendimiento.png - Matrices de tiempo por simulador")
    print("  3. ranking_configuraciones.png - TOP 20 mejores configuraciones")
    print("  4. escalabilidad_fuerte_comparativa.png - Comparación directa")
    print("  5. informe_general.txt - Resumen estadístico")

if __name__ == "__main__":
    main()
