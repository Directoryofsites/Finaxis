import re

def natural_sort_key(s):
    """
    Genera una clave para ordenamiento natural (numérico y alfabético).
    Ej: 'B 4 / 101' vendrá antes que 'B 4 / 401'.
    """
    if not s:
        return []
    return [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', str(s))]
