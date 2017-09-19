
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

#include <libelf.h>

void error(const char* msg)
{
    fprintf(stderr, "libinject.so error: %s\n", msg);
}

__attribute__((constructor)) void init()
{
    Elf* e = NULL;
    int fd = -1;
    Elf_Kind ek;

    if(elf_version(EV_CURRENT) == EV_NONE)
    {
        error("Could not start library");
        goto done;
    }

    if ((fd = open("/proc/self/exe", O_RDONLY, 0)) < 0)
    {
        error("Could not open self");
        goto done;
    }

    if((e = elf_begin(fd, ELF_C_READ, NULL)) == NULL)
    {
        error("Could not get elf handle");
        goto done;
    }

    ek = elf_kind(e);

    if(ek != ELF_K_ELF)
    {
        error("Invalid elf type");
        goto done;
    }

    

done:    
    if(fd != -1)
    {
        close(fd);
    }
    if(e)
    {
        elf_end(e);
    }
}