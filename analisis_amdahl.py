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

def parsear_log_secuencial(archivo_log):
    """
    Parsea logs de simulaciones secuenciales.
    Returns: dict {N: {'time': float, 'error': float}}
    """
    datos = {}
    
    with open(archivo_log, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Patrón para código secuencial
    patron = r'Configuración: \[(\w+)\|(\d+)CPUs\|SECUENCIAL\] N=(\d+)\s+' \
             r'Código de salida: (\d+)\s+' \
             r'STDOUT:\s+N=(\d+).*?\n' \
             r'Integral ~ ([\d.]+)\s+error = ([\d.e+-]+)\s+' \
             r'Time = ([\d.]+) sec'
    
    matches = re.finditer(patron, contenido, re.DOTALL)
    
    for match in matches:
        simulador = match.group(1)
        N = int(match.group(3))
        codigo_salida = int(match.group(4))
        integral = float(match.group(6))
        error = float(match.group(7))
        time = float(match.group(8))
        
        if codigo_salida == 0:
            if simulador not in datos:
                datos[simulador] = {}
            
            datos[simulador][N] = {
                'time': time,
                'error': error,
                'integral': integral
            }
    
    return datos

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
        
        if codigo_salida == 0:
            if simulador not in datos:
                datos[simulador] = {}
            if N not in datos[simulador]:
                datos[simulador][N] = {}
            
            datos[simulador][N][nThreads] = {'time': time}
    
    return datos

def calcular_speedup_real(tiempo_secuencial, tiempo_paralelo):
    """Calcula el speedup real."""
    return tiempo_secuencial / tiempo_paralelo

def calcular_fraccion_paralelizable(tiempo_sec, tiempo_paralelo, p):
    """
    Estima la fracción paralelizable usando la Ley de Amdahl inversa.
    Speedup = 1 / (f_s + f_p / p)
    donde f_s = fracción serial, f_p = fracción paralelizable
    """
    speedup = tiempo_sec / tiempo_paralelo
    # f_s + f_p = 1
    # Speedup = 1 / (f_s + f_p/p) = 1 / (f_s + (1-f_s)/p)
    # f_s = (p - Speedup) / (p - 1) / Speedup (aproximación)
    if p <= 1:
        return 0
    
    try:
        f_s = (1 - speedup/p) / (1 - 1/p)
        f_p = 1 - f_s
        return max(0, min(1, f_p))
    except:
        return 0.95  # Valor por defecto

def speedup_teorico_amdahl(f_p, p):
    """
    Calcula el speedup teórico según la Ley de Amdahl.
    f_p: fracción paralelizable (0 a 1)
    p: número de procesadores
    """
    f_s = 1 - f_p
    return 1 / (f_s + f_p / p)

def grafica_amdahl_vs_real(datos_sec, datos_par, simulador, directorio):
    """
    Compara speedup real vs teórico de Amdahl.
    """
    if simulador not in datos_sec or simulador not in datos_par:
        print(f"No hay datos suficientes para {simulador}")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle(f'Ley de Amdahl: Speedup Real vs Teórico - {simulador.upper()}',
                 fontsize=16, fontweight='bold')
    
    for idx, N in enumerate(sorted(datos_sec[simulador].keys())):
        if N not in datos_par[simulador]:
            continue
        
        ax = axes[idx // 2, idx % 2]
        
        tiempo_sec = datos_sec[simulador][N]['time']
        threads = sorted(datos_par[simulador][N].keys())
        
        # Speedup real
        speedups_real = [calcular_speedup_real(tiempo_sec, datos_par[simulador][N][t]['time']) 
                        for t in threads]
        
        # Estimar fracción paralelizable usando threads=8 como referencia
        if 8 in datos_par[simulador][N]:
            f_p = calcular_fraccion_paralelizable(tiempo_sec, 
                                                  datos_par[simulador][N][8]['time'], 8)
        else:
            f_p = 0.95
        
        # Speedup teórico según Amdahl
        speedups_teorico = [speedup_teorico_amdahl(f_p, t) for t in threads]
        
        # Speedup ideal (lineal)
        speedup_ideal = threads
        
        # Graficar
        ax.plot(threads, speedups_real, 'o-', color=COLORES_N[N], 
               label='Speedup Real', linewidth=3, markersize=10)
        ax.plot(threads, speedups_teorico, 's--', color='purple', 
               label=f'Ley de Amdahl (f_p={f_p:.2%})', linewidth=2.5, markersize=8)
        ax.plot(threads, speedup_ideal, 'k:', 
               label='Speedup Ideal (Lineal)', linewidth=2, alpha=0.6)
        
        ax.set_xlabel('Número de Threads', fontsize=12, fontweight='bold')
        ax.set_ylabel('Speedup', fontsize=12, fontweight='bold')
        ax.set_title(f'{ETIQUETAS_N[N]} - Fracción paralelizable: {f_p:.2%}', 
                    fontsize=13, fontweight='bold')
        ax.legend(loc='best', frameon=True, shadow=True)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xscale('log', base=2)
        ax.set_xticks(threads)
        ax.set_xticklabels([str(t) for t in threads])
    
    plt.tight_layout()
    plt.savefig(directorio / f'amdahl_vs_real_{simulador}.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: amdahl_vs_real_{simulador}.png")
    plt.close()

def grafica_eficiencia_amdahl(datos_sec, datos_par, simulador, directorio):
    """
    Eficiencia real vs predicha por Amdahl.
    """
    if simulador not in datos_sec or simulador not in datos_par:
        return
    
    plt.figure(figsize=(14, 8))
    
    for N in sorted(datos_sec[simulador].keys()):
        if N not in datos_par[simulador]:
            continue
        
        tiempo_sec = datos_sec[simulador][N]['time']
        threads = sorted(datos_par[simulador][N].keys())
        
        # Eficiencia real = Speedup / nThreads
        eficiencias_real = [(tiempo_sec / datos_par[simulador][N][t]['time']) / t * 100 
                           for t in threads]
        
        plt.plot(threads, eficiencias_real, 'o-', color=COLORES_N[N],
                label=ETIQUETAS_N[N], linewidth=2.5, markersize=8)
    
    plt.axhline(y=100, color='k', linestyle='--', linewidth=2, alpha=0.6,
                label='Eficiencia Ideal (100%)')
    
    plt.xlabel('Número de Threads', fontsize=13, fontweight='bold')
    plt.ylabel('Eficiencia (%)', fontsize=13, fontweight='bold')
    plt.title(f'Eficiencia de Paralelización - {simulador.upper()}\n(Base: Código Secuencial)',
              fontsize=15, fontweight='bold', pad=20)
    plt.legend(loc='best', frameon=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.xscale('log', base=2)
    plt.xticks(threads, [str(t) for t in threads])
    plt.ylim(0, 110)
    
    plt.tight_layout()
    plt.savefig(directorio / f'eficiencia_{simulador}.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: eficiencia_{simulador}.png")
    plt.close()

def grafica_limite_amdahl(directorio):
    """
    Muestra el límite de speedup según Amdahl para diferentes fracciones paralelizables.
    """
    plt.figure(figsize=(14, 8))
    
    procesadores = np.array([1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024])
    fracciones = [0.50, 0.75, 0.90, 0.95, 0.99, 1.0]
    colores = ['#e74c3c', '#e67e22', '#f39c12', '#2ecc71', '#3498db', '#9b59b6']
    
    for f_p, color in zip(fracciones, colores):
        speedups = [speedup_teorico_amdahl(f_p, p) for p in procesadores]
        label = f'f_p = {f_p:.0%}' if f_p < 1.0 else 'f_p = 100% (ideal)'
        linestyle = '-' if f_p < 1.0 else '--'
        plt.plot(procesadores, speedups, 'o-', color=color, 
                label=label, linewidth=2.5, markersize=6, linestyle=linestyle)
    
    plt.xlabel('Número de Procesadores', fontsize=13, fontweight='bold')
    plt.ylabel('Speedup Máximo', fontsize=13, fontweight='bold')
    plt.title('Ley de Amdahl: Speedup Máximo Teórico\nvs Fracción Paralelizable',
              fontsize=15, fontweight='bold', pad=20)
    plt.legend(loc='best', frameon=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.xscale('log', base=2)
    plt.yscale('log', base=2)
    
    plt.tight_layout()
    plt.savefig(directorio / 'limite_amdahl_teorico.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: limite_amdahl_teorico.png")
    plt.close()

def generar_tabla_amdahl(datos_sec, datos_par, simulador, directorio):
    """
    Genera tabla con comparación de speedups.
    """
    if simulador not in datos_sec or simulador not in datos_par:
        return
    
    archivo = directorio / f'analisis_amdahl_{simulador}.txt'
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write(f"ANÁLISIS LEY DE AMDAHL - {simulador.upper()}\n")
        f.write("="*100 + "\n\n")
        
        for N in sorted(datos_sec[simulador].keys()):
            if N not in datos_par[simulador]:
                continue
            
            f.write(f"\n{ETIQUETAS_N[N]}\n")
            f.write("-"*100 + "\n")
            
            tiempo_sec = datos_sec[simulador][N]['time']
            f.write(f"Tiempo Secuencial: {tiempo_sec:.6f} segundos\n\n")
            
            # Estimar fracción paralelizable
            if 8 in datos_par[simulador][N]:
                f_p = calcular_fraccion_paralelizable(tiempo_sec, 
                                                      datos_par[simulador][N][8]['time'], 8)
            else:
                f_p = 0.95
            
            f.write(f"Fracción Paralelizable Estimada: {f_p:.2%}\n")
            f.write(f"Fracción Serial Estimada: {1-f_p:.2%}\n\n")
            
            f.write(f"{'Threads':<10} {'T_Paralelo(s)':<18} {'Speedup Real':<15} "
                   f"{'Speedup Amdahl':<18} {'Eficiencia(%)':<15}\n")
            f.write("-"*100 + "\n")
            
            for t in sorted(datos_par[simulador][N].keys()):
                t_par = datos_par[simulador][N][t]['time']
                sp_real = calcular_speedup_real(tiempo_sec, t_par)
                sp_amdahl = speedup_teorico_amdahl(f_p, t)
                eficiencia = (sp_real / t) * 100
                
                f.write(f"{t:<10} {t_par:<18.6f} {sp_real:<15.2f} "
                       f"{sp_amdahl:<18.2f} {eficiencia:<15.2f}\n")
            
            f.write("\n")
    
    print(f"✓ Tabla guardada: {archivo.name}")

def main():
    """
    Función principal.
    """
    print("="*80)
    print("ANÁLISIS LEY DE AMDAHL")
    print("="*80 + "\n")
    
    # Buscar archivos log
    logs_secuencial = list(Path('.').glob('resultados_secuencial_*.log'))
    logs_paralelo = list(Path('.').glob('resultados_simulaciones_*.log'))
    
    if not logs_secuencial:
        print("✗ No se encontraron logs secuenciales")
        return
    
    if not logs_paralelo:
        print("✗ No se encontraron logs paralelos")
        return
    
    # Parsear datos secuenciales
    print("Parseando logs secuenciales...")
    datos_sec = {}
    for log in logs_secuencial:
        print(f"  - {log}")
        data = parsear_log_secuencial(log)
        datos_sec.update(data)
    
    # Parsear datos paralelos
    print("\nParseando logs paralelos...")
    datos_par = {}
    for log in logs_paralelo:
        print(f"  - {log}")
        data = parsear_log_paralelo(log)
        for sim in data:
            if sim not in datos_par:
                datos_par[sim] = {}
            datos_par[sim].update(data[sim])
    
    # Crear directorio de salida
    directorio = Path('analisis_amdahl')
    directorio.mkdir(exist_ok=True)
    
    print(f"\n{'='*60}")
    print("Generando gráficas y análisis...")
    print(f"{'='*60}\n")
    
    # Generar gráfica teórica de límite de Amdahl
    grafica_limite_amdahl(directorio)
    
    # Analizar cada simulador
    for simulador in datos_sec.keys():
        if simulador in datos_par:
            print(f"\nAnalizando {simulador.upper()}:")
            grafica_amdahl_vs_real(datos_sec, datos_par, simulador, directorio)
            grafica_eficiencia_amdahl(datos_sec, datos_par, simulador, directorio)
            generar_tabla_amdahl(datos_sec, datos_par, simulador, directorio)
    
    print("\n" + "="*80)
    print(f"✓ ANÁLISIS COMPLETADO - Resultados en: {directorio}/")
    print("="*80)

if __name__ == "__main__":
    main()
