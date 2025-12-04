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
    Returns: dict {simulador: {N: {'time': float, 'error': float}}}
    """
    datos = {}
    
    with open(archivo_log, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
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

def grafica_comparacion_tiempos_secuencial(datos, directorio):
    """
    Compara tiempos de ejecución secuencial entre Roquer y Orca.
    """
    plt.figure(figsize=(14, 8))
    
    simuladores = sorted(datos.keys())
    colores_sim = {'roquer': '#e74c3c', 'orca': '#3498db'}
    
    for simulador in simuladores:
        N_values = sorted(datos[simulador].keys())
        tiempos = [datos[simulador][N]['time'] for N in N_values]
        
        plt.plot(N_values, tiempos, 'o-', 
                color=colores_sim.get(simulador, '#666'),
                label=simulador.upper(),
                linewidth=3, markersize=10)
    
    plt.xlabel('Número de Iteraciones (N)', fontsize=13, fontweight='bold')
    plt.ylabel('Tiempo de Ejecución (segundos)', fontsize=13, fontweight='bold')
    plt.title('Comparación Roquer vs Orca - Código Secuencial\nTiempo de Ejecución vs Tamaño del Problema',
              fontsize=15, fontweight='bold', pad=20)
    plt.legend(loc='best', frameon=True, shadow=True, fontsize=12)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # Etiquetas en eje X
    N_values = sorted(list(datos[list(datos.keys())[0]].keys()))
    plt.xticks(N_values, [ETIQUETAS_N[n] for n in N_values])
    
    plt.tight_layout()
    plt.savefig(directorio / 'comparacion_tiempos_secuencial.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: comparacion_tiempos_secuencial.png")
    plt.close()

def grafica_comparacion_precision_secuencial(datos, directorio):
    """
    Compara precisión (error) entre Roquer y Orca.
    """
    plt.figure(figsize=(14, 8))
    
    simuladores = sorted(datos.keys())
    colores_sim = {'roquer': '#e74c3c', 'orca': '#3498db'}
    
    for simulador in simuladores:
        N_values = sorted(datos[simulador].keys())
        errores = [datos[simulador][N]['error'] for N in N_values]
        
        plt.plot(N_values, errores, 'o-', 
                color=colores_sim.get(simulador, '#666'),
                label=simulador.upper(),
                linewidth=3, markersize=10)
    
    plt.xlabel('Número de Iteraciones (N)', fontsize=13, fontweight='bold')
    plt.ylabel('Error Absoluto (menor = mejor)', fontsize=13, fontweight='bold')
    plt.title('Comparación Roquer vs Orca - Código Secuencial\nPrecisión del Cálculo de π',
              fontsize=15, fontweight='bold', pad=20)
    plt.legend(loc='best', frameon=True, shadow=True, fontsize=12)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.yscale('log')
    
    # Invertir eje Y para que menor error esté arriba
    plt.gca().invert_yaxis()
    
    # Etiquetas en eje X
    N_values = sorted(list(datos[list(datos.keys())[0]].keys()))
    plt.xticks(N_values, [ETIQUETAS_N[n] for n in N_values])
    
    plt.tight_layout()
    plt.savefig(directorio / 'comparacion_precision_secuencial.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: comparacion_precision_secuencial.png")
    plt.close()

def grafica_ratio_rendimiento(datos, directorio):
    """
    Muestra el ratio de rendimiento Roquer/Orca.
    """
    if 'roquer' not in datos or 'orca' not in datos:
        print("⚠ Necesitas datos de ambos simuladores para calcular el ratio")
        return
    
    plt.figure(figsize=(14, 8))
    
    N_values = sorted(datos['roquer'].keys())
    ratios = []
    
    for N in N_values:
        if N in datos['orca']:
            ratio = datos['roquer'][N]['time'] / datos['orca'][N]['time']
            ratios.append(ratio)
        else:
            ratios.append(0)
    
    bars = plt.bar(range(len(N_values)), ratios, color='#9b59b6', alpha=0.7, edgecolor='black')
    
    # Línea de referencia (ratio = 1)
    plt.axhline(y=1, color='red', linestyle='--', linewidth=2, alpha=0.7,
                label='Mismo rendimiento')
    
    # Colorear barras según si Roquer es más rápido o más lento
    for i, (bar, ratio) in enumerate(zip(bars, ratios)):
        if ratio > 1:
            bar.set_color('#e74c3c')  # Roquer más lento
        else:
            bar.set_color('#2ecc71')  # Roquer más rápido
    
    plt.xlabel('Tamaño del Problema', fontsize=13, fontweight='bold')
    plt.ylabel('Ratio Tiempo (Roquer / Orca)', fontsize=13, fontweight='bold')
    plt.title('Ratio de Rendimiento: Roquer vs Orca (Código Secuencial)\nRatio > 1: Orca más rápido | Ratio < 1: Roquer más rápido',
              fontsize=15, fontweight='bold', pad=20)
    plt.xticks(range(len(N_values)), [ETIQUETAS_N[n] for n in N_values])
    plt.legend(loc='best', frameon=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # Añadir valores sobre las barras
    for i, (ratio, n) in enumerate(zip(ratios, N_values)):
        if ratio > 0:
            plt.text(i, ratio + 0.02, f'{ratio:.2f}x', ha='center', va='bottom', 
                    fontweight='bold', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(directorio / 'ratio_rendimiento_secuencial.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfica guardada: ratio_rendimiento_secuencial.png")
    plt.close()

def generar_tabla_comparacion(datos, directorio):
    """
    Genera tabla comparativa entre simuladores.
    """
    archivo = directorio / 'comparacion_secuencial.txt'
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write("COMPARACIÓN ROQUER VS ORCA - CÓDIGO SECUENCIAL\n")
        f.write("="*100 + "\n\n")
        
        simuladores = sorted(datos.keys())
        N_values = sorted(datos[simuladores[0]].keys())
        
        for N in N_values:
            f.write(f"\n{ETIQUETAS_N[N]}\n")
            f.write("-"*100 + "\n")
            f.write(f"{'Simulador':<15} {'Tiempo (s)':<15} {'Error':<18} {'Integral':<18}\n")
            f.write("-"*100 + "\n")
            
            for sim in simuladores:
                if N in datos[sim]:
                    tiempo = datos[sim][N]['time']
                    error = datos[sim][N]['error']
                    integral = datos[sim][N]['integral']
                    f.write(f"{sim.upper():<15} {tiempo:<15.6f} {error:<18.3e} {integral:<18.12f}\n")
            
            # Calcular diferencia
            if len(simuladores) == 2 and N in datos[simuladores[0]] and N in datos[simuladores[1]]:
                t1 = datos[simuladores[0]][N]['time']
                t2 = datos[simuladores[1]][N]['time']
                diff_pct = abs(t1 - t2) / max(t1, t2) * 100
                mas_rapido = simuladores[0] if t1 < t2 else simuladores[1]
                f.write(f"\nDiferencia: {diff_pct:.2f}% | Más rápido: {mas_rapido.upper()}\n")
            
            f.write("\n")
    
    print(f"✓ Tabla guardada: {archivo.name}")

def main():
    """
    Función principal.
    """
    print("="*80)
    print("COMPARACIÓN ROQUER vs ORCA - CÓDIGO SECUENCIAL")
    print("="*80 + "\n")
    
    # Buscar archivos log secuenciales
    logs_secuencial = list(Path('.').glob('resultados_secuencial_*.log'))
    
    if not logs_secuencial:
        print("✗ No se encontraron logs secuenciales")
        print("  Archivos esperados: resultados_secuencial_roquer.log, resultados_secuencial_orca.log")
        return
    
    # Parsear datos
    print("Parseando logs secuenciales...")
    datos = {}
    for log in logs_secuencial:
        print(f"  - {log}")
        data = parsear_log_secuencial(log)
        datos.update(data)
    
    if not datos:
        print("✗ No se pudieron parsear datos de los logs")
        return
    
    print(f"\nSimuladores encontrados: {', '.join([s.upper() for s in datos.keys()])}")
    
    # Crear directorio de salida
    directorio = Path('comparacion_secuencial')
    directorio.mkdir(exist_ok=True)
    
    print(f"\n{'='*60}")
    print("Generando gráficas comparativas...")
    print(f"{'='*60}\n")
    
    # Generar gráficas
    grafica_comparacion_tiempos_secuencial(datos, directorio)
    grafica_comparacion_precision_secuencial(datos, directorio)
    grafica_ratio_rendimiento(datos, directorio)
    generar_tabla_comparacion(datos, directorio)
    
    print("\n" + "="*80)
    print(f"✓ ANÁLISIS COMPLETADO - Resultados en: {directorio}/")
    print("="*80)

if __name__ == "__main__":
    main()
