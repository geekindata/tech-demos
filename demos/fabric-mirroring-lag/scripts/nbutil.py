"""Turn a list of cell sources into a Fabric Python (non-Spark) notebook .ipynb."""
import json
def write(path, cells, param_cell=0):
    out = []
    for i, src in enumerate(cells):
        c = {'cell_type': 'code', 'source': src.splitlines(True), 'outputs': [], 'execution_count': None, 'metadata': {}}
        if i == param_cell: c['metadata'] = {'tags': ['parameters']}
        out.append(c)
    nb = {'nbformat': 4, 'nbformat_minor': 5, 'cells': out,
          'metadata': {'kernel_info': {'name': 'jupyter', 'jupyter_kernel_name': 'python3.11'},
                       'kernelspec': {'name': 'jupyter', 'display_name': 'Jupyter'},
                       'language_info': {'name': 'python'},
                       'microsoft': {'language': 'python', 'language_group': 'jupyter_python'}}}
    json.dump(nb, open(path, 'w'), indent=1)
