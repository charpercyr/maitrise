
from bcc import BPF

bpf = BPF(src_file='ebpf.c')
bpf.attach_kprobe(event='to_probe', fn_name='probe_func')

try:
    while 1:
        pass
except KeyboardInterrupt:
    pass