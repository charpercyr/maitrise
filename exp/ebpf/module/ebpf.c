#include <linux/init.h>
#include <linux/module.h>
#include <linux/filter.h>

static volatile int result = 0;
BPF_CALL_1(test_set_result, int, res)
{
    result = res;
    return 0;
}

void to_probe(void)
{
    if(result)
    {
        printk(KERN_INFO "ebpf: Result !\n");
    }
    result = 0;
}
EXPORT_SYMBOL(to_probe);

__init int start(void)
{
    printk(KERN_INFO "ebpf: Hello World !\n");
    return 0;
}
module_init(start);

__exit void end(void)
{
    
}
module_exit(end);