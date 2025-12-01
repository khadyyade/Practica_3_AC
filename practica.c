#define _GNU_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <time.h>
#include <math.h>
#include <assert.h>
#include <pthread.h>

static inline double f(double x){ return 4.0/(1.0 + x*x); }

uint64_t N;             // Numero de intervalos
int nThreads;           // Numero de threads
double a = 0.0;         // Limite inferior
double b = 1.0;         // Limite superior
double h;               // Tamaño del intervalo
double *partial_sum;    // Suma parcial por thread

// Funcion que ejecuta cada thread
void* funcionThread(void* arg){
    long id = (long)arg;
    
    // Calcular el rango de indices para este thread
    // Los threads procesarán los puntos interiores (i = 1 hasta N-1)
    // Los puntos extremos (i=0 y i=N) se manejan en main
    uint64_t puntos_interiores = N - 1;
    uint64_t elementos_por_thread = puntos_interiores / nThreads;
    uint64_t start = elementos_por_thread * id + 1;
    uint64_t end = elementos_por_thread * (id + 1) + 1;
    
    // El último thread debe procesar hasta N-1 (incluye residuo de la división)
    if (id == nThreads - 1) {
        end = N;
    }

    double local_sum = 0.0;

    // Calcular la suma local para este thread (solo puntos interiores)
    for(uint64_t i = start; i < end; ++i){
        double x = a + h * (double)i;
        local_sum += f(x);
    }

    partial_sum[id] = local_sum;
    pthread_exit(NULL);
}



int main(int na, char* arg[]){
    assert(na == 3);

    // Lectura y validacion de argumentos (N y nThreads)
    N = atoll(arg[1]);
    nThreads = atoi(arg[2]);
    assert(N > 0);
    assert(nThreads > 0);

    printf("N=%lld  Threads=%d\n", N, nThreads);

    // Calculo del tamaño del intervalo
    h = (b - a) / (double)N;

    // Reserva de memoria para las sumas parciales
    partial_sum = calloc(nThreads, sizeof(double));

   // Crear y lanzar los threads
    pthread_t threads[nThreads];

    // Medir el tiempo de comienzo
    double start_time = clock();

    for(long t = 0; t < nThreads; t++)
        pthread_create(&threads[t], NULL, funcionThread, (void*)t);

    // Esperar a que todos los threads terminen
    for(int t = 0; t < nThreads; t++)
        pthread_join(threads[t], NULL);

    // Sumar las sumas parciales de cada thread
    double sum = 0.0;
    for(int t = 0; t < nThreads; t++)
        sum += partial_sum[t];

    // Valor final del integral
    double integral = h * (0.5*f(a) + sum + 0.5*f(b));


    // Medir el tiempo de finalización
    double end_time = clock();

    // Calculo del tiempo transcurrido 
    double secs = (end_time - start_time) / CLOCKS_PER_SEC;

    printf("Integral = %.12f  error = %.3e\n", integral, fabs(integral - M_PI));
    printf("Time = %.6f sec\n", secs);

    // Liberar memoria
    free(partial_sum);
    return 0;
}
