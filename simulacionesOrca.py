import paramiko
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración del servidor
SERVIDOR_HOST = "zoo.urv.cat"
SERVIDOR_USER = "48136212-H"
NOMBRE_ARCHIVO = "practica"

# Parámetros de simulación
PARAM1_VALUES = [10000000000, 20000000000, 40000000000, 60000000000]
PARAM2_VALUES = [2, 4, 8, 16, 32, 64, 128, 256]

# Configuraciones de simulación
CONFIGURACIONES = [
    # {"simulador": "teen", "cpus": 32},  # teen está caído (1/12/2026)
    {"simulador": "orca", "cpus": 128}
]

def ejecutar_simulacion(ssh_client, simulador, cpus, param1, param2):
    """
    Ejecuta una simulación individual en el servidor remoto.
    
    Args:
        ssh_client: Cliente SSH conectado
        simulador: Nombre del simulador (teen u orca)
        cpus: Número de CPUs a usar
        param1: Primer parámetro de la simulación
        param2: Segundo parámetro de la simulación
    
    Returns:
        Tuple con información de la ejecución (config, stdout, stderr)
    """
    # Construir el comando srun
    comando = f"srun -p {simulador} -c {cpus} time ./{NOMBRE_ARCHIVO} {param1} {param2}"
    
    print(f"Ejecutando: {comando}")
    
    try:
        # Ejecutar el comando en el servidor
        stdin, stdout, stderr = ssh_client.exec_command(comando)
        
        # Esperar a que termine y obtener la salida
        salida_stdout = stdout.read().decode('utf-8')
        salida_stderr = stderr.read().decode('utf-8')
        codigo_salida = stdout.channel.recv_exit_status()
        
        config_info = f"[{simulador}|{cpus}CPUs] param1={param1}, param2={param2}"
        
        if codigo_salida == 0:
            print(f"✓ Completado: {config_info}")
        else:
            print(f"✗ Error: {config_info} (código: {codigo_salida})")
        
        return (config_info, salida_stdout, salida_stderr, codigo_salida)
        
    except Exception as e:
        print(f"✗ Excepción en {simulador}|{cpus}CPUs param1={param1}, param2={param2}: {str(e)}")
        return (f"[{simulador}|{cpus}CPUs] param1={param1}, param2={param2}", "", str(e), -1)

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

def ejecutar_simulaciones_paralelas(ssh_client, configuracion):
    """
    Ejecuta todas las combinaciones de parámetros para una configuración dada.
    Utiliza ThreadPoolExecutor para ejecutar simulaciones en paralelo.
    
    Args:
        ssh_client: Cliente SSH conectado
        configuracion: Diccionario con 'simulador' y 'cpus'
    
    Returns:
        Lista de resultados de todas las simulaciones
    """
    simulador = configuracion["simulador"]
    cpus = configuracion["cpus"]
    
    print(f"\n{'='*70}")
    print(f"Iniciando simulaciones con: simulador={simulador}, CPUs={cpus}")
    print(f"Total de combinaciones: {len(PARAM1_VALUES)} × {len(PARAM2_VALUES)} = {len(PARAM1_VALUES) * len(PARAM2_VALUES)}")
    print(f"{'='*70}\n")
    
    resultados = []
    
    # Crear lista de todas las combinaciones
    tareas = []
    for param1 in PARAM1_VALUES:
        for param2 in PARAM2_VALUES:
            tareas.append((param1, param2))
    
    # Ejecutar simulaciones en paralelo (máximo 8 hilos concurrentes para no saturar)
    with ThreadPoolExecutor(max_workers=8) as executor:
        # Enviar todas las tareas
        futures = {
            executor.submit(ejecutar_simulacion, ssh_client, simulador, cpus, p1, p2): (p1, p2)
            for p1, p2 in tareas
        }
        
        # Recoger resultados conforme se completan
        for future in as_completed(futures):
            resultado = future.result()
            resultados.append(resultado)
    
    print(f"\n✓ Completadas {len(resultados)} simulaciones para {simulador}\n")
    return resultados

def main():
    """
    Función principal que coordina la ejecución de todas las simulaciones.
    """
    print("="*70)
    print("SCRIPT DE AUTOMATIZACIÓN DE SIMULACIONES")
    print("="*70)
    
    # Solicitar contraseña al usuario
    import getpass
    password = getpass.getpass(f"Introduce la contraseña para {SERVIDOR_USER}@{SERVIDOR_HOST}: ")
    
    try:
        # Conectar al servidor
        ssh_client = conectar_servidor(password)
        
        # Almacenar todos los resultados
        todos_resultados = []
        
        # Ejecutar simulaciones para cada configuración
        for config in CONFIGURACIONES:
            resultados = ejecutar_simulaciones_paralelas(ssh_client, config)
            todos_resultados.extend(resultados)
        
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
        with open("resultados_simulaciones.log", "w", encoding="utf-8") as f:
            f.write("RESULTADOS DE SIMULACIONES\n")
            f.write("="*70 + "\n\n")
            for config_info, stdout, stderr, codigo in todos_resultados:
                f.write(f"\nConfiguración: {config_info}\n")
                f.write(f"Código de salida: {codigo}\n")
                f.write(f"STDOUT:\n{stdout}\n")
                if stderr:
                    f.write(f"STDERR:\n{stderr}\n")
                f.write("-"*70 + "\n")
        
        print(f"\n✓ Resultados guardados en: resultados_simulaciones.log")
        
    except KeyboardInterrupt:
        print("\n\n✗ Ejecución interrumpida por el usuario")
    except Exception as e:
        print(f"\n✗ Error durante la ejecución: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
