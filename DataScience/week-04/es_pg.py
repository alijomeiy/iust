from elasticsearch import Elasticsearch
from elasticsearch import helpers
from pandas.io.json import json_normalize
from faker import Faker


class EsConnectionPg:
    def __init__(self, host: str):
        self._es = Elasticsearch(hosts=[host])
        self._faker = Faker()

    def insert_index(self, doc: dict):
        return self._es.index(index="users", document=doc)

    def test_helper_insert(self):
        actions = [
            {
                "_index": "users",
                "_source": {
                    "name": self._faker.name(),
                    "street": self._faker.street_address(),
                    "city": self._faker.city(),
                    "zip": self._faker.zipcode(),
                },
            }
            for _ in range(998)
        ]
        return helpers.bulk(self._es, actions)

    def query_es(self):
        doc = {"query": {"match_all": {}}}
        return self._es.search(index="users",body=doc,size=10)


if __name__ == "__main__":
    espg = EsConnectionPg("http://192.168.21.81:9200")

    result = espg.query_es()
    print(dir(result))
    print(result.body)
