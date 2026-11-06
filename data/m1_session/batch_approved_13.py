from build_batch import R, write
P = {}
for pid in ("celandine:001", "celandine:002", "celandine:003", "celandine:005", "celandine:006", "celandine:007", "celandine:008"):
    P["culpeper-1850:herbal:" + pid] = []   # description / place / time / argument / name origin
P["culpeper-1850:herbal:carraway:007"] = [
    R("Carraway comfits, once only dipped in sugar, and half a spoonful of them eaten in the morning fasting, and as many after each meal, is a most admirable remedy, for those that are troubled with wind.",
      "Carraway", "those that are troubled with wind", rtype="compound",
      ingredients=[("Carraway", "unknown", "principal", "plant"), ("sugar", "unknown", "co_ingredient", "other")], process="other", form="other",
      ev={"process": "Carraway comfits, once only dipped in sugar", "form": "half a spoonful of them eaten"}),
]
CE = "CELANDINE"
TG = "The juice or decoction of the herb gargled between the teeth that ach, eases the pain"
P["culpeper-1850:herbal:celandine:004"] = [
    R("then may you make into an oil or ointment, which you please, to anoint your sore eyes with", CE, "sore eyes", heading=True, solvent=("oil",),
      form="ointment", filt="not_applicable",
      ev={"solvent": "make into an oil or ointment", "form": "to anoint your sore eyes", "filtered": "make into an oil or ointment"}),
    R("The herb or root boiled in white Wine and drank, a few Anniseeds being boiled therewith, opens obstructions of the liver and gall, helps the yellow jaundice; and often using it, helps the dropsy and the itch, and those who have old sores in their legs, or other parts of the body.",
      CE, "opens obstructions of the liver and gall, helps the yellow jaundice; and often using it, helps the dropsy and the itch, and those who have old sores in their legs, or other parts of the body",
      heading=True, rtype="compound", ingredients=[(CE, "unknown", "principal", "plant"), ("Anniseeds", "seed", "co_ingredient", "plant")],
      solvent=("wine",), heat="boiled", process="decoction", form="drink",
      ev={"solvent": "boiled in white Wine", "heat": "boiled in white Wine", "process": "boiled in white Wine and drank", "form": "boiled in white Wine and drank",
          "recipeType": "a few Anniseeds being boiled therewith"}),
    R("The juice thereof taken fasting, is held to be of singularly good use against the pestilence.", CE, "the pestilence", heading=True, part="juice",
      solvent=("none",), heat="cold", form="drink",
      ev={"part": "The juice thereof", "solvent": "The juice thereof taken fasting", "heat": "The juice thereof taken fasting", "form": "The juice thereof taken fasting"}),
    R("The distilled water, with a little sugar and a little good treacle mixed therewith (the party upon the taking being laid down to sweat a little) has the same effect.",
      CE, "has the same effect", heading=True, rtype="compound",
      ingredients=[(CE, "unknown", "principal", "plant"), ("sugar", "unknown", "co_ingredient", "other"), ("treacle", "unknown", "co_ingredient", "other")],
      solvent=("water",), heat="boiled", process="distillation",
      ev={"solvent": "The distilled water", "heat": "The distilled water", "process": "The distilled water"}),
    R("The juice dropped into the eyes, cleanses them from films and cloudiness which darken the sight, but it is best to allay the sharpness of the juice with a little breast milk.",
      CE, "cleanses them from films and cloudiness which darken the sight", heading=True, part="juice", solvent=("other",), heat="cold", form="other",
      ev={"part": "The juice dropped into the eyes", "solvent": "allay the sharpness of the juice with a little breast milk", "heat": "The juice dropped into the eyes",
          "form": "The juice dropped into the eyes"}),
    R("It is good in all old filthy corroding creeping ulcers wheresoever, to stay their malignity of fretting and running, and to cause them to heal more speedily",
      CE, "all old filthy corroding creeping ulcers wheresoever, to stay their malignity of fretting and running, and to cause them to heal more speedily", heading=True),
    R("The juice often applied to tetters, ring-worms, or other such like spreading cankers, will quickly heal them, and rubbed often upon warts, will take them away.",
      CE, "tetters, ring-worms, or other such like spreading cankers, will quickly heal them, and rubbed often upon warts, will take them away", heading=True,
      part="juice", heat="cold", form="other",
      ev={"part": "The juice often applied", "heat": "The juice often applied", "form": "The juice often applied"}),
    R("The herb with the roots bruised and bathed with oil of camomile, and applied to the navel, takes away the griping pains of the belly and bowels, and all the pains of the mother; and applied to women’s breasts stays the overmuch flowing of the courses.",
      CE, "takes away the griping pains of the belly and bowels, and all the pains of the mother; and applied to women’s breasts stays the overmuch flowing of the courses",
      heading=True, part="other", solvent=("oil",), process="other", form="poultice", filt="not_applicable",
      ev={"part": "The herb with the roots", "solvent": "bathed with oil of camomile", "process": "bruised and bathed with oil of camomile",
          "form": "applied to the navel", "filtered": "bruised and bathed with oil of camomile, and applied"}),
    R(TG, CE, "the teeth that ach, eases the pain", heading=True, part="juice", heat="cold", form="gargle",
      ev={"part": "The juice or decoction", "heat": "The juice or decoction", "form": "gargled between the teeth"}),
    R(TG, CE, "the teeth that ach, eases the pain", heading=True, heat="boiled", process="decoction", form="gargle",
      ev={"heat": "decoction of the herb", "process": "decoction of the herb", "form": "gargled between the teeth"}),
    R("the powder of the dried root laid upon any aching, hollow or loose tooth, will cause it to fall out", CE,
      "any aching, hollow or loose tooth, will cause it to fall out", heading=True, part="root", fod="dried", solvent=("none",), heat="cold", process="powder",
      ev={"part": "the powder of the dried root", "freshOrDried": "the dried root", "solvent": "laid upon any aching", "heat": "the powder of the dried root",
          "process": "the powder of the dried root"}),
    R("The juice mixed with some powder of brimstone is not only good against the itch, but takes away all discolourings of the skin whatsoever", CE,
      "the itch, but takes away all discolourings of the skin whatsoever", heading=True, rtype="compound",
      ingredients=[(CE, "juice", "principal", "plant"), ("brimstone", "unknown", "co_ingredient", "mineral")], part="juice", heat="cold",
      ev={"part": "The juice mixed with some powder of brimstone", "heat": "The juice mixed with some powder of brimstone"}),
]
P["culpeper-1850:herbal:celandine:009"] = [
    R("the herb, being gathered as I shewed before, and the elements draw apart from it by art of the alchymist, and after they are drawn apart rectified, the earthly quality, still in rectifying them, added to the Terra damnata (as Alchymists call it) or Terra Sacratisima (as some philosophers call it) the elements so rectified are sufficient for the cure of all diseases",
      CE, "the cure of all diseases", heading=True, process="other", ev={"process": "the elements draw apart from it by art of the alchymist"}),
]
print(write("approved", 13, P))
