# سوال
من می‌خوام یه پروژه سی برام بزنی و توش از kconfig و make استفاده کنی هدفم اینه که بفهمم این make و kconfig چطوری کار می‌کنه، بنابراین برام این‌ها رو توضیح بده و پروژه c رو هم طوری انتخاب کن که این‌ها از توش دربیاد، حتی می‌تونی از یک پروژه open source استفاده کنی و براش kconfg بسازی، نوع پروژه رو طوری انتخاب کن که kconfig و make به درستی استفاده بشه خود c اش مهم نیست

قدم به قدم بگو چی کار کنم و همه چیز رو توضیح بده، برای ساختن دایرکتوری و فایل‌ها هم command بش بده

# پاسخ
بریم یه پروژه کوچیک بسازیم که مثل نسخه‌ٔ خیلی‌خیلی مینیاتوری کرنل لینوکسه:  
C ساده، ولی با **Kconfig** برای تنظیمات و **Makefile** برای build.

هدف:

- بفهمی **make** چطوری تصمیم می‌گیره چی رو کامپایل کنه.
    
- بفهمی **Kconfig** چطوری از یه سری گزینه، فایل `.config` می‌سازه و بعد اون وارد دنیای C و Make می‌شه.
    

فرض‌ها:

- روی لینوکس / WSL / macOS هستی و `gcc` و `make` داری.
    
- ترمینال در دسترسه.
    

اگه یه‌جاش ابزار نداشتی، باز هم ساختار رو می‌فهمی؛ نهایتش گزینه‌ها رو دستی تو `.config` می‌نویسی.

---

## ۱. ایدهٔ پروژه

اسم پروژه: `c-kconfig-demo`

ویژگی‌های قابل تنظیم:

- `CONFIG_FEATURE_HELLO`  
    اگر `y` بود، برنامه تابع hello رو کامپایل و اجرا می‌کنه.
    
- `CONFIG_FEATURE_MATH`  
    اگر `y` بود، یه تابع جمع ساده رو کامپایل و تست می‌کنه.
    
- `CONFIG_USER_NAME` (string)  
    اسم کاربری که برنامه بهش سلام می‌کنه.
    

جریان کار:

1. تو Kconfig می‌گی چه گزینه‌هایی داری.
    
2. با `menuconfig` (یا مشابهش) یه فایل `.config` تولید می‌کنی (مثلاً `CONFIG_FEATURE_HELLO=y`).
    
3. با یه اسکریپت ساده از `.config` یه `config.h` تولید می‌کنیم.
    
4. کدهای C، `config.h` رو include می‌کنن و با `#ifdef CONFIG_FEATURE_HELLO` و … رفتار رو عوض می‌کنن.
    
5. `Makefile` هم خود `.config` رو می‌خونه تا بدونه کدوم فایل‌های `.c` رو اصلاً کامپایل کنه.
    

---

## ۲. ساختار دایرکتوری

در ترمینال:

```bash
mkdir -p c-kconfig-demo/src c-kconfig-demo/include c-kconfig-demo/scripts c-kconfig-demo/build
cd c-kconfig-demo
```

توضیح:

- `src/` → کدهای C
    
- `include/` → headerها (مثل `config.h`)
    
- `scripts/` → اسکریپت‌هایی مثل تبدیل `.config` به `config.h`
    
- `build/` → خروجی‌ها (objectها و باینری نهایی)
    

---

## ۳. نوشتن کد C

### ۳.۱. `src/main.c`

```bash
cat > src/main.c << 'EOF'
#include <stdio.h>
#include "config.h"

#ifdef CONFIG_FEATURE_HELLO
void feature_hello(void);
#endif

#ifdef CONFIG_FEATURE_MATH
int feature_add(int a, int b);
#endif

int main(void)
{
    printf("Demo app started.\n");

#ifdef CONFIG_USER_NAME
    printf("Configured user name: %s\n", CONFIG_USER_NAME);
#endif

#ifdef CONFIG_FEATURE_HELLO
    feature_hello();
#else
    printf("FEATURE_HELLO is disabled.\n");
#endif

#ifdef CONFIG_FEATURE_MATH
    int result = feature_add(2, 3);
    printf("2 + 3 = %d (FEATURE_MATH enabled)\n", result);
#else
    printf("FEATURE_MATH is disabled.\n");
#endif

    return 0;
}
EOF
```

اینجا:

- `config.h` رو include می‌کنیم؛ این فایل **خودکار** ساخته می‌شه از `.config`.
    
- با `#ifdef CONFIG_FEATURE_*` بسته به تنظیمات، کد فعال/غیرفعال می‌شه.
    

---

### ۳.۲. `src/feature_hello.c`

```bash
cat > src/feature_hello.c << 'EOF'
#include <stdio.h>
#include "config.h"

void feature_hello(void)
{
#ifdef CONFIG_USER_NAME
    printf("Hello, %s! FEATURE_HELLO says hi.\n", CONFIG_USER_NAME);
#else
    printf("Hello! FEATURE_HELLO is enabled but USER_NAME is not set.\n");
#endif
}
EOF
```

---

### ۳.۳. `src/feature_math.c`

```bash
cat > src/feature_math.c << 'EOF'
#include "config.h"

int feature_add(int a, int b)
{
    return a + b;
}
EOF
```

---

## ۴. فایل Kconfig

فایل اصلی تنظیمات رو توی ریشهٔ پروژه می‌سازیم:

```bash
cat > Kconfig << 'EOF'
menu "Demo application configuration"

config FEATURE_HELLO
    bool "Enable 'hello' feature"
    default y
    help
      If enabled, the program will print a friendly hello message.

config FEATURE_MATH
    bool "Enable 'math' feature"
    default y
    help
      If enabled, the program will compile a simple addition function.

config USER_NAME
    string "User name to greet"
    default "World"
    help
      This string will be used by the hello feature to greet the user.

endmenu
EOF
```

یه نگاه مفهومی:

- `menu "..."` و `endmenu` فقط منو رو گروه‌بندی می‌کنن.
    
- `config FEATURE_HELLO`  
    یه گزینهٔ تنظیمی معرفی می‌کنه.
    
- `bool / string` نوع گزینه‌ست.
    
- `default` مقدار پیش‌فرضه.
    
- `help` توی UI تنظیمات (مثل `menuconfig`) متن راهنما رو نشون می‌ده.
    

---

## ۵. تبدیل `.config` به `config.h`

زمانی که Kconfig اجرا بشه، یه فایل مثل این می‌سازه:

```text
CONFIG_FEATURE_HELLO=y
CONFIG_FEATURE_MATH=y
CONFIG_USER_NAME="World"
```

ما می‌خوایم این رو تبدیل کنیم به:

```c
#define CONFIG_FEATURE_HELLO 1
#define CONFIG_FEATURE_MATH 1
#define CONFIG_USER_NAME "World"
```

### ۵.۱. اسکریپت `scripts/genconfig.sh`

```bash
cat > scripts/genconfig.sh << 'EOF'
#!/bin/sh
# Usage: genconfig.sh .config include/config.h

IN="$1"
OUT="$2"

if [ ! -f "$IN" ]; then
    echo "Input config file '$IN' not found!"
    exit 1
fi

mkdir -p "$(dirname "$OUT")"

# header
echo "/* Auto-generated from .config - DO NOT EDIT */" > "$OUT"

# تبدیل هر خط CONFIG_... به #define مناسب
grep '^CONFIG_' "$IN" | while IFS= read -r line; do
    NAME=$(printf "%s" "$line" | cut -d= -f1)
    VAL=$(printf "%s" "$line" | cut -d= -f2-)

    case "$VAL" in
        y)
            echo "#define $NAME 1" >> "$OUT"
            ;;
        n)
            # غیرفعال؛ چیزی تعریف نمی‌کنیم
            ;;
        \"*\")
            # رشته
            echo "#define $NAME $VAL" >> "$OUT"
            ;;
        *)
            # عدد یا چیز دیگر
            echo "#define $NAME $VAL" >> "$OUT"
            ;;
    esac
done
EOF

chmod +x scripts/genconfig.sh
```

---

## ۶. نصب ابزار Kconfig (اختیاری ولی قشنگ)

اینجا به یه ابزار لازم داریم که فایل `Kconfig` رو بخونه و `.config` بسازه. چند حالت:

- روی خیلی از سیستم‌ها، راحت‌ترین راه نصب `kconfig-frontends` یا استفاده از ابزارهای داخل سورس کرنل لینوکسه.
    
- به عنوان مسیر ساده، فرض می‌کنیم ابزاری به نام `kconfig-mconf` داری یا نصب می‌کنی.
    

برای مثال روی Debian/Ubuntu _ممکنه_ چیزی مثل این جواب بده (بسته‌ها ممکنه فرق کنند):

```bash
# فقط یک نمونه، ممکن است اسم بسته متفاوت باشد
sudo apt-get update
sudo apt-get install -y kconfig-frontends
```

بعدش معمولا دستورهایی مثل `kconfig-mconf` و `kconfig-conf` در دسترس‌اند.  
اگر نداشتی، باز هم می‌تونی `.config` رو **خودت دستی** درست کنی (در بخش ۸ توضیح می‌دم).

---

## ۷. نوشتن Makefile

فایل `Makefile` را در ریشهٔ پروژه بساز:

```bash
cat > Makefile << 'EOF'
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
EOF
```

### توضیح تک‌تک نکات مهم Makefile

بخش متغیرها:

```make
CC      := gcc
CFLAGS  := -Wall -Wextra -Iinclude
OBJDIR  := build
```

- `CC` → نام کامپایلر
    
- `CFLAGS` → فلگ‌ها
    
- `OBJDIR` → دایرکتوری objectها
    

خواندن `.config`:

```make
-include .config
```

- `include` یعنی محتویات فایل رو به صورت Make-variable وارد کن.
    
- مثلا اگر `.config` شامل `CONFIG_FEATURE_HELLO=y` باشه، در make می‌تونی `$(CONFIG_FEATURE_HELLO)` رو چک کنی.
    
- خط تیره `-` قبل از `include` یعنی اگر فایل نبود، غرغر نکن (خطا نشه).
    

اضافه کردن سورس‌ها براساس config:

```make
SRCS := src/main.c

ifeq ($(CONFIG_FEATURE_HELLO),y)
SRCS += src/feature_hello.c
endif
```

یعنی:

- اگر در `.config` نوشته بود `CONFIG_FEATURE_HELLO=y`، این فایل هم وارد build می‌شه.
    
- پس Kconfig غیرمستقیم تصمیم می‌گیره کدوم `.c` ها کامپایل بشن.
    

ساخت objectها:

```make
OBJS := $(SRCS:src/%.c=$(OBJDIR)/%.o)
```

این یه substitution قشنگه:

- هر `src/foo.c` را تبدیل می‌کند به `build/foo.o`.
    

قانون تولید `config.h`:

```make
config.h: .config
	./scripts/genconfig.sh .config include/config.h
	@ln -sf ../include/config.h config.h 2>/dev/null || true
```

- می‌گه برای ساخت `config.h`، باید `.config` وجود داشته باشه.
    
- اسکریپت ما فایل `include/config.h` رو می‌سازه؛ برای راحتی یه symlink هم درست می‌کنیم.
    

قانون objectها:

```make
$(OBJDIR)/%.o: src/%.c include/config.h
	$(CC) $(CFLAGS) -c $< -o $@
```

- هر object به فایل C و `include/config.h` وابسته است.
    
- اگر config تغییر کند، `config.h` عوض می‌شه و make دوباره build می‌کنه.
    

---

## ۸. اجرای پروژه قدم‌به‌قدم

### ۸.۱. تولید `.config` با Kconfig (راه شیک)

در ریشهٔ پروژه:

```bash
make menuconfig
```

اگر `kconfig-mconf` نصب باشد:

- یه منوی ncurses باز می‌شه با عنوان "Demo application configuration".
    
- می‌تونی `FEATURE_HELLO` و `FEATURE_MATH` رو enable/disable کنی.
    
- `USER_NAME` رو عوض کنی (مثلاً بذار `"Ali"`).
    

وقتی از منو خارج بشی و save کنی، فایل `.config` ساخته می‌شه.

نمونهٔ `.config` ممکن:

```text
CONFIG_FEATURE_HELLO=y
CONFIG_FEATURE_MATH=y
CONFIG_USER_NAME="Ali"
```

### ۸.۲. build کردن

```bash
make
```

چه اتفاق‌هایی می‌افته:

1. `make` هدف پیش‌فرض `all` رو اجرا می‌کنه → یعنی `app`.
    
2. `app` به `build/`، `config.h` و objectها وابسته است.
    
3. چون `.config` هست و `config.h` نیست:
    
    - rule مربوط به `config.h` اجرا می‌شه → `scripts/genconfig.sh`
        
    - `include/config.h` ساخته می‌شه.
        
4. بعد object‌ها کامپایل می‌شن:
    
    - بسته به این که `CONFIG_FEATURE_HELLO` و `CONFIG_FEATURE_MATH` چیه، `feature_hello.c` و `feature_math.c` ممکنه کامپایل بشن یا نه.
        
5. در نهایت `app` لینک می‌شه.
    

### ۸.۳. اجرای برنامه

```bash
./app
```

اگر همه‌چی enable باشه و `USER_NAME="Ali"`:

خروجی شبیه این خواهد بود:

```text
Demo app started.
Configured user name: Ali
Hello, Ali! FEATURE_HELLO says hi.
2 + 3 = 5 (FEATURE_MATH enabled)
```

حالا دوباره:

```bash
make menuconfig
```

- مثلا `FEATURE_MATH` رو `n` کن (غیرفعال).
    
- `save` → برگرد ترمینال.
    

بعد:

```bash
make
./app
```

می‌بینی که خط مربوط به `math` عوض شده و پیام "FEATURE_MATH is disabled." چاپ می‌شه و `feature_math.c` حتی کامپایل هم نشده.

---

## ۹. اگر ابزار Kconfig نداری

اگر نتونستی `kconfig-mconf` نصب کنی، باز هم می‌تونی مفاهیم رو بفهمی:

۱. یه `.config` رو **دستی** بساز:

```bash
cat > .config << 'EOF'
CONFIG_FEATURE_HELLO=y
CONFIG_FEATURE_MATH=n
CONFIG_USER_NAME="ManualUser"
EOF
```

۲. بعد:

```bash
make
./app
```

همون جریان رخ می‌ده، فقط به جای UI، config رو با دست نوشتی.

---

## ۱۰. جمع‌بندی مفهومی (چرا این کار جواب می‌ده؟)

- **Kconfig**:
    
    - تو فقط توضیح می‌دی چه تنظیماتی وجود داره (bool, int, string, dependency و …).
        
    - یه ابزار (مثل `kconfig-mconf`) این فایل رو می‌خونه و بهت یه `.config` plain-text می‌ده.
        
- **.config**:
    
    - فقط یه سری خط `KEY=VALUE` هست.
        
    - make می‌تونه اینها رو به عنوان متغیر بخونه (`include .config`).
        
    - اسکریپت ما می‌تونه همین‌ها رو به `#define` تبدیل کنه.
        
- **Makefile**:
    
    - `.config` را می‌خونه → تصمیم می‌گیره کدوم سورس‌ها در `SRCS` باشند.
        
    - `config.h` را از `.config` می‌سازه.
        
    - Dependency graph می‌سازه که اگر `.config` عوض شد → `config.h` عوض شود → objectها rebuild شوند → app دوباره لینک شود.
        
- **C code**:
    
    - `config.h` را include می‌کنه.
        
    - بر اساس `#ifdef CONFIG_...`، کد فعال یا غیرفعال می‌شه.
        

این همون الگویی‌ه که پروژه‌های بزرگ (مثل Linux kernel, BusyBox و …) استفاده می‌کنن، فقط با جزئیات خیلی بیشتر و گزینه‌های پیچیده‌تر.

---

از اینجا به بعد می‌تونی خودت بازی کنی:

- configهای جدید اضافه کنی (مثلاً `CONFIG_ENABLE_LOGGING`)،
    
- وابستگی بذاری (مثلاً `FEATURE_MATH` فقط اگر `FEATURE_HELLO` روشن بود)،
    
- یا چند باینری مختلف بسازی که هرکدوم با configهای خودشون build می‌شن.