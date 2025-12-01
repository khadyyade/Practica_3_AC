import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configuración de estilo para gráficas bonitas
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['lines.linewidth'] = 2.5
plt.rcParams['lines.markersize'] = 8

# Colores para cada tamaño de N
COLORES_N = {
    10000000000: '#e74c3c',   # Rojo
    20000000000: '#3498db',   # Azul
    40000000000: '#2ecc71',   # Verde
    60000000000: '#f39c12'    # Naranja
}

# Etiquetas legibles para N
ETIQUETAS_N = {
    10000000000: 'N = 10G',
    20000000000: 'N = 20G',
    40000000000: 'N = 40G',
    60000000000: 'N = 60G'
}

def parsear_log(archivo_log):
    """
    Extrae los datos de un archivo log de simulaciones.
    
    Returns:
        dict: Diccionario con estructura {N: {nThreads: {'time': float, 'error': float}}}
    """
    datos = {}
    
    with open(archivo_log, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Expresión regular para capturar configuración y resultados
    patron = r'Configuración: \[(\w+)\|(\d+)CPUs\] param1=(\d+), param2=(\d+)\s+' \
             r'Código de salida: (\d+)\s+' \
             r'STDOUT:\s+N=(\d+)\s+Threads=(\d+)\s+' \
             r'Integral = ([\d.]+)\s+error = ([\d.e+-]+)\s+' \
             r'Time = ([\d.]+) sec'
    
    matches = re.finditer(patron, contenido)
    
    for match in matches:
        simulador = match.group(1)
        cpus = int(match.group(2))
        param1 = int(match.group(3))
        param2 = int(match.group(4))
        codigo_salida = int(match.group(5))
        N = int(match.group(6))
        nThreads = int(match.group(7))
        integral = float(match.group(8))
        error = float(match.group(9))
        time = float(match.group(10))
        
        # Solo considerar ejecuciones exitosas
        if codigo_salida == 0:
            # Estructura: datos[simulador][N][nThreads]
            if simulador not in datos:
                datos[simulador] = {}
            if N not in datos[simulador]:
                datos[simulador][N] = {}
            
            datos[simulador][N][nThreads] = {
                'time': time,
                'error': error,
                'integral': integral,
                'cpus': cpus
            }
    
    return datos

def extraer_tiempo_secuencial(datos, simulador):
    """
    Extrae el tiempo de ejecución con 2 threads (más cercano a secuencial)
    para calcular el speedup.
    
    Returns:
        dict: {N: tiempo_secuencial}
    """
    tiempos_base = {}
    
    if simulador in datos:
        for N in datos[simulador]:
            if 2 in datos[simulador][N]:
                tiempos_base[N] = datos[simulador][N][2]['time']
    
    return tiempos_base

def grafica_tiempo_ejecucion(datos, simulador, archivo_salida):
    """
    Genera gráfica de tiempo de ejecución vs número de threads.
    """
    plt.figure(figsize=(14, 8))
    
    if simulador not in datos:
        print(f"No hay datos para el simulador {simulador}")
        return
    
    # Para cada valor de N, graficar tiempo vs threads
    for N in sorted(datos[simulador].keys()):
        threads = sorted(datos[simulador][N].keys())
        tiempos = [datos[simulador][N][t]['time'] for t in threads]
        
        plt.plot(threads, tiempos, 
                marker='o', 
                color=COLORES_N[N],
                label=ETIQUETAS_N[N],
                linewidth=2.5,
                markersize=8)
    
    plt.xlabel('Número de Threads', fontsize=13, fontweight='bold')
    plt.ylabel('Tiempo de Ejecución (segundos)', fontsize=13, fontweight='bold')
    plt.title(f'Tiempo de Ejecución vs Número de Threads\nSimulador: {simulador.upper()}', 
              fontsize=15, fontweight='bold', pad=20)
    plt.legend(loc='best', frameon=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.xscale('log', base=2)
    plt.yscale('log')
    
    # Configurar ticks en el eje X para potencias de 2
    plt.xticks([2, 4, 8, 16, 32, 64, 128, 256], 
               ['2', '4', '8', '16', '32', '64', '128', '256'])
    
    plt.tight_layout()
    plt.savefig(archivo_salida, dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: {archivo_salida}")
    plt.close()

def grafica_speedup(datos, simulador, archivo_salida):
    """
    Genera gráfica de speedup vs número de threads.
    Speedup = Tiempo_base / Tiempo_actual
    
    Speedup > 1: La versión paralela es MÁS RÁPIDA que la base
    Speedup = 1: Igual rendimiento
    Speedup < 1: La versión paralela es MÁS LENTA (hay overhead)
    """
    plt.figure(figsize=(14, 8))
    
    if simulador not in datos:
        print(f"No hay datos para el simulador {simulador}")
        return
    
    tiempos_base = extraer_tiempo_secuencial(datos, simulador)
    
    # Para cada valor de N, graficar speedup vs threads
    for N in sorted(datos[simulador].keys()):
        if N not in tiempos_base:
            continue
        
        threads = sorted(datos[simulador][N].keys())
        tiempo_base = tiempos_base[N]
        speedups = [tiempo_base / datos[simulador][N][t]['time'] for t in threads]
        
        plt.plot(threads, speedups, 
                marker='o', 
                color=COLORES_N[N],
                label=ETIQUETAS_N[N],
                linewidth=2.5,
                markersize=8)
    
    # Línea de referencia en speedup = 1 (sin mejora ni empeoramiento)
    plt.axhline(y=1, color='red', linestyle=':', linewidth=2, alpha=0.7, 
                label='Sin mejora (Speedup=1)')
    
    # Línea de speedup ideal (lineal): con N threads, N veces más rápido
    threads_ideal = [2, 4, 8, 16, 32, 64, 128, 256]
    # Normalizar al primer valor (2 threads)
    speedup_ideal = [t/2 for t in threads_ideal]  # Relativo a 2 threads
    plt.plot(threads_ideal, speedup_ideal, 
            'k--', 
            label='Speedup Ideal (Escalado lineal)',
            linewidth=2.5,
            alpha=0.7)
    
    plt.xlabel('Número de Threads', fontsize=13, fontweight='bold')
    plt.ylabel('Speedup (Tiempo_base / Tiempo_actual)', fontsize=13, fontweight='bold')
    plt.title(f'Speedup vs Número de Threads\nSimulador: {simulador.upper()} (Base: 2 threads)\nSpeedup > 1 = Más rápido | Speedup < 1 = Más lento (overhead)', 
              fontsize=14, fontweight='bold', pad=20)
    plt.legend(loc='best', frameon=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.xscale('log', base=2)
    
    # Configurar ticks en el eje X
    plt.xticks([2, 4, 8, 16, 32, 64, 128, 256], 
               ['2', '4', '8', '16', '32', '64', '128', '256'])
    
    plt.tight_layout()
    plt.savefig(archivo_salida, dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: {archivo_salida}")
    plt.close()

def grafica_eficiencia(datos, simulador, archivo_salida):
    """
    Genera gráfica de uso de CPU vs número de threads.
    Muestra el tiempo de CPU real usado (refleja consumo de recursos).
    """
    plt.figure(figsize=(14, 8))
    
    if simulador not in datos:
        print(f"No hay datos para el simulador {simulador}")
        return
    
    # Para cada valor de N, graficar tiempo CPU vs threads
    for N in sorted(datos[simulador].keys()):
        threads = sorted(datos[simulador][N].keys())
        tiempos = [datos[simulador][N][t]['time'] for t in threads]
        
        # Mostrar el tiempo real que refleja el consumo de CPU
        plt.plot(threads, tiempos, 
                marker='o', 
                color=COLORES_N[N],
                label=ETIQUETAS_N[N],
                linewidth=2.5,
                markersize=8)
    
    plt.xlabel('Número de Threads', fontsize=13, fontweight='bold')
    plt.ylabel('Tiempo de CPU Usado (segundos)', fontsize=13, fontweight='bold')
    plt.title(f'Consumo de Recursos (Tiempo CPU) vs Número de Threads\nSimulador: {simulador.upper()}\n(Más threads = mayor consumo de recursos)', 
              fontsize=15, fontweight='bold', pad=20)
    plt.legend(loc='best', frameon=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.xscale('log', base=2)
    plt.yscale('log')
    
    # Configurar ticks en el eje X
    plt.xticks([2, 4, 8, 16, 32, 64, 128, 256], 
               ['2', '4', '8', '16', '32', '64', '128', '256'])
    
    plt.tight_layout()
    plt.savefig(archivo_salida, dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: {archivo_salida}")
    plt.close()

def grafica_precision(datos, simulador, archivo_salida):
    """
    Genera gráfica de precisión vs número de threads.
    Eje Y invertido: mayor precisión (menor error) aparece arriba.
    """
    plt.figure(figsize=(14, 8))
    
    if simulador not in datos:
        print(f"No hay datos para el simulador {simulador}")
        return
    
    # Para cada valor de N, graficar precisión vs threads
    for N in sorted(datos[simulador].keys()):
        threads = sorted(datos[simulador][N].keys())
        errores = [datos[simulador][N][t]['error'] for t in threads]
        
        plt.plot(threads, errores, 
                marker='o', 
                color=COLORES_N[N],
                label=ETIQUETAS_N[N],
                linewidth=2.5,
                markersize=8)
    
    plt.xlabel('Número de Threads', fontsize=13, fontweight='bold')
    plt.ylabel('Error Absoluto (menor = mejor)', fontsize=13, fontweight='bold')
    plt.title(f'Precisión del Cálculo de π vs Número de Threads\nSimulador: {simulador.upper()}\n(Menor error = Mayor precisión)', 
              fontsize=15, fontweight='bold', pad=20)
    plt.legend(loc='best', frameon=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.xscale('log', base=2)
    plt.yscale('log')
    
    # INVERTIR EL EJE Y para que menor error aparezca arriba
    plt.gca().invert_yaxis()
    
    # Configurar ticks en el eje X
    plt.xticks([2, 4, 8, 16, 32, 64, 128, 256], 
               ['2', '4', '8', '16', '32', '64', '128', '256'])
    
    plt.tight_layout()
    plt.savefig(archivo_salida, dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: {archivo_salida}")
    plt.close()

def grafica_escalabilidad_fuerte(datos, simulador, archivo_salida):
    """
    Gráfica de escalabilidad fuerte: tiempo para diferentes threads con N fijo.
    Muestra las 4 curvas de N en una sola gráfica.
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Escalabilidad Fuerte - Simulador: {simulador.upper()}', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    if simulador not in datos:
        print(f"No hay datos para el simulador {simulador}")
        return
    
    for idx, N in enumerate(sorted(datos[simulador].keys())):
        ax = axes[idx // 2, idx % 2]
        
        threads = sorted(datos[simulador][N].keys())
        tiempos = [datos[simulador][N][t]['time'] for t in threads]
        
        ax.plot(threads, tiempos, 
               marker='o', 
               color=COLORES_N[N],
               linewidth=3,
               markersize=10)
        
        ax.set_xlabel('Número de Threads', fontsize=12, fontweight='bold')
        ax.set_ylabel('Tiempo (segundos)', fontsize=12, fontweight='bold')
        ax.set_title(f'{ETIQUETAS_N[N]} iteraciones', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xscale('log', base=2)
        ax.set_yscale('log')
        ax.set_xticks([2, 4, 8, 16, 32, 64, 128, 256])
        ax.set_xticklabels(['2', '4', '8', '16', '32', '64', '128', '256'])
    
    plt.tight_layout()
    plt.savefig(archivo_salida, dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: {archivo_salida}")
    plt.close()

def generar_tabla_resumen(datos, simulador, archivo_salida):
    """
    Genera una tabla resumen en formato texto con los resultados.
    """
    if simulador not in datos:
        return
    
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write(f"TABLA RESUMEN DE RESULTADOS - SIMULADOR: {simulador.upper()}\n")
        f.write("="*100 + "\n\n")
        
        tiempos_base = extraer_tiempo_secuencial(datos, simulador)
        
        for N in sorted(datos[simulador].keys()):
            f.write(f"\n{ETIQUETAS_N[N]} iteraciones\n")
            f.write("-"*100 + "\n")
            f.write(f"{'Threads':<10} {'Tiempo (s)':<15} {'Speedup':<12} {'Eficiencia (%)':<18} {'Error':<15}\n")
            f.write("-"*100 + "\n")
            
            tiempo_base = tiempos_base.get(N, 1)
            
            for t in sorted(datos[simulador][N].keys()):
                tiempo = datos[simulador][N][t]['time']
                speedup = tiempo_base / tiempo
                eficiencia = (speedup / t) * 100
                error = datos[simulador][N][t]['error']
                
                f.write(f"{t:<10} {tiempo:<15.6f} {speedup:<12.2f} {eficiencia:<18.2f} {error:<15.3e}\n")
            
            f.write("\n")
    
    print(f"✓ Tabla resumen guardada: {archivo_salida}")

def main():
    """
    Función principal que coordina la generación de todas las gráficas.
    """
    print("="*80)
    print("GENERACIÓN DE GRÁFICAS DE RENDIMIENTO")
    print("="*80 + "\n")
    
    # Buscar archivos log
    archivos_log = list(Path('.').glob('resultados_simulaciones*.log'))
    
    if not archivos_log:
        print("✗ No se encontraron archivos log en el directorio actual")
        return
    
    # Procesar cada archivo log
    for archivo_log in archivos_log:
        print(f"\nProcesando: {archivo_log}")
        datos = parsear_log(archivo_log)
        
        # Determinar simuladores disponibles
        simuladores = list(datos.keys())
        print(f"Simuladores encontrados: {', '.join(simuladores)}")
        
        # Generar gráficas para cada simulador
        for simulador in simuladores:
            print(f"\n{'='*60}")
            print(f"Generando gráficas para: {simulador.upper()}")
            print(f"{'='*60}")
            
            # Crear directorio para las gráficas si no existe
            directorio = Path(f"graficas_{simulador}")
            directorio.mkdir(exist_ok=True)
            
            # Generar todas las gráficas
            grafica_tiempo_ejecucion(datos, simulador, 
                                    directorio / f"tiempo_ejecucion_{simulador}.png")
            
            grafica_speedup(datos, simulador, 
                           directorio / f"speedup_{simulador}.png")
            
            grafica_eficiencia(datos, simulador, 
                             directorio / f"eficiencia_{simulador}.png")
            
            grafica_precision(datos, simulador, 
                            directorio / f"precision_{simulador}.png")
            
            grafica_escalabilidad_fuerte(datos, simulador, 
                                        directorio / f"escalabilidad_fuerte_{simulador}.png")
            
            # Generar tabla resumen
            generar_tabla_resumen(datos, simulador, 
                                directorio / f"resumen_{simulador}.txt")
            
            print(f"\n✓ Todas las gráficas de {simulador.upper()} generadas en: {directorio}/")
    
    print("\n" + "="*80)
    print("✓ PROCESO COMPLETADO")
    print("="*80)

if __name__ == "__main__":
    main()
