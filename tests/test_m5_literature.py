"""M5 literature retrieval: name handling, query, PubMed XML parsing, licence mapping (no network)."""
from __future__ import annotations

import json
import subprocess

import pytest

from lip.m5 import literature as L

XML = """<?xml version="1.0"?><PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article>
<Journal><Title>J Test</Title><JournalIssue><PubDate><Year>2021</Year></PubDate></JournalIssue></Journal>
<ArticleTitle>Leaf extracts of <i>Melissa officinalis</i></ArticleTitle>
<Abstract><AbstractText Label="METHODS">Leaves were dried.</AbstractText><AbstractText>Water extract.</AbstractText></Abstract>
<PublicationTypeList><PublicationType>Journal Article</PublicationType></PublicationTypeList></Article>
<MeshHeadingList><MeshHeading><DescriptorName>Melissa</DescriptorName></MeshHeading></MeshHeadingList></MedlineCitation>
<PubmedData><ArticleIdList><ArticleId IdType="pubmed">123</ArticleId><ArticleId IdType="doi">10.1/x</ArticleId>
<ArticleId IdType="pmc">PMC999</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>"""


@pytest.mark.parametrize("full,expected", [
    ("Mutelia officinalis (L.) Gren. ex Mutel", "Mutelia officinalis"), ("Mentha × piperita L.", "Mentha × piperita"),
    ("Artemisia absinthium var. insipida Stechm.", "Artemisia absinthium var. insipida"), ("Melissa L.", None),
])
def test_latin_name(full, expected):
    assert L.latin_name(full) == expected


def test_search_term_and_parse():
    assert L.search_term(["Melissa officinalis", "Thymus melissa"]) == '"Melissa officinalis"[tiab] OR "Thymus melissa"[tiab]'
    r = L.parse_pubmed(XML)[0]
    assert (r["pmid"], r["year"], r["doi"], r["pmcid"], r["journal"]) == ("123", 2021, "10.1/x", "PMC999", "J Test")
    assert r["title"] == "Leaf extracts of Melissa officinalis" and r["mesh"] == ["Melissa"]
    assert r["abstract"] == "METHODS: Leaves were dried. Water extract."


def test_licence_mapping(monkeypatch):
    fake = {"resultList": {"result": [{"pmcid": "PMC1", "isOpenAccess": "Y", "license": "cc by"},
                                      {"pmcid": "PMC2", "isOpenAccess": "N"}]}}
    monkeypatch.setattr(L, "get_json", lambda *a, **k: fake)
    out = L.oa_status_batch(["PMC1", "PMC2", "PMC3"])
    assert out["PMC1"] == {"status": "pmc_oa", "licence": "cc by"} and out["PMC2"]["status"] == "pmc_not_oa"
    assert out["PMC3"]["status"] == "pmc_unknown"


def test_committed_records_hold_no_abstract_text():
    import glob
    for f in glob.glob(str(L.OUT / "*.json")):
        d = json.load(open(f))
        assert all("abstract" not in r and "abstractSha256" in r for r in d["records"])
    assert subprocess.run(["git", "check-ignore", "-q", str(L.ABSTRACTS / "x.json")]).returncode == 0
