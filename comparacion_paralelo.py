import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 10)
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
    """
    Parsea logs de simulaciones paralelas.
    Returns: dict {simulador: {N: {nThreads: {'time': float}}}}
    """
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
        N = int(match.group(3))
        nThreads = int(match.group(4))
        codigo_salida = int(match.group(5))
        time = float(match.group(10))
        error = float(match.group(9))
        
        if codigo_salida == 0:
            if simulador not in datos:
                datos[simulador] = {}
            if N not in datos[simulador]:
                datos[simulador][N] = {}
            
            datos[simulador][N][nThreads] = {'time': time, 'error': error}
    
    return datos

def grafica_comparacion_tiempos_por_N(datos, directorio):
    """
    Compara tiempos entre simuladores para cada valor de N.
    """
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('Comparación Roquer vs Orca - Simulaciones Paralelas\nTiempo de Ejecución',
                 fontsize=16, fontweight='bold')
    
    simuladores = sorted(datos.keys())
    N_values = sorted(list(datos[simuladores[0]].keys()))
    
    for idx, N in enumerate(N_values):
        ax = axes[idx // 2, idx % 2]
        
        for simulador in simuladores:
            if N in datos[simulador]:
                threads = sorted(datos[simulador][N].keys())
                tiempos = [datos[simulador][N][t]['time'] for t in threads]
                
                ax.plot(threads, tiempos, 'o-',
                       color=COLORES_SIM.get(simulador, '#666'),
                       label=simulador.upper(),
                       linewidth=3, markersize=8)
        
        ax.set_xlabel('Número de Threads', fontsize=12, fontweight='bold')
        ax.set_ylabel('Tiempo (segundos)', fontsize=12, fontweight='bold')
        ax.set_title(f'{ETIQUETAS_N[N]}', fontsize=13, fontweight='bold')
        ax.legend(loc='best', frameon=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xscale('log', base=2)
        ax.set_yscale('log')
        ax.set_xticks(threads)
        ax.set_xticklabels([str(t) for t in threads], rotation=45)
    
    plt.tight_layout()
    plt.savefig(directorio / 'comparacion_tiempos_paralelo.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: comparacion_tiempos_paralelo.png")
    plt.close()

def grafica_comparacion_speedup(datos, directorio):
    """
    Compara speedup entre simuladores (base: 2 threads de cada simulador).
    """
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('Comparación Roquer vs Orca - Simulaciones Paralelas\nSpeedup (Base: 2 threads)',
                 fontsize=16, fontweight='bold')
    
    simuladores = sorted(datos.keys())
    N_values = sorted(list(datos[simuladores[0]].keys()))
    
    for idx, N in enumerate(N_values):
        ax = axes[idx // 2, idx % 2]
        
        for simulador in simuladores:
            if N in datos[simulador] and 2 in datos[simulador][N]:
                threads = sorted(datos[simulador][N].keys())
                tiempo_base = datos[simulador][N][2]['time']
                speedups = [tiempo_base / datos[simulador][N][t]['time'] for t in threads]
                
                ax.plot(threads, speedups, 'o-',
                       color=COLORES_SIM.get(simulador, '#666'),
                       label=simulador.upper(),
                       linewidth=3, markersize=8)
        
        # Línea de speedup ideal
        threads_ideal = sorted(list(datos[simuladores[0]][N].keys()))
        speedup_ideal = [t/2 for t in threads_ideal]
        ax.plot(threads_ideal, speedup_ideal, 'k--',
               label='Speedup Ideal', linewidth=2, alpha=0.6)
        
        ax.axhline(y=1, color='red', linestyle=':', linewidth=2, alpha=0.6)
        
        ax.set_xlabel('Número de Threads', fontsize=12, fontweight='bold')
        ax.set_ylabel('Speedup', fontsize=12, fontweight='bold')
        ax.set_title(f'{ETIQUETAS_N[N]}', fontsize=13, fontweight='bold')
        ax.legend(loc='best', frameon=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xscale('log', base=2)
        ax.set_xticks(threads_ideal)
        ax.set_xticklabels([str(t) for t in threads_ideal], rotation=45)
    
    plt.tight_layout()
    plt.savefig(directorio / 'comparacion_speedup_paralelo.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: comparacion_speedup_paralelo.png")
    plt.close()

def grafica_comparacion_eficiencia(datos, directorio):
    """
    Compara eficiencia entre simuladores.
    """
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('Comparación Roquer vs Orca - Simulaciones Paralelas\nEficiencia',
                 fontsize=16, fontweight='bold')
    
    simuladores = sorted(datos.keys())
    N_values = sorted(list(datos[simuladores[0]].keys()))
    
    for idx, N in enumerate(N_values):
        ax = axes[idx // 2, idx % 2]
        
        for simulador in simuladores:
            if N in datos[simulador] and 2 in datos[simulador][N]:
                threads = sorted(datos[simulador][N].keys())
                tiempo_base = datos[simulador][N][2]['time']
                eficiencias = [(tiempo_base / datos[simulador][N][t]['time']) / t * 100 
                             for t in threads]
                
                ax.plot(threads, eficiencias, 'o-',
                       color=COLORES_SIM.get(simulador, '#666'),
                       label=simulador.upper(),
                       linewidth=3, markersize=8)
        
        ax.axhline(y=100, color='k', linestyle='--', linewidth=2, alpha=0.6,
                  label='Eficiencia Ideal')
        
        ax.set_xlabel('Número de Threads', fontsize=12, fontweight='bold')
        ax.set_ylabel('Eficiencia (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'{ETIQUETAS_N[N]}', fontsize=13, fontweight='bold')
        ax.legend(loc='best', frameon=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xscale('log', base=2)
        ax.set_ylim(0, 110)
        threads_ideal = sorted(list(datos[simuladores[0]][N].keys()))
        ax.set_xticks(threads_ideal)
        ax.set_xticklabels([str(t) for t in threads_ideal], rotation=45)
    
    plt.tight_layout()
    plt.savefig(directorio / 'comparacion_eficiencia_paralelo.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: comparacion_eficiencia_paralelo.png")
    plt.close()

def grafica_heatmap_diferencia_tiempo(datos, directorio):
    """
    Heatmap mostrando diferencia porcentual de tiempo entre simuladores.
    """
    if len(datos) != 2:
        print("⚠ Se necesitan exactamente 2 simuladores para el heatmap")
        return
    
    simuladores = sorted(datos.keys())
    sim1, sim2 = simuladores[0], simuladores[1]
    
    N_values = sorted(datos[sim1].keys())
    threads_list = sorted(datos[sim1][N_values[0]].keys())
    
    # Crear matriz de diferencias porcentuales
    matriz = []
    for N in N_values:
        fila = []
        for t in threads_list:
            if t in datos[sim1][N] and t in datos[sim2][N]:
                t1 = datos[sim1][N][t]['time']
                t2 = datos[sim2][N][t]['time']
                # Diferencia porcentual: positivo si sim1 es más lento
                diff_pct = ((t1 - t2) / t2) * 100
                fila.append(diff_pct)
            else:
                fila.append(0)
        matriz.append(fila)
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    im = ax.imshow(matriz, cmap='RdYlGn_r', aspect='auto', vmin=-50, vmax=50)
    
    # Configurar ejes
    ax.set_xticks(np.arange(len(threads_list)))
    ax.set_yticks(np.arange(len(N_values)))
    ax.set_xticklabels(threads_list)
    ax.set_yticklabels([ETIQUETAS_N[n] for n in N_values])
    
    ax.set_xlabel('Número de Threads', fontsize=13, fontweight='bold')
    ax.set_ylabel('Tamaño del Problema', fontsize=13, fontweight='bold')
    ax.set_title(f'Diferencia Porcentual de Tiempo: {sim1.upper()} vs {sim2.upper()}\n'
                f'Rojo = {sim1.upper()} más lento | Verde = {sim1.upper()} más rápido',
                fontsize=15, fontweight='bold', pad=20)
    
    # Añadir valores en las celdas
    for i in range(len(N_values)):
        for j in range(len(threads_list)):
            text = ax.text(j, i, f'{matriz[i][j]:.1f}%',
                         ha="center", va="center", color="black", fontweight='bold')
    
    # Barra de color
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Diferencia (%)', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(directorio / 'heatmap_diferencia_tiempo.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: heatmap_diferencia_tiempo.png")
    plt.close()

def generar_tabla_comparacion_paralelo(datos, directorio):
    """
    Genera tabla comparativa detallada.
    """
    archivo = directorio / 'comparacion_paralelo.txt'
    
    simuladores = sorted(datos.keys())
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write("="*120 + "\n")
        f.write("COMPARACIÓN ROQUER VS ORCA - SIMULACIONES PARALELAS\n")
        f.write("="*120 + "\n\n")
        
        N_values = sorted(datos[simuladores[0]].keys())
        
        for N in N_values:
            f.write(f"\n{ETIQUETAS_N[N]}\n")
            f.write("-"*120 + "\n")
            
            # Encabezado de tabla
            header = f"{'Threads':<10}"
            for sim in simuladores:
                header += f"{sim.upper() + ' (s)':<18} {sim.upper() + ' Speedup':<18}"
            header += f"{'Diferencia %':<18}"
            f.write(header + "\n")
            f.write("-"*120 + "\n")
            
            threads = sorted(datos[simuladores[0]][N].keys())
            
            for t in threads:
                fila = f"{t:<10}"
                
                tiempos = []
                for sim in simuladores:
                    if t in datos[sim][N]:
                        tiempo = datos[sim][N][t]['time']
                        tiempos.append(tiempo)
                        
                        # Calcular speedup respecto a 2 threads
                        if 2 in datos[sim][N]:
                            speedup = datos[sim][N][2]['time'] / tiempo
                        else:
                            speedup = 1.0
                        
                        fila += f"{tiempo:<18.6f} {speedup:<18.2f}"
                    else:
                        fila += f"{'N/A':<18} {'N/A':<18}"
                
                # Calcular diferencia porcentual
                if len(tiempos) == 2:
                    diff_pct = ((tiempos[0] - tiempos[1]) / tiempos[1]) * 100
                    fila += f"{diff_pct:<18.2f}"
                else:
                    fila += f"{'N/A':<18}"
                
                f.write(fila + "\n")
            
            f.write("\n")
    
    print(f"✓ Tabla guardada: {archivo.name}")

def main():
    """
    Función principal.
    """
    print("="*80)
    print("COMPARACIÓN ROQUER vs ORCA - SIMULACIONES PARALELAS")
    print("="*80 + "\n")
    
    # Buscar archivos log paralelos
    logs_paralelo = list(Path('.').glob('resultados_simulaciones_*.log'))
    
    if not logs_paralelo:
        print("✗ No se encontraron logs de simulaciones paralelas")
        print("  Archivos esperados: resultados_simulaciones_roquer.log, resultados_simulaciones_orca.log")
        return
    
    # Parsear datos
    print("Parseando logs paralelos...")
    datos = {}
    for log in logs_paralelo:
        print(f"  - {log}")
        data = parsear_log_paralelo(log)
        datos.update(data)
    
    if not datos:
        print("✗ No se pudieron parsear datos de los logs")
        return
    
    print(f"\nSimuladores encontrados: {', '.join([s.upper() for s in datos.keys()])}")
    
    # Crear directorio de salida
    directorio = Path('comparacion_paralelo')
    directorio.mkdir(exist_ok=True)
    
    print(f"\n{'='*60}")
    print("Generando gráficas comparativas...")
    print(f"{'='*60}\n")
    
    # Generar gráficas
    grafica_comparacion_tiempos_por_N(datos, directorio)
    grafica_comparacion_speedup(datos, directorio)
    grafica_comparacion_eficiencia(datos, directorio)
    grafica_heatmap_diferencia_tiempo(datos, directorio)
    generar_tabla_comparacion_paralelo(datos, directorio)
    
    print("\n" + "="*80)
    print(f"✓ ANÁLISIS COMPLETADO - Resultados en: {directorio}/")
    print("="*80)

if __name__ == "__main__":
    main()
