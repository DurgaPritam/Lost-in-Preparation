from build_batch import R, write
P = {}
for pid in ("hops:001", "hops:002", "hops:003", "hops:004", "hops:006", "liquorice:001", "liquorice:002"):
    P["culpeper-1850:herbal:" + pid] = []   # intro / description / place / time / astrology
Q5 = "outwardly, an oil ointment, or plaister of it, is most admirable for the gout, to cool the veneral heat of the reins in the French pox; to stop the toothache, being applied to the aching side: to allay all inflammations, and to help the diseases before premised"
I5 = "the gout, to cool the veneral heat of the reins in the French pox; to stop the toothache, being applied to the aching side: to allay all inflammations, and to help the diseases before premised"
P["culpeper-1850:herbal:henbane:005"] = [
    R(Q5, "HENBANE", I5, heading=True, solvent=("oil",), form="ointment", filt="not_applicable",
      ev={"solvent": "an oil ointment", "form": "an oil ointment", "filtered": "outwardly, an oil ointment"}),
    R(Q5, "HENBANE", I5, heading=True, form="plaster", filt="not_applicable", ev={"form": "or plaister of it", "filtered": "or plaister of it"}),
]
HO = "Hops"
P["culpeper-1850:herbal:hops:005"] = [
    R("This, in physical operations, is to open obstructions of the liver and spleen, to cleanse the blood, to loosen the belly, to cleanse the reins from gravel, and provoke urine.",
      HO, "to open obstructions of the liver and spleen, to cleanse the blood, to loosen the belly, to cleanse the reins from gravel, and provoke urine"),
    R("The decoction of the tops of Hops, as well of the tame as the wild, works the same effects.", HO, "works the same effects", part="other", heat="boiled",
      process="decoction", ev={"part": "the tops of Hops", "heat": "The decoction of the tops of Hops", "process": "The decoction of the tops of Hops"}),
    R("In cleansing the blood they help to cure the French diseases, and all manner of scabs, itch, and other breakings-out of the body; as also all tetters, ringworms, and spreading sores, the morphew and all discolouring of the skin.",
      HO, "the French diseases, and all manner of scabs, itch, and other breakings-out of the body; as also all tetters, ringworms, and spreading sores, the morphew and all discolouring of the skin"),
    R("The decoction of the flowers and hops, do help to expel poison that any one hath drank.", HO, "expel poison that any one hath drank", part="other",
      heat="boiled", process="decoction",
      ev={"part": "the flowers and hops", "heat": "The decoction of the flowers", "process": "The decoction of the flowers"}),
    R("Half a dram of the seed in powder taken in drink, kills worms in the body, brings down women’s courses, and expels urine.", HO,
      "kills worms in the body, brings down women’s courses, and expels urine", part="seed", heat="cold", process="powder", form="drink", filt="no",
      ev={"part": "the seed in powder", "heat": "the seed in powder", "process": "the seed in powder", "form": "taken in drink",
          "filtered": "the seed in powder taken in drink"}),
    R("A syrup made of the juice and sugar, cures the yellow jaundice, eases the head-ache that comes of heat, and tempers the heat of the liver and stomach, and is profitably given in long and hot agues that rise in choler and blood.",
      HO, "the yellow jaundice, eases the head-ache that comes of heat, and tempers the heat of the liver and stomach, and is profitably given in long and hot agues that rise in choler and blood",
      rtype="compound", ingredients=[(HO, "juice", "principal", "plant"), ("sugar", "unknown", "co_ingredient", "other")], part="juice", process="other",
      ev={"part": "made of the juice", "process": "A syrup made of the juice and sugar"}),
]
L = "Liquorice"
P["culpeper-1850:herbal:liquorice:003"] = [
    R("Liquorice boiled in fair water, with some Maiden-hair and figs, makes a good drink for those that have a dry cough or hoarseness, wheezing or shortness of breath, and for all the griefs of the breast and lungs, phthisic or consumptions caused by the distillation of salt humours on them. It is also good in all pains of the reins, the stranguary, and heat of urine",
      L, "those that have a dry cough or hoarseness, wheezing or shortness of breath, and for all the griefs of the breast and lungs, phthisic or consumptions caused by the distillation of salt humours on them. It is also good in all pains of the reins, the stranguary, and heat of urine",
      rtype="compound", ingredients=[(L, "unknown", "principal", "plant"), ("Maiden-hair", "unknown", "co_ingredient", "plant"), ("figs", "fruit", "co_ingredient", "plant")],
      solvent=("water",), heat="boiled", process="decoction", form="drink",
      ev={"solvent": "boiled in fair water", "heat": "boiled in fair water", "process": "boiled in fair water", "form": "makes a good drink"}),
    R("The fine powder of Liquorice blown through a quill into the eyes that have a pin and web (as they call it) or rheumatic distillations in them, doth cleanse and help them.",
      L, "the eyes that have a pin and web (as they call it) or rheumatic distillations in them, doth cleanse and help them", solvent=("none",), heat="cold",
      process="powder", form="other",
      ev={"solvent": "blown through a quill into the eyes", "heat": "The fine powder of Liquorice", "process": "The fine powder of Liquorice",
          "form": "blown through a quill into the eyes"}),
    R("The juice of Liquorice is as effectual in all the diseases of the breast and lungs, the reins and bladder, as the decoction.", L,
      "all the diseases of the breast and lungs, the reins and bladder", part="juice", ev={"part": "The juice of Liquorice"}),
    R("The juice distilled in Rose-water, with some Gum Tragacanth, is a fine licking medicine for hoarseness, wheezing, &c.", L, "hoarseness, wheezing, &c.",
      rtype="compound", ingredients=[(L, "juice", "principal", "plant"), ("Gum Tragacanth", "resin", "co_ingredient", "plant")], part="juice",
      solvent=("other",), heat="boiled", process="distillation", form="other",
      ev={"part": "The juice distilled in Rose-water", "solvent": "distilled in Rose-water", "heat": "The juice distilled", "process": "The juice distilled",
          "form": "a fine licking medicine"}),
]
print(write("approved", 16, P))
