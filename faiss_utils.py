from faiss import (
    METRIC_L2,
    METRIC_INNER_PRODUCT,
    index_factory as _cpu_index_factory,
    index_cpu_to_all_gpus,
    get_num_gpus,
)

def index_factory(d, key, metric):
    idx = _cpu_index_factory(d, key, metric)
    return index_cpu_to_all_gpus(idx)
