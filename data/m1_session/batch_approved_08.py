from build_batch import R, write
P = {}
GP_ = "ground-pine-or-chamepitys"
MS_ = "queen-of-the-meadows-meadow-sweet-or-mead-sweet"
for pid in (f"{GP_}:002", f"{GP_}:004", f"{GP_}:006", f"{GP_}:009", f"{MS_}:002", f"{MS_}:004", f"{MS_}:006"):
    P["culpeper-1652:herbal:" + pid] = []   # description / place / time / warning
G = "Ground Pine"
JO = "It is as effectual also in all pains and Diseases of the Joynts, as Gouts, Cramps, Palseys, Sciatica, and Aches; either the Decoction of the Herb in 'Wine taken inwardly"
JI = "all pains and Diseases of the Joynts, as Gouts, Cramps, Palseys, Sciatica, and Aches"
PILLS = [(G, "unknown", "principal", "plant"), ("Hermodactils", "unknown", "co_ingredient", "plant"), ("Venice Turpentine", "resin", "co_ingredient", "plant")]
GH = "The green Herb or the Decoction thereof being applied, dissolveth the hardness of Womens Breasts, and all other hard Swellings in any other part of the Body"
GHI = "dissolveth the hardness of Womens Breasts, and all other hard Swellings in any other part of the Body"
GU = "The green Herb also applied, or the Juyce thereof with some Honey, not only clenseth putrid, stinking foul and Malignant Ulcers and Sores of all sorts, but healeth and sodereth up the lips of green Wounds in any part also"
GUI = "clenseth putrid, stinking foul and Malignant Ulcers and Sores of all sorts, but healeth and sodereth up the lips of green Wounds in any part also"
P[f"culpeper-1652:herbal:{GP_}:008"] = [
    R("The Decoction of Ground Pine drunk, doth wonderfully prevail against the Strangury or any inward pains arising from the Diseases of the Reins and Urine, and is especial good for all Obstructions of the Liver and Spleen and gently openeth the Body",
      G, "the Strangury or any inward pains arising from the Diseases of the Reins and Urine, and is especial good for all Obstructions of the Liver and Spleen and gently openeth the Body",
      heat="boiled", process="decoction", form="drink",
      ev={"heat": "The Decoction of Ground Pine", "process": "The Decoction of Ground Pine", "form": "The Decoction of Ground Pine drunk"}),
    R("gently openeth the Body, for which purpose they were wont in former times to make Pills with the Pouder thereof, and the Purple Figs", G,
      "gently openeth the Body", rtype="compound", ingredients=[(G, "unknown", "principal", "plant"), ("Purple Figs", "fruit", "co_ingredient", "plant")],
      process="powder", form="other", ev={"process": "Pills with the Pouder thereof", "form": "to make Pills"}),
    R("It marveilously helpeth all the Diseases of the Mother used inwardly, or applied outwardly, procuring Womens Courses, and expelling the dead Child and afterbirth",
      G, "all the Diseases of the Mother used inwardly, or applied outwardly, procuring Womens Courses, and expelling the dead Child and afterbirth"),
    R(JO, G, JI, solvent=("wine",), heat="boiled", process="decoction", form="drink",
      ev={"solvent": "the Decoction of the Herb in 'Wine", "heat": "the Decoction of the Herb", "process": "the Decoction of the Herb", "form": "taken inwardly"}),
    R(JO + ", or applied outwardly", G, JI, solvent=("wine",), heat="boiled", process="decoction",
      ev={"solvent": "the Decoction of the Herb in 'Wine", "heat": "the Decoction of the Herb", "process": "the Decoction of the Herb"}),
    R(JO + ", or applied outwardly, or both for some time together, for which purpose the Pills made with the Pouder of Ground Pine, and of Hermodactils with Venice Turpentine are very effectual",
      G, JI, rtype="compound", ingredients=PILLS, process="powder", form="other",
      ev={"process": "the Pouder of Ground Pine", "form": "the Pills made with the Pouder"}),
    R("These Pills also are special good for those that have the Dropsie, to be continued for some time.", G, "those that have the Dropsie",
      rtype="compound", ingredients=PILLS, process="powder", form="other",
      ev={"process": "the Pouder of Ground Pine", "form": "These Pills also are special good"}),
    R("The same is a special good help for the Jaundice, and for griping pains in the Joynts, Belly, or inward parts; It helpeth also all Diseases of the Brain proceeding of cold and Flegmatick Humors and Distillations, as also for the Falling-sickness. It is an espcial Remedy for the Poyson of the Aconites of all sorts, and other poisonful Herbs, as also against the stinking of any Venemous Creature. It is a good Remedy for a cold Cough, especially in the beginning.",
      G, "the Jaundice, and for griping pains in the Joynts, Belly, or inward parts; It helpeth also all Diseases of the Brain proceeding of cold and Flegmatick Humors and Distillations, as also for the Falling-sickness. It is an espcial Remedy for the Poyson of the Aconites of all sorts, and other poisonful Herbs, as also against the stinking of any Venemous Creature. It is a good Remedy for a cold Cough"),
    R("For all this purposes aforesaid, the Herb being tunned up in new Drink and drunk is almost as effectual", G, "all this purposes aforesaid",
      solvent=("other",), form="drink", ev={"solvent": "tunned up in new Drink", "form": "in new Drink and drunk"}),
    R("The Distilled Water of the Herb hath the same effects, but more weakly.", G, "hath the same effects", solvent=("water",), heat="boiled",
      process="distillation",
      ev={"solvent": "The Distilled Water of the Herb", "heat": "The Distilled Water", "process": "The Distilled Water"}),
    R("The Conserve of the Flowers doth the like, which Mathiolus much commendeth against the Palsey.", G, "doth the like, which Mathiolus much commendeth against the Palsey",
      part="flower", process="other", form="other",
      ev={"part": "The Conserve of the Flowers", "process": "The Conserve of the Flowers", "form": "The Conserve of the Flowers"}),
    R(GH, G, GHI, fod="fresh", heat="cold", form="poultice", filt="not_applicable",
      ev={"freshOrDried": "The green Herb", "heat": "The green Herb or the Decoction thereof being applied", "form": "The green Herb or the Decoction thereof being applied",
          "filtered": "The green Herb or the Decoction thereof being applied"}),
    R(GH, G, GHI, heat="boiled", process="decoction", ev={"heat": "the Decoction thereof", "process": "the Decoction thereof being applied"}),
    R(GU, G, GUI, fod="fresh", heat="cold", form="poultice", filt="not_applicable",
      ev={"freshOrDried": "The green Herb also applied", "heat": "The green Herb also applied", "form": "The green Herb also applied",
          "filtered": "The green Herb also applied"}),
    R(GU, G, GUI, part="juice", solvent=("honey",), heat="cold",
      ev={"part": "the Juyce thereof", "solvent": "the Juyce thereof with some Honey", "heat": "the Juyce thereof with some Honey"}),
]
M = "Meadow-sweet"
AG = "It is said to alter and take away the fits of Quartan Agues, and to make a merry heart, for which purpose some use the Flowers, and some the Leavs"
P[f"culpeper-1652:herbal:{MS_}:008"] = [
    R("It is used to stay all manner of Bleedings, Fluxes, Vomitings, and Womens Courses, and also their Whites", M,
      "stay all manner of Bleedings, Fluxes, Vomitings, and Womens Courses, and also their Whites", heading=True),
    R(AG, M, "alter and take away the fits of Quartan Agues, and to make a merry heart", heading=True, part="flower",
      ev={"part": "some use the Flowers"}),
    R(AG, M, "alter and take away the fits of Quartan Agues, and to make a merry heart", heading=True, part="leaf",
      ev={"part": "and some the Leavs"}),
    R("It helpeth speedily those that are troubled with the Chollick, being boyled in Wine", M, "those that are troubled with the Chollick", heading=True,
      solvent=("wine",), heat="boiled", process="decoction",
      ev={"solvent": "being boyled in Wine", "heat": "being boyled in Wine", "process": "being boyled in Wine"}),
    R("being boyled in Wine; and with a little Honey taken warm, it openeth the Belly", M, "it openeth the Belly", heading=True, solvent=("wine", "honey"),
      heat="boiled", heatText="taken warm", process="decoction", form="drink",
      ev={"solvent": ["being boyled in Wine", "with a little Honey"], "heat": "being boyled in Wine", "process": "being boyled in Wine",
          "form": "with a little Honey taken warm"}),
    R("but boyled in red Wine and drunk it stayeth the Flux of the Belly", M, "stayeth the Flux of the Belly", heading=True, solvent=("wine",),
      heat="boiled", process="decoction", form="drink",
      ev={"solvent": "boyled in red Wine", "heat": "boyled in red Wine", "process": "boyled in red Wine and drunk", "form": "boyled in red Wine and drunk"}),
    R("Being outwardly applied, it healeth old Ulcers that are Cankrous or eaten, or hollow and Fistulous, for which it is by many much commended, as also for the Sores in the Mouth or secret parts",
      M, "old Ulcers that are Cankrous or eaten, or hollow and Fistulous, for which it is by many much commended, as also for the Sores in the Mouth or secret parts",
      heading=True),
]
P[f"culpeper-1652:herbal:{MS_}:009"] = [
    R("The water thereof helpeth the heat and Inflamation in the Eyes.", M, "the heat and Inflamation in the Eyes", heading=True, solvent=("water",),
      ev={"solvent": "The water thereof"}),
]   # leaves raising blisters: an effect reported from Tragus, not a use
print(write("approved", 8, P))
