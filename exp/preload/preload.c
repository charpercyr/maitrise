#include <stdio.h>

void __attribute__((constructor)) on_init(void)
{
    printf("Hello World !\n");
}