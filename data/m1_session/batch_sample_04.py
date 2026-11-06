from build_batch import R, write
P = {}
P["pliny-nh:b20:c003:001"] = []   # keeping and testing elaterium; no health indication
RA = "Radishes"
P["pliny-nh:b20:c013:003"] = [
    R("Radishes are good, too, for curing ulcerations of the intestines and suppurations of the thoracic organs, if eaten with honey", RA,
      "ulcerations of the intestines and suppurations of the thoracic organs", solvent=("honey",), form="other",
      ev={"solvent": "eaten with honey", "form": "if eaten with honey"}),
    R("they should be boiled in earth and water; a decoction which, according to them, promotes the menstrual discharge", RA,
      "promotes the menstrual discharge", rtype="compound", ingredients=[(RA, "unknown", "principal", "plant"), ("earth", "unknown", "co_ingredient", "mineral")],
      solvent=("water",), heat="boiled", process="decoction",
      ev={"solvent": "boiled in earth and water", "heat": "boiled in earth and water", "process": "a decoction"}),
    R("Taken with vinegar or honey, radishes expel worms from the intestines", RA, "expel worms from the intestines", solvent=("vinegar", "honey"),
      ev={"solvent": "Taken with vinegar or honey"}),
    R("a decoction of them boiled down to one-third, taken in wine, is good for intestinal hernia", RA, "intestinal hernia", solvent=("wine",),
      heat="boiled", dur="boiled down to one-third", process="decoction", form="drink",
      ev={"solvent": "taken in wine", "heat": "boiled down to one-third", "process": "a decoction of them", "form": "taken in wine"}),
    R("Medius recommends them to be given boiled to persons troubled with spitting of blood, and to women who are suckling, for the purpose of increasing the milk",
      RA, "persons troubled with spitting of blood, and to women who are suckling, for the purpose of increasing the milk", heat="boiled",
      ev={"heat": "given boiled"}),
    R("Hippocrates recommends females whose hair falls off, to rub the head with radishes", RA, "females whose hair falls off", form="other",
      ev={"form": "to rub the head with radishes"}),
    R("for pains of the uterus, they should be applied to the navel", RA, "pains of the uterus", filt="not_applicable", form="poultice",
      ev={"filtered": "applied to the navel", "form": "applied to the navel"}),
]
SY = "SCOLYMOS"
P["pliny-nh:b20:c099:002"] = [
    R("This plant, gathered before it blossoms, and beaten up and subjected to pressure, produces a juice, which, applied to the head, makes the hair grow again when it has fallen off through alopecy",
      SY, "makes the hair grow again when it has fallen off through alopecy", heading=True, part="juice", heat="cold", process="expression", form="other",
      ev={"part": "produces a juice", "heat": "beaten up and subjected to pressure", "process": "subjected to pressure, produces a juice",
          "form": "applied to the head"}),
    R("It strengthens the stomach also, and if we are to believe what is said, has some influence upon the womb in promoting the conception of male offspring",
      SY, "strengthens the stomach also, and if we are to believe what is said, has some influence upon the womb in promoting the conception of male offspring",
      heading=True),
    R("The thin juice, like mastich, which exudes from these plants, imparts sweetness to the breath", SY, "imparts sweetness to the breath", heading=True,
      part="resin", ev={"part": "The thin juice, like mastich, which exudes from these plants"}),
]
P["pliny-nh:b21:c018:001"] = []   # the nature of odours; no use
P["pliny-nh:b21:c047:001"] = []   # beehives
P["pliny-nh:b22:c056:001"] = []   # remarks against compound medicines
EL = "elelisphacos"
P["pliny-nh:b22:c071:001"] = [
    R("This plant acts as an emmenagogue and a diuretic: and it affords a remedy for wounds inflicted by the sting-ray", EL,
      "acts as an emmenagogue and a diuretic: and it affords a remedy for wounds inflicted by the sting-ray"),
    R("It is taken in drink with wormwood for dysentery", EL, "dysentery", rtype="compound",
      ingredients=[(EL, "unknown", "principal", "plant"), ("wormwood", "unknown", "co_ingredient", "plant")], form="drink",
      ev={"form": "taken in drink"}),
    R("employed with wine it accelerates the catamenia when retarded", EL, "accelerates the catamenia when retarded", solvent=("wine",),
      ev={"solvent": "employed with wine"}),
    R("a decoction of it having the effect of arresting them when in excess", EL, "arresting them when in excess", heat="boiled", process="decoction",
      ev={"heat": "a decoction of it", "process": "a decoction of it"}),
    R("the plant, applied by itself, stanches the blood of wounds", EL, "stanches the blood of wounds", solvent=("none",), filt="not_applicable",
      form="poultice", ev={"solvent": "applied by itself", "filtered": "applied by itself", "form": "the plant, applied by itself"}),
    R("It is a cure, too, for the stings of serpents", EL, "the stings of serpents"),
    R("a decoction of it in wine allays prurigo of the testes", EL, "allays prurigo of the testes", solvent=("wine",), heat="boiled", process="decoction",
      ev={"solvent": "a decoction of it in wine", "heat": "a decoction of it in wine", "process": "a decoction of it in wine"}),
]
P["pliny-nh:b23:c057:001"] = [
    R("They have an astringent effect upon the stomach and bowels, provided they are taken in moderation", "pomegranate",
      "an astringent effect upon the stomach and bowels"),
]   # the warnings against use in fevers and vomiting are contraindications, not uses
MT = "mulberry-trees"
P["pliny-nh:b23:c070:001"] = [
    R("This juice is an antidote to the venom of serpents, is good for dysentery, disperses inflamed tumours and all kinds of gatherings, heals wounds, and allays both head-ache and ear-ache",
      MT, "an antidote to the venom of serpents, is good for dysentery, disperses inflamed tumours and all kinds of gatherings, heals wounds, and allays both head-ache and ear-ache",
      part="juice", process="other", ev={"part": "This juice", "process": "if the outer bark is peeled off, they emit a great abundance of juice"}),
    R("it is taken in drink for affections of the spleen", MT, "affections of the spleen", part="juice", process="other", form="drink",
      ev={"part": "This juice", "process": "if the outer bark is peeled off, they emit a great abundance of juice", "form": "taken in drink"}),
    R("is used as a liniment for the same purpose, as also for fits of shivering", MT, "fits of shivering", part="juice", process="other", form="ointment",
      filt="not_applicable", ev={"part": "This juice", "process": "if the outer bark is peeled off, they emit a great abundance of juice",
                                 "form": "used as a liniment", "filtered": "used as a liniment"}),
]
P["pliny-nh:b24:c007:001"] = [
    R("The round excrescences which grow on the robur * * * and mixed with bear’s grease, are remedial in cases of loss of the hair by alopecy", "robur",
      "loss of the hair by alopecy", part="other", solvent=("other",), ev={"part": "The round excrescences", "solvent": "mixed with bear’s grease"}),
]
print(write("sample", 4, P))
