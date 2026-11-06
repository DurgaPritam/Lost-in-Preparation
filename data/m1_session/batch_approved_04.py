from build_batch import R, write
P = {}
PW = "the-iesser-celondine-usually-known-by-the-name-of-pilewort"
for pid in (f"{PW}:003", f"{PW}:005", f"{PW}:007", "clary:002", "clary:004", "clary:006"):
    P["culpeper-1652:herbal:" + pid] = []   # description / place / time
PI = "Pilewort"
P[f"culpeper-1652:herbal:{PW}:009"] = [
    R("the Decoction of the Leavs and Roots, doth wonderfully help the Piles and Hemorrhoids, as also Kernels by the Ears and Throat called the Kings evil; or any other hard Wens or Tumors",
      PI, "the Piles and Hemorrhoids, as also Kernels by the Ears and Throat called the Kings evil; or any other hard Wens or Tumors", heading=True,
      part="other", heat="boiled", process="decoction",
      ev={"part": "the Leavs and Roots", "heat": "the Decoction of the Leavs and Roots", "process": "the Decoction of the Leavs and Roots"}),
]
Q = "Pilewort being made into an Oyl Oyntment or Plaister, readily cures both the Piles or Hemorrhoids, and the Kings Evil"
P[f"culpeper-1652:herbal:{PW}:010"] = [
    R(Q, PI, "the Piles or Hemorrhoids, and the Kings Evil", solvent=("oil",), form="ointment", filt="not_applicable",
      ev={"solvent": "made into an Oyl Oyntment", "form": "made into an Oyl Oyntment", "filtered": "made into an Oyl Oyntment"}),
    R(Q, PI, "the Piles or Hemorrhoids, and the Kings Evil", form="plaster", filt="not_applicable",
      ev={"form": "Oyntment or Plaister", "filtered": "Oyntment or Plaister"}),
    R("the very Herb born about ones Body ne⟦??⟧ the Skin, helps in such Diseases, though it never touch the place grieved", PI, "such Diseases",
      heading=True, solvent=("none",), form="other", filt="not_applicable",
      ev={"solvent": "the very Herb born about ones Body", "form": "the very Herb born about ones Body", "filtered": "though it never touch the place grieved"}),
]
CL = "Clary"
INF = "hot Inflamations, as also Boyls, Felons, and the hot Inflamations that are gathered by their pains"
QL = "The Leavs used with Vinegar either by it self or with a little Honey, doth help hot Inflamations, as also Boyls, Felons, and the hot Inflamations that are gathered by their pains"
P["culpeper-1652:herbal:clary:008"] = [
    R("The Seed is used to be put into the Eyes to cleer them from Moats, or other such like things gotten within the Lids to offend them, as also to clear them from white or red spots in them",
      CL, "cleer them from Moats, or other such like things gotten within the Lids to offend them, as also to clear them from white or red spots in them",
      heading=True, part="seed", form="other", ev={"part": "The Seed is used", "form": "put into the Eyes"}),
    R("The Muccilage of the Seed made with Water, and applied to Tumors and swellings, disperseth and taketh them away, as also draweth forth Splinters, Thorns, or other things gotten into the Flesh",
      CL, "Tumors and swellings, disperseth and taketh them away, as also draweth forth Splinters, Thorns, or other things gotten into the Flesh",
      heading=True, part="seed", solvent=("water",), process="other", form="poultice", filt="not_applicable",
      ev={"part": "The Muccilage of the Seed", "solvent": "made with Water", "process": "The Muccilage of the Seed made with Water",
          "form": "applied to Tumors and swellings", "filtered": "applied to Tumors and swellings"}),
    R(QL, CL, INF, heading=True, part="leaf", solvent=("vinegar",), ev={"part": "The Leavs used", "solvent": "used with Vinegar either by it self"}),
    R(QL, CL, INF, heading=True, part="leaf", solvent=("vinegar", "honey"),
      ev={"part": "The Leavs used", "solvent": ["used with Vinegar", "with a little Honey"]}),
    R("The Pouder of the dried Leavs put into the Nose provoketh neesing, and therby purgeth the Head and Brain of much Rhewm and Corruption",
      CL, "purgeth the Head and Brain of much Rhewm and Corruption", heading=True, part="leaf", fod="dried", heat="cold", process="powder",
      form="inhalation",
      ev={"part": "the dried Leavs", "freshOrDried": "the dried Leavs", "heat": "The Pouder of the dried Leavs", "process": "The Pouder of the dried Leavs",
          "form": "put into the Nose provoketh neesing"}),
    R("The Seed or Leavs taken in Wine provoketh to Venery", CL, "provoketh to Venery", heading=True, part="seed", solvent=("wine",), form="drink",
      ev={"part": "The Seed or Leavs", "solvent": "taken in Wine", "form": "taken in Wine"}),
    R("The Seed or Leavs taken in Wine provoketh to Venery", CL, "provoketh to Venery", heading=True, part="leaf", solvent=("wine",), form="drink",
      ev={"part": "The Seed or Leavs", "solvent": "taken in Wine", "form": "taken in Wine"}),
    R("It is of much use both for Men and Women that have weak Backs, to help to strengthen the Reins, used either by it self or with other Herbs conducing to the same effect",
      CL, "Men and Women that have weak Backs, to help to strengthen the Reins", heading=True),
    R("The fresh Leavs dipped in a Batter of Flower, Egs, and a little Milk, and fried in Butter, and served to the Table, is not unpleasant to any, but exceeding profitable for those that are troubled with weak Backs, and the effects therof",
      CL, "those that are troubled with weak Backs, and the effects therof", heading=True, rtype="compound",
      ingredients=[(CL, "leaf", "principal", "plant"), ("Flower", "unknown", "co_ingredient", "other"), ("Egs", "unknown", "co_ingredient", "animal")],
      part="leaf", fod="fresh", solvent=("other",), heat="warm", heatText="fried in Butter", process="other", form="other",
      ev={"part": "The fresh Leavs", "freshOrDried": "The fresh Leavs", "solvent": ["a little Milk", "fried in Butter"], "heat": "fried in Butter",
          "process": "dipped in a Batter of Flower, Egs, and a little Milk, and fried in Butter", "form": "served to the Table"}),
    R("The Juyce of the Herb put into Ale or Beer, and drunk, bringeth down Womens Courses, and expelleth the After-birth", CL,
      "bringeth down Womens Courses, and expelleth the After-birth", heading=True, part="juice", solvent=("other",), heat="cold", form="drink",
      ev={"part": "The Juyce of the Herb", "solvent": "put into Ale or Beer", "heat": "The Juyce of the Herb put into Ale or Beer", "form": "and drunk"}),
]
P["culpeper-1652:herbal:clary:009"] = [
    R("when they have gotten the running of the Reins, or Women the Whites, then run to the bush of Clary; Maid bring hither the Frying Pan, fetch me some Butter quickly, then to eating fryed Clary",
      CL, "the running of the Reins, or Women the Whites", solvent=("other",), heat="warm", heatText="fryed", process="other", form="other",
      ev={"solvent": "fetch me some Butter quickly", "heat": "eating fryed Clary", "process": "bring hither the Frying Pan", "form": "eating fryed Clary"}),
]   # reported practice the author disputes; recorded as written
print(write("approved", 4, P))
