In the name of Allah

## Practical details
- OS: Ubuntu 22.04.5 LTS
- Deployment: Docker
- Solution services:
  - NoSQL Database: Elasticsearch 9.1.5
  - Visualization: Kibana 9.1.5
  - SQL Database: PostgreSQL 16.10-alpine3.22
  - Orchestration: Airflow 2.9.2
  - Orchestration: NiFi 1.27.0
- Report version: 0.1

## About the Problem
A data pipeline solution typically includes at least three logical architectural components, as described in the diagram below:
```mermaid
flowchart LR
    Source --> Processor
    Processor --> Destination
```
Nodes represent the implementation logically, but each node can contain many sophisticated details and components.

In this practice, we aim to create a simple lab that contains a single node and serves as a playground for manipulating and working with data.

# Solution
## 1. Writing Docker Compose
For Elasticsearch and Kibana, the official Elasticsearch blog has a post describing how to write a suitable Docker Compose. For business purposes and production environments, SSL certificates are used, but they are not required for playground lab.
For other services, I have described the details in the docker compose created by ChatGPT. The final result is below, and some decisions made are described as comments:

```yml
version: "3.8"

volumes:
  # In the first test, I used mounted paths like ./data/esdata, but it didn't work, and I couldn't find the reason with quick searches.
  esdata:
    driver: local
  kibanadata:
    driver: local

networks:
  default:
    name: elastic
    external: false

services:
  es:
    # Our company has a Nexus Docker image repository, which acts as a proxy for sanctions purposes. But it's possible to use images with other anti-sanctions solutions.
    image: elasticsearch:${STACK_VERSION}
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
    image: kibana:9.1.5
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
    image: apache/nifi:1.27.0
    environment:
      NIFI_WEB_HTTP_PORT: "8080"
    ports:
      - "8080:8080"

  airflow:
    container_name: airflow
    image: apache/airflow:2.9.2
    command: standalone
    environment:
      AIRFLOW__CORE__LOAD_EXAMPLES: "false"
    ports:
      - "8081:8080"
  
  postgres:
    image: postgres:16.10-alpine3.22
    container_name: db
    environment:
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - ./data/pg-data:/var/lib/postgresql/data
```

```bash
# Project namespace (defaults to the current folder name if not set)
COMPOSE_PROJECT_NAME=pipline-lab

# Password for the 'elastic' user (at least 6 characters)
ELASTIC_PASSWORD=123qwe1!@#QWE

# Password for the 'kibana_system' user (at least 6 characters)
KIBANA_PASSWORD=123qwe!@#QWE

# Version of Elastic products
STACK_VERSION=9.1.5

# Set to 'basic' or 'trial' to automatically start the 30-day trial
LICENSE=basic
# LICENSE=trial

# Port to expose Elasticsearch HTTP API to the host
ES_PORT=9200

# Port to expose Kibana to the host
KIBANA_PORT=5601

# Increase or decrease based on the available host memory (in bytes)
ES_MEM_LIMIT=4g
KB_MEM_LIMIT=1073741824
LS_MEM_LIMIT=1073741824

# SAMPLE Predefined Key only to be used in POC environments
# ENCRYPTION_KEY=c34d38b3a14956121ff2170e5030b471551370178f43e5626eec58b04a30fae2

```

## 2. State

The services logs are reviewed for exception detection, also for Kibana web view are loaded