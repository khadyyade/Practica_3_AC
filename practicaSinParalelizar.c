// Integració numèrica càlcul de PI
#define _GNU_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <time.h>
#include <math.h>
#include <assert.h>
#define NPUNTS (60000000000LL)
#define A (0.0)
#define B (1.0)
static inline double f(double x){ return 4.0/(1.0 + x*x); }
int main(int na, char* arg[]){
if (na != 2) {
    fprintf(stderr, "Error: Número incorrecto de argumentos\n");
    fprintf(stderr, "Uso: %s <N>\n", arg[0]);
    fprintf(stderr, "Ejemplo: %s 10000000000\n", arg[0]);
    return 1;
}
uint64_t N = atoll(arg[1]);
if (N <= 0 || N > NPUNTS) {
    fprintf(stderr, "Error: N debe estar entre 1 y %lld\n", NPUNTS);
    return 1;
}
double a = A;
double b = B;
printf("N=%lld [%.6f, %.6f]\n", N, a, b);

// Medir tiempo de inicio
clock_t start_time = clock();

const double h = (b - a) / (double)N;
// Suma interior
double sum = 0.0;
for (uint64_t i=1;i<N;++i){
double x = a + h*(double)i;
sum += f(x);
}
double integral = h * (0.5*f(a) + sum + 0.5*f(b));

// Medir tiempo de finalización
clock_t end_time = clock();
double secs = (double)(end_time - start_time) / CLOCKS_PER_SEC;

printf("Integral ~ %.12f error = %.3e\n", integral, fabs(integral - M_PI));
printf("Time = %.6f sec\n", secs);
return 0;
}