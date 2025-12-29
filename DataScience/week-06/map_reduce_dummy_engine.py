from multiprocessing import Pool, cpu_count
from collections import defaultdict


def _run_mapper_chunk(map_function, chunk):
    out = []
    for record in chunk:
        mapped = map_function(record)

        if not mapped:
            continue

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


def tag_with_source(records, src_name):
    return [dict(r, __src=src_name) for r in records]


# ---------------------------------- Select -----------------------------------


def map_select(record):
    if record["age"] > 30:
        return [("keep", record)]
    return []


def reduce_select_age_gt_30(key, values):
    for r in values:
        yield r


# ---------------------------------- Project ----------------------------------


def map_project_name_city(record):
    key = (record["name"], record["city"])
    return [(key, None)]


def reduce_project_name_city(key, values):
    name, city = key
    yield {"name": name, "city": city}


# ---------------------------------- Rename -----------------------------------


def map_rename_name_to_fullname(record):
    new_rec = dict(record)
    if "name" in new_rec:
        new_rec["full_name"] = new_rec.pop("name")
    return [("all", new_rec)]


def reduce_rename_passthrough(key, values):
    for r in values:
        yield r


# ----------------------------------- Unioin ----------------------------------


def map_union(record):
    key = tuple(sorted(record.items()))
    return [(key, record)]


def reduce_union(key, values):
    yield values[0]


# -------------------------------- Intersection -------------------------------


def map_intersection(record):
    src = record["__src"]
    pure_items = tuple(sorted((k, v) for k, v in record.items() if k != "__src"))
    key = pure_items
    return [(key, src)]


def reduce_intersection(key, values):
    srcs = set(values)
    if "R" in srcs and "S" in srcs:
        rec = dict(key)
        yield rec


# --------------------------------- Diffrence ---------------------------------


def map_difference(record):
    src = record["__src"]
    pure_items = tuple(sorted((k, v) for k, v in record.items() if k != "__src"))
    key = pure_items
    return [(key, src)]


def reduce_difference(key, values):
    srcs = set(values)
    if "R" in srcs and "S" not in srcs:
        rec = dict(key)
        yield rec


# ------------------------------ Cartesian Product ----------------------------


def map_cartesian(record):
    return [("all", record)]


def reduce_cartesian(key, values):
    R_records = []
    S_records = []

    for r in values:
        src = r["__src"]
        pure = {k: v for k, v in r.items() if k != "__src"}
        if src == "R":
            R_records.append(pure)
        else:
            S_records.append(pure)

    for r in R_records:
        for s in S_records:
            merged = dict(r)
            for k, v in s.items():
                if k in merged:
                    merged[f"S_{k}"] = v
                else:
                    merged[k] = v
            yield merged


# ----------------------------------- Join ------------------------------------


def map_join_on_id(record):
    return [(record["id"], (record, record["owner"]))]


def reduce_join_on_id(key, values):
    # if avali dasht va domovi ham dasht
    yield [()]


# ----------------------------------- Join ------------------------------------


def map_division(record):
    return [("div", record)]


def reduce_division(key, values):
    enroll_pairs = []  # (SID, CID)
    must_cids = set()

    for r in values:
        src = r["__src"]
        if src == "R":
            enroll_pairs.append((r["SID"], r["CID"]))
        else:  # S
            must_cids.add(r["CID"])

    sid_to_cids = defaultdict(set)
    for sid, cid in enroll_pairs:
        sid_to_cids[sid].add(cid)

    for sid, cids in sid_to_cids.items():
        if must_cids.issubset(cids):
            yield {"SID": sid}


if __name__ == "__main__":
    records = [
        {"id": 1, "name": "Ali", "city": "Tehran", "age": 25},
        {"id": 2, "name": "Sara", "city": "Tehran", "age": 31},
        {"id": 3, "name": "Reza", "city": "Shiraz", "age": 29},
        {"id": 4, "name": "Neda", "city": "Mashhad", "age": 22},
        {"id": 5, "name": "Amir", "city": "Tehran", "age": 27},
        {"id": 6, "name": "Maryam", "city": "Isfahan", "age": 35},
        {"id": 7, "name": "Hossein", "city": "Tabriz", "age": 40},
    ]

    select_engine = MapReduceDummyEngine(map_select, reduce_select_age_gt_30)
    print("\n=== SELECTION age>30 ===")
    print(select_engine.run(records, parallel=True))

    project_engine = MapReduceDummyEngine(
        map_project_name_city, reduce_project_name_city
    )
    print("\n=== PROJECTION name,city ===")
    print(project_engine.run(records, parallel=True))

    rename_engine = MapReduceDummyEngine(
        map_rename_name_to_fullname, reduce_rename_passthrough
    )
    print("\n=== RENAME full_name <- name ===")
    print(rename_engine.run(records, parallel=True))

    R = records[:5]
    S = records[3:]
    union_engine = MapReduceDummyEngine(map_union, reduce_union)
    print("\n=== UNION R and S ===")
    print(union_engine.run(R + S, parallel=True))

    # ===== INTERSECTION: R ∩ S
    R_tag = tag_with_source(R, "R")
    S_tag = tag_with_source(S, "S")
    inter_engine = MapReduceDummyEngine(map_intersection, reduce_intersection)
    print("\n=== INTERSECTION R and S ===")
    print(inter_engine.run(R_tag + S_tag, parallel=True))

    # ===== DIFFERENCE: R − S
    diff_engine = MapReduceDummyEngine(map_difference, reduce_difference)
    print("\n=== DIFFERENCE R − S ===")
    print(diff_engine.run(R_tag + S_tag, parallel=True))

    R_small = records[:3]
    S_small = records[3:5]
    cart_engine = MapReduceDummyEngine(map_cartesian, reduce_cartesian)
    print("\n=== CARTESIAN PRODUCT R × S ===")
    print(
        cart_engine.run(
            tag_with_source(R_small, "R") + tag_with_source(S_small, "S"),
            parallel=False,
        )
    )

    users = [
        {"id": 1, "name": "Ali", "city": "Tehran", "age": 25},
        {"id": 2, "name": "Sara", "city": "Tehran", "age": 31},
        {"id": 3, "name": "Reza", "city": "Shiraz", "age": 29},
    ]
    salaries = [
        {"id": 1, "salary": 1000},
        {"id": 2, "salary": 2000},
        {"id": 4, "salary": 3000},
    ]
    join_engine = MapReduceDummyEngine(map_join_on_id, reduce_join_on_id)
    print("\n=== JOIN users ⋈ salaries ON id ===")
    print(
        join_engine.run(
            tag_with_source(users, "R") + tag_with_source(salaries, "S"),
            parallel=False,
        )
    )

    # ===== DIVISION: Enroll ÷ MustTake
    enroll = [
        {"SID": 1, "CID": 10},
        {"SID": 1, "CID": 20},
        {"SID": 2, "CID": 10},
        {"SID": 3, "CID": 10},
        {"SID": 3, "CID": 20},
    ]
    must_take = [
        {"CID": 10},
        {"CID": 20},
    ]
    div_engine = MapReduceDummyEngine(map_division, reduce_division)
    print("\n=== DIVISION Enroll MustTake ===")
    print(
        div_engine.run(
            tag_with_source(enroll, "R") + tag_with_source(must_take, "S"),
            parallel=False,
        )
    )
