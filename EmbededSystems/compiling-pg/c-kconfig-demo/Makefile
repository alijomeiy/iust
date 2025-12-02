CC      := gcc
CFLAGS  := -Wall -Wextra -Iinclude
OBJDIR  := build

-include .config

SRCS := src/main.c

ifeq ($(CONFIG_FEATURE_HELLO),y)
SRCS += src/feature_hello.c
endif

ifeq ($(CONFIG_FEATURE_MATH),y)
SRCS += src/feature_math.c
endif

OBJS := $(SRCS:src/%.c=$(OBJDIR)/%.o)

.PHONY: all
all: app

app: $(OBJDIR) config.h $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS)

$(OBJDIR):
	mkdir -p $(OBJDIR)

config.h: .config
	./scripts/genconfig.sh .config include/config.h
	@# یه لینک نسبی یا کپی برای راحتی این فایل rule
	@ln -sf ../include/config.h config.h 2>/dev/null || true

$(OBJDIR)/%.o: src/%.c include/config.h
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: menuconfig
menuconfig:
	kconfig-mconf Kconfig

.PHONY: clean
clean:
	rm -rf $(OBJDIR) app config.h

.PHONY: distclean
distclean: clean
	rm -f .config
