from build_batch import R, write
P = {}
for pid in ("cleavers:001", "cleavers:002", "cleavers:003", "cleavers:004", "henbane:001", "henbane:002", "henbane:003"):
    P["culpeper-1850:herbal:" + pid] = []   # names / description / place / time
C = "CLEAVERS"
JL = "The juice of the leaves, or they a little bruised, and applied to any bleeding wounds, stays the bleeding."
P["culpeper-1850:herbal:cleavers:005"] = [
    R("The juice of the herb and the seed together taken in wine, helps those bitten with an adder, by preserving the heart from the venom.", C,
      "those bitten with an adder, by preserving the heart from the venom", heading=True, part="other", solvent=("wine",), form="drink",
      ev={"part": "The juice of the herb and the seed together", "solvent": "taken in wine", "form": "taken in wine"}),
    R("It is familiarly taken in broth to keep them lean and lank, that are apt to grow fat.", C, "to keep them lean and lank, that are apt to grow fat",
      heading=True, solvent=("other",), form="drink", ev={"solvent": "taken in broth", "form": "taken in broth"}),
    R("The distilled water drank twice a day, helps the yellow jaundice", C, "the yellow jaundice", heading=True, solvent=("water",), heat="boiled",
      process="distillation", form="drink",
      ev={"solvent": "The distilled water", "heat": "The distilled water", "process": "The distilled water", "form": "The distilled water drank"}),
    R("the decoction of the herb, in experience, is found to do the same, and stays lasks and bloody-fluxes", C, "to do the same, and stays lasks and bloody-fluxes",
      heading=True, heat="boiled", process="decoction", ev={"heat": "the decoction of the herb", "process": "the decoction of the herb"}),
    R(JL, C, "any bleeding wounds, stays the bleeding", heading=True, part="juice", heat="cold",
      ev={"part": "The juice of the leaves", "heat": "The juice of the leaves"}),
    R(JL, C, "any bleeding wounds, stays the bleeding", heading=True, part="leaf", heat="cold", process="other", form="poultice", filt="not_applicable",
      ev={"part": "The juice of the leaves, or they a little bruised", "heat": "a little bruised, and applied", "process": "a little bruised, and applied",
          "form": "a little bruised, and applied to any bleeding wounds", "filtered": "a little bruised, and applied"}),
    R("The juice also is very good to close up the lips of green wounds", C, "to close up the lips of green wounds", heading=True, part="juice", heat="cold",
      ev={"part": "The juice also is very good", "heat": "The juice also is very good"}),
    R("the powder of the dried herb strewed thereupon doth the same, and likewise helps old ulcers", C, "doth the same, and likewise helps old ulcers",
      heading=True, fod="dried", solvent=("none",), heat="cold", process="powder",
      ev={"freshOrDried": "the dried herb", "solvent": "the powder of the dried herb strewed thereupon", "heat": "the powder of the dried herb",
          "process": "the powder of the dried herb"}),
    R("Being boiled in hog’s grease, it helps all sorts of hard swellings or kernels in the throat, being anointed therewith.", C,
      "all sorts of hard swellings or kernels in the throat", heading=True, solvent=("other",), heat="boiled", process="other", form="ointment",
      filt="not_applicable",
      ev={"solvent": "Being boiled in hog’s grease", "heat": "Being boiled in hog’s grease", "process": "Being boiled in hog’s grease",
          "form": "being anointed therewith", "filtered": "being anointed therewith"}),
    R("The juice dropped into the ears, takes away the pain of them.", C, "takes away the pain of them", heading=True, part="juice", heat="cold", form="other",
      ev={"part": "The juice dropped into the ears", "heat": "The juice dropped into the ears", "form": "The juice dropped into the ears"}),
]
P["culpeper-1850:herbal:cleavers:006"] = [
    R("It is a good remedy in the Spring, eaten (being first chopped small, and boiled well) in water-gruel, to cleanse the blood, and strengthen the liver, thereby to keep the body in health, and fitting it for that change of season that is coming.",
      C, "to cleanse the blood, and strengthen the liver, thereby to keep the body in health, and fitting it for that change of season that is coming",
      heading=True, solvent=("other",), heat="boiled", form="other",
      ev={"solvent": "in water-gruel", "heat": "being first chopped small, and boiled well", "form": "eaten (being first chopped small, and boiled well)"}),
]
H = "Henbane"
SW = ("all manner of swellings of the privities, or women’s breast, or elsewhere, if they be boiled in wine, and either applied themselves, or the fomentation "
      "warm; it also assuages the pain of the gout, the sciatica, and other pains in the joints which arise from a hot cause")
QSW = "are good to assuage " + SW
ANT = "Fennel seed, Nettle seed, the seed of Cresses, Mustard, or Radish; as also Onions or Garlic taken in wine, do all help to free them from danger, and restore them to their due temper again"
AI = "free them from danger, and restore them to their due temper again"
def a(name, part):
    return R(ANT, name, AI, part=part, ev={"part": name} if part != "unknown" else None)
P["culpeper-1850:herbal:henbane:004"] = [
    R("The leaves of Henbane do cool all hot inflammations in the eyes, or any other part of the body", H, "cool all hot inflammations in the eyes, or any other part of the body",
      part="leaf", ev={"part": "The leaves of Henbane"}),
    R(QSW, H, SW, part="leaf", solvent=("wine",), heat="boiled", process="decoction", form="poultice", filt="not_applicable",
      ev={"part": "The leaves of Henbane", "solvent": "boiled in wine", "heat": "boiled in wine", "process": "if they be boiled in wine",
          "form": "applied themselves", "filtered": "applied themselves"}),
    R(QSW, H, SW, part="leaf", solvent=("wine",), heat="boiled", heatText="the fomentation warm", process="decoction", form="other",
      ev={"part": "The leaves of Henbane", "solvent": "boiled in wine", "heat": "boiled in wine", "process": "if they be boiled in wine",
          "form": "the fomentation warm"}),
    R("And applied with vinegar to the forehead and temples, helps the head-ache and want of sleep in hot fevers.", H, "the head-ache and want of sleep in hot fevers",
      part="leaf", solvent=("vinegar",), form="poultice", filt="not_applicable",
      ev={"part": "The leaves of Henbane", "solvent": "applied with vinegar", "form": "applied with vinegar to the forehead and temples",
          "filtered": "applied with vinegar to the forehead and temples"}),
    R("The juice of the herb or seed, or the oil drawn from the seed, does the like.", H, "does the like", part="juice", heat="cold",
      ev={"part": "The juice of the herb or seed", "heat": "The juice of the herb or seed"}),
    R("The juice of the herb or seed, or the oil drawn from the seed, does the like.", H, "does the like", part="seed", process="other",
      ev={"part": "the oil drawn from the seed", "process": "the oil drawn from the seed"}),
    R("The oil of the seed is helpful for deafness, noise, and worms in the ears, being dropped therein", H, "deafness, noise, and worms in the ears",
      part="seed", process="other", form="other",
      ev={"part": "The oil of the seed", "process": "The oil of the seed", "form": "being dropped therein"}),
    R("the juice of the herb or root doth the same", H, "doth the same", part="juice", heat="cold",
      ev={"part": "the juice of the herb or root", "heat": "the juice of the herb or root"}),
    R("The decoction of the herb or seed, or both, kills lice in man or beast.", H, "kills lice in man or beast", heat="boiled", process="decoction",
      ev={"heat": "The decoction of the herb", "process": "The decoction of the herb"}),
    R("The fume of the dried herb, stalks and seed, burned, quickly heals swellings, chilblains or kibes in the hands or feet, by holding them in the fume thereof.",
      H, "swellings, chilblains or kibes in the hands or feet", part="other", fod="dried", process="other", form="inhalation", filt="not_applicable",
      ev={"part": "the dried herb, stalks and seed", "freshOrDried": "the dried herb", "process": "stalks and seed, burned", "form": "The fume of the dried herb",
          "filtered": "by holding them in the fume thereof"}),
    R("The remedy to help those that have taken Henbane is to drink goat’s milk, honeyed water, or pine kernels, with sweet wine", "pine kernels",
      "help those that have taken Henbane", part="seed", solvent=("wine",), form="drink",
      ev={"part": "pine kernels", "solvent": "with sweet wine", "form": "is to drink"}),
    a("Fennel seed", "seed"), a("Nettle seed", "seed"), a("the seed of Cresses", "seed"), a("Mustard", "unknown"), a("Radish", "unknown"),
    R(ANT, "Onions", AI, solvent=("wine",), form="drink", ev={"solvent": "Onions or Garlic taken in wine", "form": "Onions or Garlic taken in wine"}),
    R(ANT, "Garlic", AI, solvent=("wine",), form="drink", ev={"solvent": "Garlic taken in wine", "form": "Garlic taken in wine"}),
]
print(write("approved", 15, P))
