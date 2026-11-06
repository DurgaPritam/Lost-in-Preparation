from build_batch import R, write
P = {}
PW = "the-lesser-celandine-usually-known-by-the-name-of-pilewort-a"
CY = "clary-or-more-properly-clear-eye"
for pid in (f"{PW}:001", f"{PW}:002", f"{PW}:003", f"{PW}:004", f"{CY}:001", f"{CY}:002", f"{CY}:003"):
    P["culpeper-1850:herbal:" + pid] = []   # intro / description / place / time
PI = "PILEWORT"
P[f"culpeper-1850:herbal:{PW}:005"] = [
    R("the decoction of the leaves and roots wonderfully helps piles and hæmorrhoids, also kernels by the ears and throat, called the king’s evil, or any other hard wens or tumours",
      PI, "piles and hæmorrhoids, also kernels by the ears and throat, called the king’s evil, or any other hard wens or tumours", heading=True, part="other",
      heat="boiled", process="decoction",
      ev={"part": "the leaves and roots", "heat": "the decoction of the leaves and roots", "process": "the decoction of the leaves and roots"}),
]   # the root's 'signature' of the piles: doctrine, the use is recorded from the decoction sentence
Q = "Pilewort made into an oil, ointment, or plaister, readily cures both the piles, or hæmorrhoids, and the king’s evil"
P[f"culpeper-1850:herbal:{PW}:006"] = [
    R(Q, "Pilewort", "the piles, or hæmorrhoids, and the king’s evil", solvent=("oil",), form="ointment", filt="not_applicable",
      ev={"solvent": "made into an oil, ointment", "form": "made into an oil, ointment", "filtered": "made into an oil, ointment"}),
    R(Q, "Pilewort", "the piles, or hæmorrhoids, and the king’s evil", form="plaster", filt="not_applicable",
      ev={"form": "ointment, or plaister", "filtered": "ointment, or plaister"}),
    R("The very herb borne about one’s body next the skin helps in such diseases, though it never touch the place grieved", "Pilewort", "such diseases",
      solvent=("none",), form="other", filt="not_applicable",
      ev={"solvent": "The very herb borne about one’s body", "form": "The very herb borne about one’s body next the skin",
          "filtered": "though it never touch the place grieved"}),
]
CL = "CLARY"
QL = "The leaves used with vinegar, either by itself, or with a little honey, doth help boils, felons, and the hot inflammation that are gathered by their pains"
IL = "boils, felons, and the hot inflammation that are gathered by their pains"
P[f"culpeper-1850:herbal:{CY}:004"] = [
    R("The seed put into the eyes clears them from motes, and such like things gotten within the lids to offend them, as also clears them from white and red spots on them.",
      CL, "clears them from motes, and such like things gotten within the lids to offend them, as also clears them from white and red spots on them",
      heading=True, part="seed", form="other", ev={"part": "The seed put into the eyes", "form": "put into the eyes"}),
    R("The mucilage of the seed made with water, and applied to tumours, or swellings, disperses and takes them away; as also draws forth splinters, thorns, or other things gotten into the flesh.",
      CL, "tumours, or swellings, disperses and takes them away; as also draws forth splinters, thorns, or other things gotten into the flesh", heading=True,
      part="seed", solvent=("water",), process="other", form="poultice", filt="not_applicable",
      ev={"part": "The mucilage of the seed", "solvent": "made with water", "process": "The mucilage of the seed made with water",
          "form": "applied to tumours, or swellings", "filtered": "applied to tumours, or swellings"}),
    R(QL, CL, IL, heading=True, part="leaf", solvent=("vinegar",), ev={"part": "The leaves used", "solvent": "used with vinegar, either by itself"}),
    R(QL, CL, IL, heading=True, part="leaf", solvent=("vinegar", "honey"), ev={"part": "The leaves used", "solvent": ["used with vinegar", "with a little honey"]}),
    R("The powder of the dried root put into the nose, provokes sneezing, and thereby purges the head and brain of much rheum and corruption.", CL,
      "purges the head and brain of much rheum and corruption", heading=True, part="root", fod="dried", heat="cold", process="powder", form="inhalation",
      ev={"part": "the dried root", "freshOrDried": "the dried root", "heat": "The powder of the dried root", "process": "The powder of the dried root",
          "form": "put into the nose, provokes sneezing"}),
    R("The seed or leaves taken in wine, provokes to venery.", CL, "provokes to venery", heading=True, part="seed", solvent=("wine",), form="drink",
      ev={"part": "The seed or leaves", "solvent": "taken in wine", "form": "taken in wine"}),
    R("The seed or leaves taken in wine, provokes to venery.", CL, "provokes to venery", heading=True, part="leaf", solvent=("wine",), form="drink",
      ev={"part": "The seed or leaves", "solvent": "taken in wine", "form": "taken in wine"}),
    R("It is of much use both for men and women that have weak backs, and helps to strengthen the reins: used either by itself, or with other herbs conducing to the same effect",
      CL, "men and women that have weak backs, and helps to strengthen the reins", heading=True),
    R("The fresh leaves dipped in a batter of flour, eggs, and a little milk, and fried in butter, and served to the table, is not unpleasant to any, but exceedingly profitable for those that are troubled with weak backs, and the effects thereof.",
      CL, "those that are troubled with weak backs, and the effects thereof", heading=True, rtype="compound",
      ingredients=[(CL, "leaf", "principal", "plant"), ("flour", "unknown", "co_ingredient", "other"), ("eggs", "unknown", "co_ingredient", "animal")],
      part="leaf", fod="fresh", solvent=("other",), heat="warm", heatText="fried in butter", process="other", form="other",
      ev={"part": "The fresh leaves", "freshOrDried": "The fresh leaves", "solvent": ["a little milk", "fried in butter"], "heat": "fried in butter",
          "process": "dipped in a batter of flour, eggs, and a little milk, and fried in butter", "form": "served to the table"}),
    R("The juice of the herb put into ale or beer, and drank, brings down women’s courses, and expels the after-birth.", CL,
      "brings down women’s courses, and expels the after-birth", heading=True, part="juice", solvent=("other",), heat="cold", form="drink",
      ev={"part": "The juice of the herb", "solvent": "put into ale or beer", "heat": "The juice of the herb put into ale or beer", "form": "and drank"}),
]
print(write("approved", 14, P))
