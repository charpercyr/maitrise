
#include <iostream>

#include <dyntrace/fasttp/fasttp.hpp>

extern void* addresses[];

int main()
{
    for(;;) asm("pause");
    return 0;
}