"""Hand-curated toxicity entries for the study-set species (replaces the Wikipedia-derived column).

basis = "ai_drafted_unverified": each entry was drafted by an AI (Claude Code) from ONE reputable source
opened in the pipeline run, and quotes ONE sentence of it. The quote is re-checked against the
fetched source text on every run (whitespace-normalised; PDF text extracted with pypdf). `verified_by`
stays empty until a person checks the entry. Five summaries were revised after the review pass in
data/reference/review_v1/toxicity_review.csv (basis ai_assisted_check), each within its source.

Sources: European Medicines Agency herbal documents (EU herbal monographs, assessment reports,
public statements; "Reproduction is authorised provided the source is acknowledged") and
peer-reviewed open-access PMC articles with a Creative Commons licence stated on the article page.

Categories (what the SOURCE says; none of them is a safety rating):
  toxic_reported        poisoning, toxic effects or toxic constituents reported
  concern_reported      a specific risk, contraindication, warning or restriction, without poisoning
  no_toxicity_reported  the source reports no toxicity in its study or assessment; NOT evidence of safety
  data_lacking          the source states that safety / toxicity data are lacking
  unknown               no reputable source was located in this session; NOT evidence of safety
The toxicity flag is for a lab's risk assessment. Toxic plants stay in the study set.
"""
from __future__ import annotations

import html
import re

import pandas as pd

from ..http import get_pdf_text, get_text
from ..paths import ROOT

OUT = ROOT / "data" / "reference" / "toxicity_curated.csv"
BASIS = "ai_drafted_unverified"
CATEGORIES = ("toxic_reported", "concern_reported", "no_toxicity_reported", "data_lacking", "unknown")
EMA = "https://www.ema.europa.eu"
PMC = "https://pmc.ncbi.nlm.nih.gov/articles/{}/"
EMA_LICENCE = "Reproduction is authorised provided the source is acknowledged"

# (species, category, summary in our words, kind, locator, source name, verbatim quote)
#   kind "ema": locator = EMA document path (PDF); kind "pmc": locator = PMCID; kind None: unknown
EMA_DOC = {
    "wormwood": "/en/documents/herbal-summary/wormwood-herb-summary-public_en.pdf",
    "agrimony": "/en/documents/herbal-summary/agrimony-summary-public_en.pdf",
    "comfrey": "/en/documents/herbal-summary/comfrey-root-summary-public_en.pdf",
    "lavender": "/en/documents/herbal-monograph/final-community-herbal-monograph-lavandula-angustifolia-p-mill-flos_en.pdf",
    "liquorice": "/en/documents/herbal-monograph/final-european-union-herbal-monograph-glycyrrhiza-glabra-l-glycyrrhiza-inflata-bat-glycyrrhiza-uralensis-fisch-radix-revision-1_en.pdf",
    "melissa": "/en/documents/herbal-summary/melissa-leaf-summary-public_en.pdf",
    "centaury": "/en/documents/herbal-summary/centaury-summary-public_en.pdf",
    "celandine": "/en/documents/public-statement/final-public-statement-chelidonium-majus-l-herba_en.pdf",
    "hop": "/en/documents/herbal-summary/hop-strobile-summary-public_en.pdf",
    "caraway": "/en/documents/herbal-summary/caraway-fruit-summary-public_en.pdf",
    "meadowsweet": "/en/documents/herbal-monograph/final-community-herbal-monograph-filipendula-ulmaria-l-maxim-herba-first-version_en.pdf",
}
EMA_SUMMARY = "EMA/HMPC, EU herbal medicine summary for the public"
EMA_MONO = "EMA/HMPC, EU herbal monograph"
NO_SIDE = "At the time of the HMPC assessment, no side effects had been reported with these medicines."

ENTRIES: list[tuple] = [
    ("Artemisia absinthium", "concern_reported", "EMA contraindicates wormwood herb medicines in allergy to wormwood or other Asteraceae, and in liver disease and bile-duct disorders.",
     "ema", EMA_DOC["wormwood"], EMA_SUMMARY + " (wormwood herb)",
     "They must also not be taken by patients with bile duct obstruction, cholangitis (inflammation of the bile ducts) or liver disease."),
    ("Agrimonia eupatoria", "no_toxicity_reported", "EMA reported no side effects at its assessment; this is not evidence of safety.",
     "ema", EMA_DOC["agrimony"], EMA_SUMMARY + " (agrimony)", NO_SIDE),
    ("Crocus sativus", "toxic_reported", "A review reports adverse effects in humans above about 5 g/day and moderate toxicity of an ethanolic extract in zebrafish.",
     "pmc", "PMC12729493", "Review, PMC (open access)",
     "Although doses exceeding 5 g/day in humans may lead to adverse effects, the IC 50 of saffron ethanolic extract in zebrafish was determined to be 1021.374 mg/L, indicating moderate toxicity."),
    ("Symphytum officinale", "toxic_reported", "EMA: comfrey root contains pyrrolizidine alkaloids that are toxic to the liver when taken by mouth.",
     "ema", EMA_DOC["comfrey"], EMA_SUMMARY + " (comfrey root)",
     "Comfrey root contains substances known as pyrrolizidine alkaloids, which have toxic effects on the liver when taken by mouth."),
    ("Lavandula angustifolia", "data_lacking", "EMA monograph: reproductive toxicity, genotoxicity and carcinogenicity have not been tested.",
     "ema", EMA_DOC["lavender"], EMA_MONO + " (Lavandula angustifolia, flos)",
     "Tests on reproductive toxicity, genotoxicity and carcinogenicity have not been performed."),
    ("Ajuga chamaepitys", "no_toxicity_reported", "Invertebrate assays only (Daphnia, Artemia); the same paper reports toxicity to Daphnia pulex at high concentration. No mammalian data; not evidence of safety.",
     "pmc", "PMC11085171", "Primary study, PMC (open access)",
     "The extract was virtually non-toxic to Daphnia magna throughout the exposure period, with the highest recorded average lethality being 10%."),
    ("Ranunculus ficaria", "toxic_reported", "A single human case report of acute toxic liver injury attributed to lesser celandine.",
     "pmc", "PMC4342611", "Case report, PMC (open access)",
     "This case is the first to explain hepatotoxicity caused by lesser celandine."),
    ("Glycyrrhiza glabra", "toxic_reported", "EMA monograph: overdose with prolonged or high intake causes water retention, hypokalaemia, hypertension, cardiac rhythm disorders and hypertensive encephalopathy.",
     "ema", EMA_DOC["liquorice"], EMA_MONO + " (Glycyrrhiza spp., radix, revision 1)",
     "Cases of overdose have been reported with prolonged use (more than 4 weeks) and/or intake of high amount of liquorice, with symptoms such as water retention, hypokalaemia, hypertension, cardiac rhythm disorders, and hypertensive encephalopathy."),
    ("Melissa officinalis", "no_toxicity_reported", "EMA reported no side effects at its assessment; this is not evidence of safety.",
     "ema", EMA_DOC["melissa"], EMA_SUMMARY + " (melissa leaf)", NO_SIDE),
    ("Hyssopus officinalis", "toxic_reported", "Review: ingesting hyssop essential oil may cause convulsions (pinocamphone). About the essential oil, not whole-herb preparations.",
     "pmc", "PMC7956842", "Review, PMC (open access)",
     "Ingestion of hyssop oil might cause epileptiform convulsions [ 207 ] and seizures due to its high pinocamphone content [ 121 ]."),
    ("Pastinaca sativa", "concern_reported", "Review: phototoxicity on skin contact (furanocoumarins).",
     "pmc", "PMC8010426", "Review, PMC (open access)",
     "A main mentioned side effect of parsnip is phototoxicity that was usually reported in direct skin contact."),
    ("Galium aparine", "no_toxicity_reported", "In vitro cell assay only; no in vivo toxicity source located. Not evidence of safety.",
     "pmc", "PMC11267910", "Primary study, PMC (open access)",
     "The results of the viability assay showed no cytotoxicity effects on human umbilical endothelial cell (HUVEC) and normal human dermal fibroblast (NHDF) cell lines treated with different concentrations of whole plant extract and cell viability increased in a dose-dependent manner."),
    ("Centaurium erythraea", "concern_reported", "EMA contraindicates centaury medicines in stomach ulcers; no side effects had been reported at its assessment.",
     "ema", EMA_DOC["centaury"], EMA_SUMMARY + " (centaury)", "Centaury medicines should not be taken by people with ulcers in the stomach."),
    ("Chelidonium majus", "toxic_reported", "EMA public statement: products withdrawn in some EU countries over reported adverse effects, particularly liver toxicity.",
     "ema", EMA_DOC["celandine"], "EMA/HMPC, public statement (Chelidonium majus L., herba)",
     "In some European countries marketing authorisations for medicinal products containing Chelidonium majus have been withdrawn because of concerns with reported adverse effects, particularly liver toxicity."),
    ("Hyoscyamus niger", "toxic_reported", "Clinical toxicology review: tropane-alkaloid poisoning, possibly fatal, though the review notes that deaths are very rare.",
     "pmc", "PMC4224707", "Review, PMC (open access)",
     "One of the most important and geographically common plants is Hyoscyamus Niger with therapeutic and possible toxic effects, which may be even fatal."),
    ("Raphanus sativus", "concern_reported", "Systematic review: radish root affected thyroid activity in two rat studies (one found signs of hypothyroidism; the other reached different conclusions). Not poisoning.",
     "pmc", "PMC11012840", "Systematic review, PMC (open access)",
     "A noticeable influence on thyroid activity by radish root was observed in two studies on rats ( Table 6 )."),
    ("Laser trilobum", "unknown", "No reputable open source on toxicity located in this session (PMC searches for Laser trilobum and Siler trilobum). Not evidence of safety.",
     None, None, None, None),
    ("Salvia sclarea", "no_toxicity_reported", "In vitro cell assay only; the same paper notes a modest drop in HEK 293 viability at the highest concentrations. Not evidence of safety.",
     "pmc", "PMC13075098", "Primary study, PMC (open access)",
     "After treatment of HEK 293 and HaCaT cells with increasing concentrations of S. sclarea and S. pratensis extracts (10–200 µg/mL), no significant increase in lactate dehydrogenase (LDH) release was observed compared to the control, indicating that the extracts did not induce detectable cytotoxicity or membrane damage in the tested cell lines after 24 h, as indicates Figure 7 ."),
    ("Euphorbia antiquorum", "toxic_reported", "Genus-level review: the latex of most Euphorbia species is toxic, causing severe skin irritation and possibly blindness. "
     "Not specific to E. antiquorum. (Replaces an earlier no_toxicity_reported entry from a root-extract test, after review.)",
     "pmc", "PMC11821031", "Review of Euphorbia species, PMC (open access)",
     "However, it is critical to note that the latex produced by most Euphorbia species is toxic and can induce severe skin irritation and potentially lead to blindness."),
    ("Papaver somniferum", "toxic_reported", "Review and case study: tea from unwashed poppy seeds can carry enough morphine to cause dependence.",
     "pmc", "PMC6513924", "Review and case study, PMC (open access)",
     "Unwashed poppy seeds may contain sufficient alkaloid residue to produce tea with a substantial morphine content to the extent that regular users can develop dependence and opioid use disorder."),
    ("Humulus lupulus", "no_toxicity_reported", "EMA reported no side effects at its assessment; this is not evidence of safety.",
     "ema", EMA_DOC["hop"], EMA_SUMMARY + " (hop strobile)", NO_SIDE),
    ("Allium cepa", "toxic_reported", "Veterinary review: onion causes oxidative haemolysis (anaemia) in cats, dogs and cattle. Animal evidence, not human.",
     "pmc", "PMC9495094", "Veterinary review, PMC (open access)",
     "Cats, dogs and cattle appear most susceptible to the onion’s toxic effects, whereas sheep and goats are more resistant."),
    ("Coriandrum sativum", "data_lacking", "Review: recommends further study of toxicity and adverse effects at higher doses and over longer periods (it cites food-use status in the USA).",
     "pmc", "PMC9314633", "Review, PMC (open access)",
     "Although the safety of coriander has been confirmed by the United States Food and Drug Administration (FDA) and the Flavor and Extract Manufacturers Association (FEMA), further studies are recommended to investigate the toxicity and adverse effects of this plant when consumed at higher doses and longer periods of time."),
    ("Carum carvi", "concern_reported", "EMA contraindicates caraway fruit medicines in allergy to caraway, other Apiaceae, mugwort or birch.",
     "ema", EMA_DOC["caraway"], EMA_SUMMARY + " (caraway fruit)",
     "Caraway fruit medicines must not be used in patients who are hypersensitive (allergic) to caraway fruit or other plants of the Apiaceae (Umbelliferae) family (fennel, anise, celery, coriander and dill), to mugwort or birch."),
    ("Citrullus colocynthis", "toxic_reported", "Human case report: multiorgan toxicity after eating the fruit.",
     "pmc", "PMC12522648", "Case report, PMC (open access)",
     "Citrullus colocynthis , a plant traditionally used for its purgative properties, is known for its severe toxicity when consumed in excessive amounts."),
    ("Cotinus coggygria", "toxic_reported", "Review: a methanol extract was genotoxic in Drosophila germ cells. A laboratory finding, not poisoning.",
     "pmc", "PMC4890191", "Review, PMC (open access)",
     "The SLRL test revealed the genotoxic effect of the 5% methanol extract on the eukaryotic model system Drosophila melanogaster in premeiotic germinative cell lines, i.e. spermatozoids, as well as spermatocytes, while spermatids proved to be more resistant to the genotoxic effects of the extract ( Matić et al., 2011b )."),
    ("Dioscorea communis", "concern_reported", "Review: the rhizome extract irritates the skin (the source frames this as therapeutic). No poisoning source located.",
     "pmc", "PMC8949886", "Review, PMC (open access)",
     "The TCR extract has an irritating effect on the skin, thus improving the blood supply to the affected area [ 1 ]."),
    ("Filipendula ulmaria", "concern_reported", "EMA monograph: contraindicated in hypersensitivity to salicylates; not recommended with salicylates or NSAIDs without medical advice.",
     "ema", EMA_DOC["meadowsweet"], EMA_MONO + " (Filipendula ulmaria, herba)",
     "Concomitant use with salicylates and other NSAIDs is not recommended without medical advice."),
    ("Betonica officinalis", "unknown", "No reputable open source on toxicity located in this session (genus-level Stachys reviews cover other species only). Not evidence of safety.",
     None, None, None, None),
    ("Moricandia arvensis", "unknown", "No reputable open source on toxicity located in this session (papers found address anti-genotoxicity or cancer-cell cytotoxicity only). Not evidence of safety.",
     None, None, None, None),
]


# What the cited evidence covers, when it is narrower than "this species, in people" (shown beside the category).
SCOPE = {
    "Allium cepa": "animals only (veterinary); not evidence about people at food doses",
    "Euphorbia antiquorum": "genus-level (Euphorbia latex)",
    "Ajuga chamaepitys": "invertebrate assays only",
    "Galium aparine": "in vitro only",
    "Salvia sclarea": "in vitro only",
    "Raphanus sativus": "animal studies (rats)",
    "Hyssopus officinalis": "essential oil only",
    "Papaver somniferum": "one preparation (unwashed poppy-seed tea)",
}


class ToxicityError(ValueError):
    pass


def _norm(s: str) -> str:
    s = s.replace("­", "").replace("ﬁ", "fi").replace("ﬂ", "fl")
    s = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s)  # PDF line-end hyphenation
    return re.sub(r"\s+", " ", s).strip()


def _source(kind: str, loc: str) -> tuple[str, str, str, str, str]:
    """-> (normalised text, url, sha256, retrievedAt, licence)."""
    if kind == "ema":
        url = EMA + loc
        text, sha, when = get_pdf_text("ema", url)
        t = _norm(text)
        lic = (f"EMA: '{EMA_LICENCE}.'" if EMA_LICENCE in t else "unknown (EMA reuse statement not found in document)")
        return t, url, sha, when, lic
    if kind == "pmc":
        url = PMC.format(loc)
        raw, sha, when = get_text("sources", url)
        lm = re.search(r"creativecommons\.org/licenses/([a-z-]+)/(\d\.\d)", raw)
        lic = f"CC {lm.group(1).upper()} {lm.group(2)}" if lm else "none stated"
        cut = min([i for i in (raw.find('class="ref-list'), raw.find('id="ref-list')) if i > 0] or [len(raw)])
        return _norm(html.unescape(re.sub(r"<[^>]+>", " ", raw[:cut]))), url, sha, when, lic
    raise ToxicityError(f"unknown source kind {kind!r}")


def build(species: list[str] | None = None) -> pd.DataFrame:
    by = {e[0]: e for e in ENTRIES}
    if len(by) != len(ENTRIES):
        raise ToxicityError("duplicate species in ENTRIES")
    rows = []
    for sp in species or list(by):
        e = by.get(sp)
        if e is None:
            raise ToxicityError(f"no curated toxicity decision for {sp!r}")
        _, cat, summary, kind, loc, name, quote = e
        if cat not in CATEGORIES:
            raise ToxicityError(f"{sp}: bad category {cat!r}")
        row = {"acceptedName": sp, "toxicity": cat, "evidenceScope": SCOPE.get(sp, "species"), "summary": summary, "sourceName": name or "", "sourceUrl": "",
               "quote": quote or "", "sourceSha256": "", "retrievedAt": "", "licence": "", "basis": BASIS, "verified_by": ""}
        if kind:
            text, url, sha, when, lic = _source(kind, loc)
            if lic.startswith(("none", "unknown")):
                raise ToxicityError(f"{sp}: source has no stated reuse licence; do not quote it")
            if _norm(quote) not in text:
                raise ToxicityError(f"{sp}: quote not found in fetched source {url}: {quote[:90]!r}")
            row.update(sourceUrl=url, sourceSha256=sha, retrievedAt=when, licence=lic)
        elif cat != "unknown":
            raise ToxicityError(f"{sp}: a category other than 'unknown' needs a source")
        rows.append(row)
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    return df


def table() -> pd.DataFrame:
    """The curated table as last built (build() must have run)."""
    return pd.read_csv(OUT, dtype=str).fillna("")
