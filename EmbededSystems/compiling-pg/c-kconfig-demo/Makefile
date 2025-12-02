# کامپایلر و فلگ‌ها
CC      := gcc
CFLAGS  := -Wall -Wextra -Iinclude
OBJDIR  := build

# سعی می‌کنیم .config رو include کنیم (اگه وجود داشته باشه)
-include .config

# منبع‌های پایه
SRCS := src/main.c

# بر اساس تنظیمات، سورس‌های بیشتر اضافه کن
ifeq ($(CONFIG_FEATURE_HELLO),y)
SRCS += src/feature_hello.c
endif

ifeq ($(CONFIG_FEATURE_MATH),y)
SRCS += src/feature_math.c
endif

# از لیست سورس‌ها، اسم object بساز
OBJS := $(SRCS:src/%.c=$(OBJDIR)/%.o)

# تارگت پیش‌فرض
.PHONY: all
all: app

# تارگت برنامهٔ نهایی
app: $(OBJDIR) config.h $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS)

# ساختن دایرکتوری build
$(OBJDIR):
	mkdir -p $(OBJDIR)

# ساختن config.h از .config
config.h: .config
	./scripts/genconfig.sh .config include/config.h
	@# یه لینک نسبی یا کپی برای راحتی این فایل rule
	@ln -sf ../include/config.h config.h 2>/dev/null || true

# کامپایل objectها
$(OBJDIR)/%.o: src/%.c include/config.h
	$(CC) $(CFLAGS) -c $< -o $@

# اجرای menuconfig با ابزار Kconfig (در صورت موجود بودن)
.PHONY: menuconfig
menuconfig:
	kconfig-mconf Kconfig

# تمیز کردن
.PHONY: clean
clean:
	rm -rf $(OBJDIR) app config.h

# پاک کردن تنظیمات
.PHONY: distclean
distclean: clean
	rm -f .config
