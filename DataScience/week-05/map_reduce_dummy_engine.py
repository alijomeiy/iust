from multiprocessing import Pool, cpu_count
from collections import defaultdict


def _run_mapper_chunk(map_function, chunk):
    """Run map_fn over a chunk of records and return list of (key, value)."""
    out = []
    for record in chunk:
        mapped = map_function(record)

        # اگر mapper هیچ چیزی برنگردونه (None) یا خالی باشه → یعنی zero output
        if not mapped:
            continue

        # اینجا فرض می‌کنیم mapped یک iterable از (key, value) هاست
        for kv in mapped:
            out.append(kv)

    return out


class MapReduceDummyEngine:
    def __init__(self, map_function, reduce_function):
        self.mapper = map_function
        self.reducer = reduce_function

    def run(self, records, parallel=True):
        if not records:
            return []

        if parallel:
            worker_counts = min(cpu_count(), len(records))
        else:
            worker_counts = 1

        chunk_size = (len(records) + worker_counts - 1) // worker_counts
        chunks = [
            records[i * chunk_size : (i + 1) * chunk_size]
            for i in range(worker_counts)
            if records[i * chunk_size : (i + 1) * chunk_size]
        ]

        # MAP PHASE
        if parallel and worker_counts > 1:
            with Pool(worker_counts) as pool:
                mapped_lists = pool.starmap(
                    _run_mapper_chunk,
                    [(self.mapper, c) for c in chunks],
                )
        else:
            mapped_lists = [_run_mapper_chunk(self.mapper, c) for c in chunks]

        # SHUFFLE PHASE
        intermediates = defaultdict(list)
        for mapped in mapped_lists:
            for key, value in mapped:
                intermediates[key].append(value)

        # REDUCE PHASE
        results = []
        for key in sorted(intermediates.keys()):
            values = intermediates[key]
            for out_record in self.reducer(key, values):
                results.append(out_record)

        return results


def map_count_by_city(record):
    city = record["city"]
    # هر رکورد در این شهر → یک واحد به حسابش
    return [(city, 1)]


def reduce_count_by_city(key, values):
    # print(f"K: {key} ---> Vs:{values}")
    total = sum(values)
    # key همون city هست
    yield (key, total)


def map_select_upperthan_30(record):
    age = record["age"]
    if age > 30:
        return [(record["id"], record)]


def reduce_select_upper_than_30(key, values):
    yield (key, values)


def map_project_name_city(record):
    return [(record["name"], record["city"])]


def reduce_project_name_city(key, values):
    yield (key, values)


# def map_uni

if __name__ == "__main__":
    records = [
        {"id": 1, "name": "Ali", "city": "Tehran", "age": 25},
        {"id": 2, "name": "Sara", "city": "Tehran", "age": 31},
        {"id": 3, "name": "Reza", "city": "Shiraz", "age": 29},
        {"id": 4, "name": "Neda", "city": "Mashhad", "age": 22},
        {"id": 5, "name": "Amir", "city": "Tehran", "age": 27},
        {"id": 6, "name": "Maryam", "city": "Isfahan", "age": 35},
        {"id": 7, "name": "Hossein", "city": "Tabriz", "age": 40},
        {"id": 8, "name": "Fatemeh", "city": "Mashhad", "age": 19},
        {"id": 9, "name": "Mohsen", "city": "Shiraz", "age": 33},
        {"id": 10, "name": "Sina", "city": "Tehran", "age": 21},
        {"id": 11, "name": "Pari", "city": "Isfahan", "age": 28},
        {"id": 12, "name": "Ladan", "city": "Tehran", "age": 24},
        {"id": 13, "name": "Kian", "city": "Tabriz", "age": 30},
        {"id": 14, "name": "Hani", "city": "Shiraz", "age": 26},
        {"id": 15, "name": "Sahar", "city": "Tehran", "age": 32},
        {"id": 16, "name": "Pouya", "city": "Mashhad", "age": 23},
        {"id": 17, "name": "Arash", "city": "Tehran", "age": 38},
        {"id": 18, "name": "Yasmin", "city": "Isfahan", "age": 20},
        {"id": 19, "name": "Behnam", "city": "Tehran", "age": 45},
        {"id": 20, "name": "Roya", "city": "Shiraz", "age": 34},
    ]

    counter_engine = MapReduceDummyEngine(map_count_by_city, reduce_count_by_city)
    project_engine = MapReduceDummyEngine(
        map_project_name_city, reduce_project_name_city
    )
    select_engine = MapReduceDummyEngine(
        map_select_upperthan_30, reduce_select_upper_than_30
    )

    result = counter_engine.run(records, parallel=True)
    print(f"\n\nCOUNT: {result}")
    result = project_engine.run(records, parallel=True)
    print(f"\n\nPROJECT: {result}")
    result = select_engine.run(records, parallel=True)
    print(f"\n\nSELECT: {result}")
