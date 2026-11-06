from build_batch import R, write
P = {}
P["pliny-nh:b25:c050:001"] = []   # description; the swallow restoring its nestlings' sight is a legend of discovery, not a remedy given
P["pliny-nh:b27:c028:001"] = []   # varieties; wormwood draught as a race prize, not a health use
P["pliny-nh:b27:c028:005"] = []   # ink against mice; hair dye: no health use
CP = "CHAMÆPITYS"
AP = "and are useful as an application, mixed with dates or quinces, for maladies of the liver"
P["pliny-nh:b24:c020:002"] = [
    R("These plants are good for stings inflicted by scorpions", CP, "stings inflicted by scorpions", heading=True),
    R(AP, CP, "maladies of the liver", heading=True, rtype="compound",
      ingredients=[(CP, "unknown", "principal", "plant"), ("dates", "fruit", "co_ingredient", "plant")], form="poultice", filt="not_applicable",
      ev={"form": "useful as an application", "filtered": "useful as an application"}),
    R(AP, CP, "maladies of the liver", heading=True, rtype="compound",
      ingredients=[(CP, "unknown", "principal", "plant"), ("quinces", "fruit", "co_ingredient", "plant")], form="poultice", filt="not_applicable",
      ev={"form": "useful as an application", "filtered": "useful as an application"}),
    R("a decoction of them with barley-meal is used for the kidneys and the bladder", CP, "the kidneys and the bladder", heading=True, rtype="compound",
      ingredients=[(CP, "unknown", "principal", "plant"), ("barley-meal", "unknown", "co_ingredient", "plant")], heat="boiled", process="decoction",
      ev={"heat": "a decoction of them", "process": "a decoction of them"}),
    R("A decoction of them in water is used also for jaundice and for strangury.", CP, "jaundice and for strangury", heading=True, solvent=("water",),
      heat="boiled", process="decoction",
      ev={"solvent": "A decoction of them in water", "heat": "A decoction of them in water", "process": "A decoction of them in water"}),
    R("The kind last mentioned, in combination with honey, is good for wounds inflicted by serpents", CP, "wounds inflicted by serpents", heading=True,
      solvent=("honey",), ev={"solvent": "in combination with honey"}),
    R("a pessary is made of it, with honey, as a detergent for the uterus", CP, "a detergent for the uterus", heading=True, solvent=("honey",), form="other",
      ev={"solvent": "with honey", "form": "a pessary is made of it"}),
    R("Taken in drink it brings away coagulated blood", CP, "brings away coagulated blood", heading=True, form="drink", ev={"form": "Taken in drink"}),
    R("rubbed upon the body it acts as a sudorific", CP, "acts as a sudorific", heading=True),
    R("it is particularly useful also for the kidneys", CP, "the kidneys", heading=True),
    R("Pills of a purgative nature are made of it for dropsy, with figs.", CP, "dropsy", heading=True, rtype="compound",
      ingredients=[(CP, "unknown", "principal", "plant"), ("figs", "fruit", "co_ingredient", "plant")], form="other", ev={"form": "Pills of a purgative nature"}),
    R("Taken in wine, in doses of one victoriatus, it dispels lumbago, and cures coughs that are not of an inveterate description.", CP,
      "dispels lumbago, and cures coughs that are not of an inveterate description", heading=True, solvent=("wine",), form="drink",
      ev={"solvent": "Taken in wine", "form": "Taken in wine"}),
    R("A decoction of it in vinegar, taken in drink, will instantaneously bring away the dead fœtus, it is said.", CP, "bring away the dead fœtus", heading=True,
      solvent=("vinegar",), heat="boiled", process="decoction", form="drink",
      ev={"solvent": "A decoction of it in vinegar", "heat": "A decoction of it in vinegar", "process": "A decoction of it in vinegar", "form": "taken in drink"}),
]
P["pliny-nh:b24:c116:001"] = [
    R("A chaplet made of this plant has the effect of relieving headache.", "philanthropos", "relieving headache", solvent=("none",), form="other",
      filt="not_applicable", ev={"solvent": "A chaplet made of this plant", "form": "A chaplet made of this plant", "filtered": "A chaplet made of this plant"}),
]
LC = "lappa canaria"
SW = "Taken out of the ground without the aid of iron, and thrown into their wash, or given to them in wine and milk, it cures diseases in swine"
P["pliny-nh:b24:c116:002"] = [
    R("As to the plant known as the “lappa canaria,” beaten up in wine with plantago and millefolium, it effects the cure of carcinomatous sores", LC,
      "carcinomatous sores", rtype="compound",
      ingredients=[(LC, "unknown", "principal", "plant"), ("plantago", "unknown", "co_ingredient", "plant"), ("millefolium", "unknown", "co_ingredient", "plant")],
      solvent=("wine",), process="other", ev={"solvent": "beaten up in wine", "process": "beaten up in wine"}),
    R(SW, LC, "diseases in swine", form="other", ev={"form": "thrown into their wash"}),
    R(SW, LC, "diseases in swine", solvent=("wine", "other"), form="drink", ev={"solvent": "given to them in wine and milk", "form": "given to them in wine and milk"}),
]
P["pliny-nh:b25:c050:002"] = [
    R("The juice is extracted while they are in flower, and is boiled gently in a copper vessel on hot ashes, with Attic honey, being esteemed a sovereign remedy for films upon the eyes",
      "chelidonia", "films upon the eyes", part="juice", solvent=("honey",), heat="boiled", heatText="boiled gently in a copper vessel on hot ashes",
      process="other",
      ev={"part": "The juice is extracted", "solvent": "with Attic honey", "heat": "boiled gently in a copper vessel on hot ashes",
          "process": "The juice is extracted while they are in flower"}),
]   # the eye-salves named after it: a form, no condition named
W = "wormwood"
DEC = ("the decoction, on the other hand, is wholesome in the highest degree, as it acts astringently upon the stomach, carries off bile, is a powerful "
       "diuretic, has a soothing effect upon the bowels, and assuages pains in the intestines")
DEV = {"part": "Six drachmæ of the leaves are boiled, with the branches", "solvent": "in three sextarii of rain water",
       "heat": "Six drachmæ of the leaves are boiled", "process": "A decoction of it in water", "form": "A decoction of it in water is also taken"}
P["pliny-nh:b27:c028:002"] = [
    R("This plant is very strengthening to the stomach, and hence it is that wines are flavoured with it", W, "very strengthening to the stomach", heading=True),
    R(DEC, W, "acts astringently upon the stomach, carries off bile, is a powerful diuretic, has a soothing effect upon the bowels, and assuages pains in the intestines",
      rtype="compound", ingredients=[(W, "other", "principal", "plant"), ("Salt", "unknown", "co_ingredient", "mineral")], part="other",
      solvent=("water",), heat="boiled", dur="a day and a night", process="decoction", form="drink", ev=DEV),
    R("With the addition of sile, Gallic nard, and a little vinegar, it dispels nausea and flatulency, and expels intestinal worms.", W,
      "dispels nausea and flatulency, and expels intestinal worms", rtype="compound",
      ingredients=[(W, "other", "principal", "plant"), ("sile", "unknown", "co_ingredient", "plant"), ("Gallic nard", "unknown", "co_ingredient", "plant")],
      part="other", solvent=("water", "vinegar"), heat="boiled", process="decoction",
      ev={"part": DEV["part"], "solvent": ["in three sextarii of rain water", "a little vinegar"], "heat": DEV["heat"], "process": DEV["process"]}),
    R("It removes qualmishness, promotes the digestion", W, "removes qualmishness, promotes the digestion", part="other", solvent=("water",), heat="boiled",
      process="decoction", ev={k: DEV[k] for k in ("part", "solvent", "heat", "process")}),
    R("with the addition of rue, pepper, and salt, disperses crudities of the stomach", W, "disperses crudities of the stomach", rtype="compound",
      ingredients=[(W, "other", "principal", "plant"), ("rue", "unknown", "co_ingredient", "plant"), ("pepper", "unknown", "co_ingredient", "plant"),
                   ("salt", "unknown", "co_ingredient", "mineral")],
      part="other", solvent=("water",), heat="boiled", process="decoction", ev={k: DEV[k] for k in ("part", "solvent", "heat", "process")}),
]   # the steeped 'dilution' names no indication; the extracted juice is called bad for head and stomach (a warning, not a use)
PUR = "The ancients were in the habit of giving wormwood as a purgative, the dose being six drachmæ of the seed with three of salt and one cyathus of honey, in one sextarius of sea water kept for some time"
SP = "for diseases of the spleen, with vinegar, pap, or figs"
P["pliny-nh:b27:c028:003"] = [
    R(PUR, W, "a purgative", rtype="compound", ingredients=[(W, "seed", "principal", "plant"), ("salt", "unknown", "co_ingredient", "mineral")], part="seed",
      solvent=("water", "honey"), ev={"part": "six drachmæ of the seed", "solvent": ["in one sextarius of sea water", "one cyathus of honey"]}),
    R(PUR + ". This preparation, however, is rendered more efficacious by doubling the proportion of salt; the seed, too, must be bruised with the greatest care, as there is considerable difficulty in pounding it. Some authorities have prescribed the dose above mentioned to be given in polenta, with the addition of pennyroyal",
      W, "a purgative", rtype="compound",
      ingredients=[(W, "seed", "principal", "plant"), ("polenta", "unknown", "co_ingredient", "other"), ("pennyroyal", "unknown", "co_ingredient", "plant")],
      part="seed", process="other", ev={"part": "six drachmæ of the seed", "process": "the seed, too, must be bruised"}),
    R(PUR + ". This preparation, however, is rendered more efficacious by doubling the proportion of salt; the seed, too, must be bruised with the greatest care, as there is considerable difficulty in pounding it. Some authorities have prescribed the dose above mentioned to be given in polenta, with the addition of pennyroyal; while others recommend the leaves to be given to children in a dried fig, to disguise their bitterness",
      W, "a purgative", rtype="compound", ingredients=[(W, "leaf", "principal", "plant"), ("dried fig", "fruit", "co_ingredient", "plant")], part="leaf",
      ev={"part": "recommend the leaves to be given to children"}),
    R("Taken with iris, wormwood acts as a detergent upon the thoracic organs", W, "acts as a detergent upon the thoracic organs", rtype="compound",
      ingredients=[(W, "unknown", "principal", "plant"), ("iris", "unknown", "co_ingredient", "plant")]),
    R("for jaundice it is used raw, with parsley or adiantum", W, "jaundice", rtype="compound",
      ingredients=[(W, "unknown", "principal", "plant"), ("parsley", "unknown", "co_ingredient", "plant")], heat="cold", ev={"heat": "it is used raw"}),
    R("for jaundice it is used raw, with parsley or adiantum", W, "jaundice", rtype="compound",
      ingredients=[(W, "unknown", "principal", "plant"), ("adiantum", "unknown", "co_ingredient", "plant")], heat="cold", ev={"heat": "it is used raw"}),
    R("In cases of flatulency, it is sipped every now and then, warmed in water", W, "flatulency", solvent=("water",), heat="warm", heatText="warmed in water",
      form="drink", ev={"solvent": "warmed in water", "heat": "warmed in water", "form": "it is sipped every now and then"}),
    R("for liver complaints it is taken with Gallic nard", W, "liver complaints", rtype="compound",
      ingredients=[(W, "unknown", "principal", "plant"), ("Gallic nard", "unknown", "co_ingredient", "plant")]),
    R(SP, W, "diseases of the spleen", solvent=("vinegar",), ev={"solvent": "with vinegar"}),
    R(SP, W, "diseases of the spleen", rtype="compound", ingredients=[(W, "unknown", "principal", "plant"), ("pap", "unknown", "co_ingredient", "other")]),
    R(SP, W, "diseases of the spleen", rtype="compound", ingredients=[(W, "unknown", "principal", "plant"), ("figs", "fruit", "co_ingredient", "plant")]),
    R("Taken in vinegar it neutralizes the bad effects of fungi and of viscus", W, "neutralizes the bad effects of fungi and of viscus", solvent=("vinegar",),
      ev={"solvent": "Taken in vinegar"}),
    R("in wine it is an antidote to the poison of hemlock, and to the bite of the shrew-mouse, and is curative of wounds inflicted by the sea-dragon and the scorpion",
      W, "an antidote to the poison of hemlock, and to the bite of the shrew-mouse, and is curative of wounds inflicted by the sea-dragon and the scorpion",
      solvent=("wine",), ev={"solvent": "in wine it is an antidote"}),
    R("It contributes also very greatly to the improvement of the sight", W, "the improvement of the sight"),
    R("is used as an external application, with raisin wine, for defluxions of the eyes", W, "defluxions of the eyes", solvent=("wine",),
      ev={"solvent": "with raisin wine"}),
    R("is used as an external application, with raisin wine, for defluxions of the eyes, and with honey, for bruises", W, "bruises", solvent=("honey",),
      ev={"solvent": "and with honey, for bruises"}),
]
GN = "Three or four sprigs of wormwood, with one root of Gallic nard, taken in six cyathi of water, act as a diuretic and as an emmenagogue"
EM = "indeed, if taken with honey, or employed as a pessary with wool, it has especial virtues as an emmenagogue"
PL = "In combination with Cyprian wax or figs, it is highly recommended as a plaster for the iliac regions"
P["pliny-nh:b27:c028:004"] = [
    R("The steam of a decoction of wormwood is curative of affections of the ears", W, "affections of the ears", heat="boiled", process="decoction",
      form="inhalation", filt="not_applicable",
      ev={"heat": "a decoction of wormwood", "process": "a decoction of wormwood", "form": "The steam of a decoction", "filtered": "The steam of a decoction"}),
    R("when they are attacked with running sores, a liniment of wormwood bruised with honey is applied", W, "running sores", solvent=("honey",), process="other",
      form="ointment", filt="not_applicable",
      ev={"solvent": "bruised with honey", "process": "wormwood bruised with honey", "form": "a liniment of wormwood", "filtered": "a liniment of wormwood"}),
    R(GN, W, "act as a diuretic and as an emmenagogue", rtype="compound",
      ingredients=[(W, "unknown", "principal", "plant"), ("Gallic nard", "root", "co_ingredient", "plant")], solvent=("water",), form="drink",
      ev={"solvent": "taken in six cyathi of water", "form": "taken in six cyathi of water"}),
    R(EM, W, "especial virtues as an emmenagogue", solvent=("honey",), ev={"solvent": "if taken with honey"}),
    R(EM, W, "especial virtues as an emmenagogue", rtype="compound",
      ingredients=[(W, "unknown", "principal", "plant"), ("wool", "unknown", "co_ingredient", "animal")], form="other",
      ev={"form": "employed as a pessary with wool"}),
    R("In combination with honey and nitre it is useful for quinzy", W, "quinzy", rtype="compound",
      ingredients=[(W, "unknown", "principal", "plant"), ("nitre", "unknown", "co_ingredient", "mineral")], solvent=("honey",),
      ev={"solvent": "In combination with honey and nitre"}),
    R("an infusion of it in water is good for epinyctis", W, "epinyctis", solvent=("water",), process="infusion",
      ev={"solvent": "an infusion of it in water", "process": "an infusion of it in water"}),
    R("A topical application is made of it for recent wounds, provided always they have not been touched with water: it is employed also for ulcers upon the head",
      W, "recent wounds, provided always they have not been touched with water: it is employed also for ulcers upon the head"),
    R(PL, W, "the iliac regions", rtype="compound", ingredients=[(W, "unknown", "principal", "plant"), ("Cyprian wax", "unknown", "co_ingredient", "other")],
      form="plaster", filt="not_applicable", ev={"form": "as a plaster for the iliac regions", "filtered": "as a plaster"}),
    R(PL, W, "the iliac regions", rtype="compound", ingredients=[(W, "unknown", "principal", "plant"), ("figs", "fruit", "co_ingredient", "plant")],
      form="plaster", filt="not_applicable", ev={"form": "as a plaster for the iliac regions", "filtered": "as a plaster"}),
    R("it is curative also of prurigo, but it must never be administered in fevers", W, "prurigo"),
    R("Taken in drink, it is a preventive of sea sickness", W, "a preventive of sea sickness", form="drink", ev={"form": "Taken in drink"}),
    R("worn attached to the body, beneath an apron, it arrests inguinal swellings", W, "arrests inguinal swellings", solvent=("none",), form="other",
      filt="not_applicable",
      ev={"solvent": "worn attached to the body", "form": "worn attached to the body, beneath an apron", "filtered": "worn attached to the body"}),
    R("The smell of it induces sleep", W, "induces sleep", form="inhalation", filt="not_applicable",
      ev={"form": "The smell of it induces sleep", "filtered": "The smell of it"}),
    R("The smell of it induces sleep, a similar effect being produced by placing it under the pillow unknown to the party", W, "induces sleep",
      solvent=("none",), form="other", filt="not_applicable",
      ev={"solvent": "placing it under the pillow", "form": "placing it under the pillow", "filtered": "placing it under the pillow"}),
]   # keeping worms from clothes and driving away gnats: not health uses
print(write("approved", 22, P))
