from build_batch import R, write
P = {}
for pid in ("henbane:007", "henbane:011", "henbane:012", "henbane:013", "henbane:014", "hops:001", "hops:002", "hops:004"):
    P["culpeper-1652:herbal:" + pid] = []   # time / astrology / description / place
H = "Henbane"
SW = ("all manner of Swellings of the Cods or Womens Breasts, or els where, if they be boyled in Wine, and either applied themselves or the "
      "Fomentation warm; it also asswageth the pain of the Gout, the Sciatica and all other pains in the Joynts which arise from an hot caus")
QSW = "are good to asswage " + SW
ANT = "Fennel Seed, Nettle Seed, the Seed of Cresses, Mustard, or Radish, as also Onions, or Garlick taken in wine, do all help to free them from danger, and restore them to their due temper again"
ANT_IND = "free them from danger, and restore them to their due temper again"
def antidote(name, part, wine):
    return R(ANT, name, ANT_IND, part=part, solvent=("wine",) if wine else ("unknown",),
             ev={**({"part": name} if part != "unknown" else {}), **({"solvent": "Garlick taken in wine", "form": "Garlick taken in wine"} if wine else {})},
             form="drink" if wine else "unknown")
P["culpeper-1652:herbal:henbane:009"] = [
    R("The Leavs of Henbane do cool all hot Inflamations in the Eyes or any other part of the Body", H,
      "cool all hot Inflamations in the Eyes or any other part of the Body", part="leaf", ev={"part": "The Leavs of Henbane"}),
    R(QSW, H, SW, part="leaf", solvent=("wine",), heat="boiled", process="decoction", form="poultice", filt="not_applicable",
      ev={"part": "The Leavs of Henbane", "solvent": "boyled in Wine", "heat": "boyled in Wine", "process": "if they be boyled in Wine",
          "form": "applied themselves", "filtered": "applied themselves"}),
    R(QSW, H, SW, part="leaf", solvent=("wine",), heat="boiled", heatText="the Fomentation warm", process="decoction", form="other",
      ev={"part": "The Leavs of Henbane", "solvent": "boyled in Wine", "heat": "boyled in Wine", "process": "if they be boyled in Wine",
          "form": "the Fomentation warm"}),
    R("And applied with Vinegar to the Forehead and Temples, helpeth the Headach and want of sleep in hot Feavers", H,
      "the Headach and want of sleep in hot Feavers", part="leaf", solvent=("vinegar",), form="poultice", filt="not_applicable",
      ev={"part": "The Leavs of Henbane", "solvent": "applied with Vinegar", "form": "applied with Vinegar to the Forehead and Temples",
          "filtered": "applied with Vinegar to the Forehead and Temples"}),
    R("The Juyce of the Herb or Seed, or the Oyl drawn from the Seed doth the like", H, "doth the like", part="juice", heat="cold",
      ev={"part": "The Juyce of the Herb or Seed", "heat": "The Juyce of the Herb or Seed"}),
    R("The Juyce of the Herb or Seed, or the Oyl drawn from the Seed doth the like", H, "doth the like", part="seed", process="other",
      ev={"part": "the Oyl drawn from the Seed", "process": "the Oyl drawn from the Seed"}),
    R("The Oyl of the Seed is helpful for the Deafness, Nois, and Worms in the Ears, being dropped therein", H, "the Deafness, Nois, and Worms in the Ears",
      part="seed", process="other", form="other",
      ev={"part": "The Oyl of the Seed", "process": "The Oyl of the Seed", "form": "being dropped therein"}),
    R("the Juyce of the Herb, or Root doth also the same", H, "doth also the same", part="juice", heat="cold",
      ev={"part": "the Juyce of the Herb, or Root", "heat": "the Juyce of the Herb, or Root"}),
    R("The Decoction of the Herb, or Seed, or both, killeth Lice in Man and Beast", H, "killeth Lice in Man and Beast", heat="boiled", process="decoction",
      ev={"heat": "The Decoction of the Herb", "process": "The Decoction of the Herb"}),
    R("The fume of the dried Herb Stalks and Seed burned, quickly healeth Swellings, Chilblains,, or Kibes in the Hands or Feet, by holding them in the fume thereof",
      H, "Swellings, Chilblains,, or Kibes in the Hands or Feet", part="other", fod="dried", process="other", form="inhalation", filt="not_applicable",
      ev={"part": "the dried Herb Stalks and Seed", "freshOrDried": "the dried Herb Stalks", "process": "Stalks and Seed burned",
          "form": "The fume of the dried Herb", "filtered": "by holding them in the fume thereof"}),
    R("The Remedy to help those that have taken Henbane is to drink Goats Milk, Honyed Water or Pine Kernels, with Sweet Wine", "Pine Kernels",
      "help those that have taken Henbane", part="seed", solvent=("wine",), form="drink",
      ev={"part": "Pine Kernels", "solvent": "with Sweet Wine", "form": "is to drink"}),
    antidote("Fennel Seed", "seed", False), antidote("Nettle Seed", "seed", False), antidote("the Seed of Cresses", "seed", False),
    antidote("Mustard", "unknown", False), antidote("Radish", "unknown", False),
    R(ANT, "Onions", ANT_IND, solvent=("wine",), form="drink", ev={"solvent": "Onions, or Garlick taken in wine", "form": "Onions, or Garlick taken in wine"}),
    R(ANT, "Garlick", ANT_IND, solvent=("wine",), form="drink", ev={"solvent": "Garlick taken in wine", "form": "Garlick taken in wine"}),
]
Q10 = "outwardly, an Oyl, Oyntment, or Plaister of it, is most admirable for the Gout, to cool the Venerial heat of the Reins in the French Pox, to stop the Toothach being applied to the aching side, to allay all Inflamations, and to help the Diseases before premised"
I10 = "the Gout, to cool the Venerial heat of the Reins in the French Pox, to stop the Toothach being applied to the aching side, to allay all Inflamations, and to help the Diseases before premised"
P["culpeper-1652:herbal:henbane:010"] = [
    R(Q10, H, I10, heading=True, solvent=("oil",), form="ointment", filt="not_applicable",
      ev={"solvent": "an Oyl, Oyntment", "form": "an Oyl, Oyntment", "filtered": "outwardly, an Oyl, Oyntment"}),
    R(Q10, H, I10, heading=True, form="plaster", filt="not_applicable", ev={"form": "or Plaister of it", "filtered": "or Plaister of it"}),
]   # "this Herb must never be taken inwardly": a warning, recorded in the text, not a use
print(write("approved", 6, P))
