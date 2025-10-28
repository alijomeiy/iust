بسم الله الرحمن الرحیم
## جزئیات عملیاتی
- سیستم عامل: اوبونتو 22.04.5 LTS
   - استقرار: docker
- سرویس‌های موجود در راه‌حل:
    - پایگاه داده NoSQL: Elasticsearch 9.1.5
    - ابزار تجسم داده‌ها: Kibana 9.1.5
    - پایگاه داده SQL: PostgreSQL 16.10-alpine3.22
    - زمان‌بندی و مدیریت: Airflow 2.9.2
    - زمان‌بندی و مدیریت: NiFi 1.27.0
- نسخه گزارش: 0.1
- تاریخ نگارش: جمعه ۲ آبان‌ماه ۱۴۰۴
## درباره مشکل
در این هفته در ادامه  [[۰۰-گزارش-استقرار-آزمایشگاه-خط-داده]] مطابق فصل سوم کتاب Data Engineering with Python می‌خواهیم خط لوله‌ای را مستقر کنیم شامل موارد زیر است.

سند داکر کامپوز در [ریپازیتوری شخصی گیت‌هاب](https://github.com/alijomeiy/iust/blob/main/DataScience/week-02/docker-compose.yml) بارگذاری شده است، اما در ادامه نیز آمده است.

```yml
x-airflow-common
  &airflow-common
  image: ${AIRFLOW_IMAGE_NAME:-docker.resaa.net/apache/airflow:3.1.1}
  # build: .
  env_file:
    - ${ENV_FILE_PATH:-.env}
  environment: &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__CORE__AUTH_MANAGER: airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'false'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__CORE__EXECUTION_API_SERVER_URL: 'http://airflow-apiserver:8080/execution/'
    AIRFLOW__WEBSERVER__EXPOSE_CONFIG: 'true'
    # yamllint disable rule:line-length
    # Use simple http server on scheduler for health checks
    # See https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/check-health.html#scheduler-health-check-server
    # yamllint enable rule:line-length
    AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK: 'true'
    # WARNING: Use _PIP_ADDITIONAL_REQUIREMENTS option ONLY for a quick checks
    # for other purpose (development, test and especially production usage) build/extend Airflow image.
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:-}
    # The following line can be used to set a custom config file, stored in the local config folder
    AIRFLOW_CONFIG: '/opt/airflow/config/airflow.cfg'
  volumes:
    - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
    # - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
    - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
    - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on: &airflow-common-depends-on
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy

services:
  postgres:
    image: docker.resaa.net/postgres:16
    container_name: postgres
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: [ "CMD", "pg_isready", "-U", "airflow" ]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: always

  redis:
    # Redis is limited to 7.2-bookworm due to licencing change
    # https://redis.io/blog/redis-adopts-dual-source-available-licensing/
    image: docker.resaa.net/redis:7.2-bookworm
    container_name: redis
    expose:
      - 6379
    healthcheck:
      test: [ "CMD", "redis-cli", "ping" ]
      interval: 10s
      timeout: 30s
      retries: 50
      start_period: 30s
    restart: always

  airflow-apiserver:
    <<: *airflow-common
    command: api-server
    container_name: airflow_ali_server
    ports:
      - "8081:8080"
    healthcheck:
      test: [ "CMD", "curl", "--fail", "http://localhost:8080/api/v2/version" ]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    container_name: airflow_scheduler
    healthcheck:
      test: [ "CMD", "curl", "--fail", "http://localhost:8974/health" ]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-dag-processor:
    <<: *airflow-common
    command: dag-processor
    container_name: airflow_dagp_processor
    healthcheck:
      test: [ "CMD-SHELL", 'airflow jobs check --job-type DagProcessorJob --hostname "$${HOSTNAME}"' ]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-worker:
    <<: *airflow-common
    command: celery worker
    container_name: airflow_common
    healthcheck:
      # yamllint disable rule:line-length
      test:
        - "CMD-SHELL"
        - 'celery --app airflow.providers.celery.executors.celery_executor.app inspect ping -d "celery@$${HOSTNAME}" || celery --app airflow.executors.celery_executor.app inspect ping -d "celery@$${HOSTNAME}"'
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    environment:
      <<: *airflow-common-env
      # Required to handle warm shutdown of the celery workers properly
      # See https://airflow.apache.org/docs/docker-stack/entrypoint.html#signal-propagation
      DUMB_INIT_SETSID: "0"
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-apiserver:
        condition: service_healthy
      airflow-init:
        condition: service_completed_successfully

  airflow-triggerer:
    <<: *airflow-common
    command: triggerer
    container_name: airflow-triggerer
    healthcheck:
      test: [ "CMD-SHELL", 'airflow jobs check --job-type TriggererJob --hostname "$${HOSTNAME}"' ]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    container_name: airflow_init
    # yamllint disable rule:line-length
    command:
      - -c
      - |
        if [[ -z "${AIRFLOW_UID}" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: AIRFLOW_UID not set!\e[0m"
          echo "If you are on Linux, you SHOULD follow the instructions below to set "
          echo "AIRFLOW_UID environment variable, otherwise files will be owned by root."
          echo "For other operating systems you can get rid of the warning with manually created .env file:"
          echo "    See: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#setting-the-right-airflow-user"
          echo
          export AIRFLOW_UID=$$(id -u)
        fi
        one_meg=1048576
        mem_available=$$(($$(getconf _PHYS_PAGES) * $$(getconf PAGE_SIZE) / one_meg))
        cpus_available=$$(grep -cE 'cpu[0-9]+' /proc/stat)
        disk_available=$$(df / | tail -1 | awk '{print $$4}')
        warning_resources="false"
        if (( mem_available < 4000 )) ; then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough memory available for Docker.\e[0m"
          echo "At least 4GB of memory required. You have $$(numfmt --to iec $$((mem_available * one_meg)))"
          echo
          warning_resources="true"
        fi
        if (( cpus_available < 2 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough CPUS available for Docker.\e[0m"
          echo "At least 2 CPUs recommended. You have $${cpus_available}"
          echo
          warning_resources="true"
        fi
        if (( disk_available < one_meg * 10 )); then
          echo
          echo -e "\033[1;33mWARNING!!!: Not enough Disk space available for Docker.\e[0m"
          echo "At least 10 GBs recommended. You have $$(numfmt --to iec $$((disk_available * 1024 )))"
          echo
          warning_resources="true"
        fi
        if [[ $${warning_resources} == "true" ]]; then
          echo
          echo -e "\033[1;33mWARNING!!!: You have not enough resources to run Airflow (see above)!\e[0m"
          echo "Please follow the instructions to increase amount of resources available:"
          echo "   https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#before-you-begin"
          echo
        fi
        echo
        echo "Creating missing opt dirs if missing:"
        echo
        mkdir -v -p /opt/airflow/{logs,dags,plugins,config}
        echo
        echo "Airflow version:"
        /entrypoint airflow version
        echo
        echo "Files in shared volumes:"
        echo
        ls -la /opt/airflow/{logs,dags,plugins,config}
        echo
        echo "Running airflow config list to create default config file if missing."
        echo
        /entrypoint airflow config list >/dev/null
        echo
        echo "Files in shared volumes:"
        echo
        ls -la /opt/airflow/{logs,dags,plugins,config}
        echo
        echo "Change ownership of files in /opt/airflow to ${AIRFLOW_UID}:0"
        echo
        chown -R "${AIRFLOW_UID}:0" /opt/airflow/
        echo
        echo "Change ownership of files in shared volumes to ${AIRFLOW_UID}:0"
        echo
        chown -v -R "${AIRFLOW_UID}:0" /opt/airflow/{logs,dags,plugins,config}
        echo
        echo "Files in shared volumes:"
        echo
        ls -la /opt/airflow/{logs,dags,plugins,config}

    # yamllint enable rule:line-length
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_MIGRATE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow}
      _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}
      _PIP_ADDITIONAL_REQUIREMENTS: ''
    user: "0:0"

  airflow-cli:
    <<: *airflow-common
    profiles:
      - debug
    container_name: airflow_cli
    environment:
      <<: *airflow-common-env
      CONNECTION_CHECK_MAX_COUNT: "0"
    # Workaround for entrypoint issue. See: https://github.com/apache/airflow/issues/16252
    command:
      - bash
      - -c
      - airflow
    depends_on:
      <<: *airflow-common-depends-on

  # You can enable flower by adding "--profile flower" option e.g. docker-compose --profile flower up
  # or by explicitly targeted on the command line e.g. docker-compose up flower.
  # See: https://docs.docker.com/compose/profiles/
  flower:
    <<: *airflow-common
    command: celery flower
    container_name: airflow_flower
    profiles:
      - flower
    ports:
      - "5555:5555"
    healthcheck:
      test: [ "CMD", "curl", "--fail", "http://localhost:5555/" ]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully
  es:
    image: docker.resaa.net/elasticsearch:${STACK_VERSION}
    container_name: es
    labels:
      co.elastic.logs/module: elasticsearch
    volumes:
      - esdata:/usr/share/elasticsearch/data
    ports:
      - ${ES_PORT}:9200
    environment:
      - node.name=es
      - discovery.type=single-node
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
      - bootstrap.memory_lock=true
      - xpack.security.enabled=false
      - xpack.security.http.ssl.enabled=false
      - xpack.security.transport.ssl.enabled=false
    mem_limit: ${ES_MEM_LIMIT}
    ulimits:
      memlock:
        soft: -1
        hard: -1

  kibana:
    image: docker.resaa.net/kibana:9.1.5
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://192.168.21.81:9200
    ports:
      - "5601:5601"
    volumes:
      - kibanadata:/usr/share/kibana/data
    depends_on:
      - es

  nifi:
    container_name: nifi
    image: docker.resaa.net/apache/nifi:1.27.0
    environment:
      NIFI_WEB_HTTP_PORT: "8080"
    ports:
      - "8080:8080"
volumes:
  postgres-db-volume:
  esdata:
    driver: local
  kibanadata:
    driver: local

networks:
  default:
    name: elastic
    external: false
```


## راه‌حل

برای استقرار از سند [استقرار داکری تارنمای رسمی airflow](curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.1.1/docker-compose.yaml') استفاده شد. در این سند استقرار این کانتینر با نسخه `3.1.1` بود و من هم از همین نسخه استفاده کردم که قدری در دستورات پایتون با کتاب متفاوت بود.
## یادداشت‌ها
- برای ساخت کاربر جدید در airflow می‌توان دستور زیر را اجرا کرد، بدیهی است که در استقرار غیر داکری بخش ابتدایی یعنی `docker exec airflow` باید پاک شود.
```bash
docker exec airflow airflow users create --role Admin --username <admin username> --email <admin emain> --firstname <admin first name> --lastname <admin last name> --password <admin password>
```
- همین‌طور به صورت پیش‌فرض با اجرای دستور زیر مقدار پیش‌فرض رمز کاربر ادمین چاپ خواهد شد
```bash
docker exec airflow cat /opt/airflow/standalone_admin_password.txt
```
- در ابتدا فکر می‌کردم استقرار داکری میکروسرویسی که در خود airflow هم در یک پیوند آن را آماده کرده پیچیدگی‌های زیادی دارد و برای خوشه‌های کوبر مناسب است اما اشتباه می‌کردم و همان مناسب بود
- توضیح‌های کتاب با نسخه‌های جدیدتر airflow تضاد دارد
- به صورت پیش‌فرض airflow متغیر محیط `AIRFLOW__WEBSERVER__EXPOSE_CONFIG` را دارد، اگر بخواهیم تنظیمات در پنل وب نمایش داده شود لازم است این مقدار با `true` بازنویسی شود.