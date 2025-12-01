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

    // Sumamos solo los puntos interiores 
    uint64_t start = (N / nThreads) * id + 1; // Indice inicial (excluye i=0)
    uint64_t end = (id == nThreads-1) ? N : (N / nThreads) * (id + 1); // Indice final

    double local_sum = 0.0;

    // Calcular la suma local para este thread
    for(uint64_t i = start; i < end; ++i){
        double x = a + h * (double)i; // Punto medio del intervalo
        local_sum += f(x); // Sumar el valor de la función en el punto x
    }

    partial_sum[id] = local_sum;
    pthread_exit(NULL); // Terminar el thread
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
