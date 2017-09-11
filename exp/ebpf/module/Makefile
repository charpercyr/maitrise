
TARGET=ebpf

obj-m += $(TARGET).o

KMAKE = $(MAKE) -C /lib/modules/$(shell uname -r)/build M=$(shell pwd)

all:
	$(KMAKE) modules

install: all
	$(KMAKE) modules_install

clean:
	$(KMAKE) clean

test: all
	sudo insmod $(TARGET).ko

rmtest:
	sudo rmmod $(TARGET)