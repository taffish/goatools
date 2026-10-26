#!/usr/bin/env python3
"""Offline synthetic regression for upstream v1.6.7 MICA and tie-breaking."""
import math
from pathlib import Path
import tempfile

from goatools.obo_parser import GODag
from goatools.semantic import (
    TermCounts, deepest_common_ancestor, get_info_content, get_freq_msca,
    lin_sim, most_informative_common_ancestor, resnik_sim, schlicker_sim,
)

# Different branches deliberately disagree on maximum depth and maximum IC.
parents = {2: [8150], 3: [2], 4: [8150], 5: [8150],
           6: [3, 4], 7: [3, 4], 8: [4, 5], 9: [4, 5]}
def go(i):
    return f"GO:{i:07d}"

obo = "format-version: 1.2\n\n"
for i in [8150, *parents]:
    obo += (f"[Term]\nid: {go(i)}\nname: synthetic {i}\n"
            "namespace: biological_process\n")
    obo += "".join(f"is_a: {go(p)}\n" for p in parents.get(i, [])) + "\n"
annotations = {f"g{i}": {go(3)} for i in range(1, 6)}
annotations.update({f"g{i}": {go(i)} for i in range(6, 10)})
annotations.update({f"g{i}": {go(5)} for i in range(10, 13)})
with tempfile.TemporaryDirectory(prefix="taf-goatools-mica-") as tmp:
    path = Path(tmp) / "synthetic.obo"
    path.write_text(obo)
    dag = GODag(str(path), prt=None)
    counts = TermCounts(dag, annotations)
    assert math.isclose(get_info_content(go(4), counts), math.log(3))
    assert deepest_common_ancestor([go(6), go(7)], dag) == go(3)
    assert most_informative_common_ancestor([go(6), go(7)], dag, counts) == go(4)
    for a, b in [(6, 7), (7, 6), (8, 9), (9, 8)]:
        assert math.isclose(resnik_sim(go(a), go(b), dag, counts), math.log(3))
        assert math.isclose(lin_sim(go(a), go(b), dag, counts), math.log(3)/math.log(12))
        assert math.isclose(get_freq_msca(go(a), go(b), dag, counts), 1/3)
        assert math.isclose(schlicker_sim(go(a), go(b), dag, counts),
                            math.log(3)/math.log(12) * (1-1/3))
    assert deepest_common_ancestor([go(8), go(9)], dag) == go(5)
    assert deepest_common_ancestor([go(9), go(8)], dag) == go(5)
    assert most_informative_common_ancestor([go(6), go(6)], dag, counts) == go(6)
print("SEMANTIC_MICA_PASS")
