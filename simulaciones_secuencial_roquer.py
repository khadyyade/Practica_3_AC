import paramiko
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración del servidor
SERVIDOR_HOST = "zoo.urv.cat"
SERVIDOR_USER = "48136212-H"
NOMBRE_ARCHIVO = "practicaSinParalelizar"

# Parámetros de simulación (solo valores de N)
N_VALUES = [10000000000, 20000000000, 40000000000, 60000000000]

# Configuración de Roquer
SIMULADOR = "roquer"
CPUS = 12

def ejecutar_simulacion_secuencial(ssh_client, simulador, cpus, N):
    """
    Ejecuta una simulación secuencial en el servidor remoto.
    
    Args:
        ssh_client: Cliente SSH conectado
        simulador: Nombre del simulador (roquer)
        cpus: Número de CPUs a reservar
        N: Número de iteraciones
    
    Returns:
        Tuple con información de la ejecución (config, stdout, stderr)
    """
    # Construir el comando srun para la versión secuencial
    comando = f"srun -p {simulador} -c {cpus} time ./{NOMBRE_ARCHIVO} {N}"
    
    print(f"Ejecutando: {comando}")
    
    try:
        # Ejecutar el comando en el servidor
        stdin, stdout, stderr = ssh_client.exec_command(comando)
        
        # Esperar a que termine y obtener la salida
        salida_stdout = stdout.read().decode('utf-8')
        salida_stderr = stderr.read().decode('utf-8')
        codigo_salida = stdout.channel.recv_exit_status()
        
        config_info = f"[{simulador}|{cpus}CPUs|SECUENCIAL] N={N}"
        
        if codigo_salida == 0:
            print(f"✓ Completado: {config_info}")
        else:
            print(f"✗ Error: {config_info} (código: {codigo_salida})")
        
        return (config_info, salida_stdout, salida_stderr, codigo_salida)
        
    except Exception as e:
        print(f"✗ Excepción en {simulador}|{cpus}CPUs N={N}: {str(e)}")
        return (f"[{simulador}|{cpus}CPUs|SECUENCIAL] N={N}", "", str(e), -1)

def conectar_servidor(password):
    """
    Establece conexión SSH con el servidor remoto.
    
    Args:
        password: Contraseña para autenticación SSH
    
    Returns:
        Cliente SSH conectado
    """
    print(f"Conectando a {SERVIDOR_HOST}...")
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh_client.connect(
            hostname=SERVIDOR_HOST,
            username=SERVIDOR_USER,
            password=password,
            timeout=30
        )
        print("✓ Conexión SSH establecida exitosamente")
        return ssh_client
    except Exception as e:
        print(f"✗ Error al conectar: {str(e)}")
        raise

def ejecutar_simulaciones_secuenciales(ssh_client):
    """
    Ejecuta todas las simulaciones secuenciales para diferentes valores de N.
    
    Args:
        ssh_client: Cliente SSH conectado
    
    Returns:
        Lista de resultados de todas las simulaciones
    """
    print(f"\n{'='*70}")
    print(f"SIMULACIONES SECUENCIALES - Simulador: {SIMULADOR.upper()}, CPUs: {CPUS}")
    print(f"Total de ejecuciones: {len(N_VALUES)}")
    print(f"{'='*70}\n")
    
    resultados = []
    
    # Ejecutar cada simulación secuencialmente (una tras otra)
    for N in N_VALUES:
        resultado = ejecutar_simulacion_secuencial(ssh_client, SIMULADOR, CPUS, N)
        resultados.append(resultado)
        # Pequeña pausa entre ejecuciones
        time.sleep(1)
    
    print(f"\n✓ Completadas {len(resultados)} simulaciones secuenciales\n")
    return resultados

def main():
    """
    Función principal que coordina la ejecución de todas las simulaciones.
    """
    print("="*70)
    print("SCRIPT DE AUTOMATIZACIÓN - CÓDIGO SECUENCIAL (Roquer)")
    print("="*70)
    
    # Solicitar contraseña al usuario
    import getpass
    password = getpass.getpass(f"Introduce la contraseña para {SERVIDOR_USER}@{SERVIDOR_HOST}: ")
    
    try:
        # Conectar al servidor
        ssh_client = conectar_servidor(password)
        
        # Ejecutar simulaciones secuenciales
        todos_resultados = ejecutar_simulaciones_secuenciales(ssh_client)
        
        # Cerrar conexión SSH
        ssh_client.close()
        print("\n✓ Conexión SSH cerrada")
        
        # Resumen final
        print("\n" + "="*70)
        print("RESUMEN DE EJECUCIÓN")
        print("="*70)
        exitosos = sum(1 for r in todos_resultados if r[3] == 0)
        fallidos = len(todos_resultados) - exitosos
        print(f"Total de simulaciones ejecutadas: {len(todos_resultados)}")
        print(f"Exitosas: {exitosos}")
        print(f"Fallidas: {fallidos}")
        
        # Guardar resultados en archivo log
        nombre_log = f"resultados_secuencial_{SIMULADOR}.log"
        with open(nombre_log, "w", encoding="utf-8") as f:
            f.write("RESULTADOS DE SIMULACIONES SECUENCIALES\n")
            f.write("="*70 + "\n\n")
            for config_info, stdout, stderr, codigo in todos_resultados:
                f.write(f"\nConfiguración: {config_info}\n")
                f.write(f"Código de salida: {codigo}\n")
                f.write(f"STDOUT:\n{stdout}\n")
                if stderr:
                    f.write(f"STDERR:\n{stderr}\n")
                f.write("-"*70 + "\n")
        
        print(f"\n✓ Resultados guardados en: {nombre_log}")
        
    except KeyboardInterrupt:
        print("\n\n✗ Ejecución interrumpida por el usuario")
    except Exception as e:
        print(f"\n✗ Error durante la ejecución: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
