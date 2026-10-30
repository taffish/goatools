"""Small independent fixtures for the upstream 1.6.8 parsing corrections."""
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from pathlib import Path
import tempfile

from goatools.anno.gpad_reader import GpadReader
from goatools.grouper.read_goids import read_sections
from goatools.parsers.ncbi_gene_file_reader import NCBIgeneFileReader
from goatools.ratio import _chk_gene2go


with tempfile.TemporaryDirectory(prefix="taf-goatools-168-") as tmp:
    root = Path(tmp)
    v1 = root / "old.gpa"
    v2 = root / "new.gpad"
    first = ["UniProtKB", "P1", "enables", "GO:0005515", "PMID:1", "ECO:0000353",
             "UniProtKB:Q1", "taxon:9606", "20260425", "IntAct", "", ""]
    second = ["UniProtKB", "P2", "NOT|involved_in", "GO:0006915", "PMID:2",
              "ECO:0000250", "", "", "20260101", "UniProt", "", ""]
    v1.write_text("!gpa-version: 1.1\n" + "\n".join("\t".join(x) for x in (first, second)) + "\n")
    modern = [["UniProtKB:P1", "", "RO:0002327", *first[3:7], "NCBITaxon:9606",
               "2026-04-25", *first[9:]],
              ["UniProtKB:P2", "NOT", "RO:0002331", *second[3:7], "",
               "2026-01-01", *second[9:]]]
    v2.write_text("!gpad-version: 2.0\n!generated-by: synthetic\n" +
                  "\n".join("\t".join(x) for x in modern) + "\n")
    a, b = GpadReader(str(v1)), GpadReader(str(v2))
    assert len(a.associations) == len(b.associations) == 2
    assert a.associations == b.associations
    assert b.associations[0].DB_ID == "P1" and b.associations[0].Date == date(2026, 4, 25)
    assert b.associations[1].Qualifier == {"NOT", "involved_in"}
    assert b.get_id2gos(prt=None) == {"P1": {"GO:0005515"}}
    modern[0][7] = "NCBITaxon:9606|NCBITaxon:10090"
    modern[0][11] = "contributor-id=A|model-state=production|contributor-id=B"
    v2.write_text("!gpad-version: 2.0\n" + "\t".join(modern[0]) + "\n")
    row, = GpadReader(str(v2)).associations
    assert row.Taxon == [9606, 10090]
    assert row.Properties == {"contributor-id": ["A", "B"], "model-state": ["production"]}
    v2.write_text(v2.read_text().replace("RO:0002327", "RO:9999999"))
    output = StringIO()
    try:
        with redirect_stdout(output):
            GpadReader(str(v2))
    except SystemExit as exc:
        assert exc.code != 0 and "UNRECOGNIZED RELATION" in output.getvalue()
    else:
        raise AssertionError("invalid relation accepted")
    ncbi = root / "genes.tsv"
    ncbi.write_text("GeneID\tSymbol\tchromosome\n1017\tCDK2\t9\n7157\tTP53\t17\n")
    data, _ = NCBIgeneFileReader(str(ncbi), log=None).run("lists", None)
    assert data == [[1017, "CDK2", " 9"], [7157, "TP53", "17"]]
    try:
        _chk_gene2go({"GO:0008150": {"CDK2"}})
    except Exception as exc:
        assert not isinstance(exc, TypeError) and "EXPECTED TO BE gene2go" in str(exc)
    else:
        raise AssertionError("go2gene accepted")
    assert read_sections("goatools.test_data.sections.gjoneska_pfenning")
print("UPSTREAM_168_PARSING_PASS")
