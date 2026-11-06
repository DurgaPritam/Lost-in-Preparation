from build_batch import R, write
P = {}
P["pliny-nh:b20:c076:003"] = []   # 'meconium' named, no indication
P["pliny-nh:b20:c076:004"] = []   # tests of the purity of opium
CO = "COLOCYNTHIS"
GD = "gourd"   # referent after "the cultivated gourd" is ambiguous (cultivated gourd or colocynthis): recorded under the text's word "gourd"
LV = "The leaves of it, bruised with fresh cypress-leaves, or the leaves alone, boiled in a vessel of potters’ clay and beaten up with goose-grease, and then applied to the part affected, are an excellent cure for wounds"
ER = "they are good, too, for erysipelas, whether it is the shavings of the rind or the seeds of the plant that are applied to the part affected"
P["pliny-nh:b20:c008:002"] = [
    R("The pulp of this fruit, taken with wormwood and salt, is a remedy for toothache", CO, "toothache", heading=True, rtype="compound",
      ingredients=[(CO, "fruit", "principal", "plant"), ("wormwood", "unknown", "co_ingredient", "plant"), ("salt", "unknown", "co_ingredient", "mineral")],
      part="fruit", ev={"part": "The pulp of this fruit"}),
    R("the juice of it, warmed with vinegar, has the effect of strengthening loose teeth", CO, "strengthening loose teeth", heading=True, part="juice",
      solvent=("vinegar",), heat="warm", heatText="warmed with vinegar",
      ev={"part": "the juice of it", "solvent": "warmed with vinegar", "heat": "warmed with vinegar"}),
    R("Rubbed in with oil, it removes pains of the spine, loins, and hips", CO, "pains of the spine, loins, and hips", heading=True, solvent=("oil",),
      form="ointment", filt="not_applicable", ev={"solvent": "Rubbed in with oil", "form": "Rubbed in with oil", "filtered": "Rubbed in with oil"}),
    R("the seeds of it, in even numbers, attached to the body in a linen cloth, will cure, it is said, the fevers to which the Greeks have given the name of “periodic.”",
      CO, "the fevers to which the Greeks have given the name of “periodic.”", heading=True, part="seed", solvent=("none",), form="other",
      filt="not_applicable",
      ev={"part": "the seeds of it", "solvent": "attached to the body in a linen cloth", "form": "attached to the body in a linen cloth",
          "filtered": "attached to the body in a linen cloth"}),
    R("The juice, too, of the cultivated gourd shred in pieces, applied warm, is good for ear-ache", "cultivated gourd", "ear-ache", part="juice",
      heat="warm", heatText="applied warm", ev={"part": "The juice, too, of the cultivated gourd", "heat": "applied warm"}),
    R("and the flesh of the inside, used without the seed, for corns on the feet and the suppurations known to the Greeks as “apostemata.”", "cultivated gourd",
      "corns on the feet and the suppurations known to the Greeks as “apostemata.”", part="fruit", ev={"part": "the flesh of the inside, used without the seed"}),
    R("When the pulp and seeds are boiled together, the decoction is good for strengthening loose teeth, and for preventing toothache", GD,
      "strengthening loose teeth, and for preventing toothache", part="other", heat="boiled", process="decoction",
      ev={"part": "the pulp and seeds", "heat": "the pulp and seeds are boiled together", "process": "the decoction is good"}),
    R("wine, too, boiled with this plant, is curative of defluxions of the eyes", GD, "defluxions of the eyes", solvent=("wine",), heat="boiled",
      process="decoction", ev={"solvent": "wine, too, boiled with this plant", "heat": "boiled with this plant", "process": "wine, too, boiled with this plant"}),
    R(LV, GD, "an excellent cure for wounds", rtype="compound",
      ingredients=[(GD, "leaf", "principal", "plant"), ("cypress-leaves", "leaf", "co_ingredient", "plant")], part="leaf", process="other", form="poultice",
      filt="not_applicable",
      ev={"part": "The leaves of it", "process": "bruised with fresh cypress-leaves", "form": "applied to the part affected", "filtered": "applied to the part affected"}),
    R(LV, GD, "an excellent cure for wounds", part="leaf", solvent=("other",), heat="boiled", process="other", form="poultice", filt="not_applicable",
      ev={"part": "the leaves alone", "solvent": "beaten up with goose-grease", "heat": "boiled in a vessel of potters’ clay",
          "process": "boiled in a vessel of potters’ clay and beaten up with goose-grease", "form": "applied to the part affected",
          "filtered": "applied to the part affected"}),
    R("Fresh shavings of the rind are used as a cooling application for gout, and burning pains in the head, in infants more particularly", GD,
      "gout, and burning pains in the head, in infants more particularly", part="other", fod="fresh", heat="cold", form="poultice", filt="not_applicable",
      ev={"part": "shavings of the rind", "freshOrDried": "Fresh shavings of the rind", "heat": "Fresh shavings of the rind",
          "form": "a cooling application", "filtered": "a cooling application"}),
    R(ER, GD, "erysipelas", part="other", form="poultice", filt="not_applicable",
      ev={"part": "the shavings of the rind", "form": "applied to the part affected", "filtered": "applied to the part affected"}),
    R(ER, GD, "erysipelas", part="seed", form="poultice", filt="not_applicable",
      ev={"part": "the seeds of the plant", "form": "applied to the part affected", "filtered": "applied to the part affected"}),
    R("The juice of the scrapings, employed as a liniment with rose-oil and vinegar, moderates the burning heats of fevers", GD,
      "moderates the burning heats of fevers", part="juice", solvent=("oil", "vinegar"), form="ointment", filt="not_applicable",
      ev={"part": "The juice of the scrapings", "solvent": ["with rose-oil", "rose-oil and vinegar"], "form": "employed as a liniment",
          "filtered": "employed as a liniment"}),
    R("the ashes of the dried fruit applied to burns are efficacious in a most remarkable degree", GD, "burns", part="fruit", fod="dried", process="other",
      form="other", ev={"part": "the dried fruit", "freshOrDried": "the dried fruit", "process": "the ashes of the dried fruit", "form": "applied to burns"}),
]
P["pliny-nh:b20:c008:003"] = [
    R("Chrysippus, the physician, condemned the use of the gourd as a food: it is generally agreed, however, that it is extremely good for the stomach, and for ulcerations of the intestines and of the bladder.",
      GD, "extremely good for the stomach, and for ulcerations of the intestines and of the bladder", form="other", ev={"form": "the use of the gourd as a food"}),
]
RA = "radishes"
SD = "Parched radish-seed, as well as radishes themselves, chewed, is useful for pains in the sides"
PH = "A decoction of the leaves, taken in drink, or else the juice of the plant taken in doses of two cyathi, is an excellent remedy for phthiriasis"
P["pliny-nh:b20:c013:001"] = [
    R("The cultivated radish, too, in addition to what we have already said of it, purges the stomach, attenuates the phlegm, acts as a diuretic, and detaches the bilious secretions.",
      "cultivated radish", "purges the stomach, attenuates the phlegm, acts as a diuretic, and detaches the bilious secretions"),
    R("A decoction of the rind of radishes in wine, taken in the morning in doses of three cyathi, has the effect of breaking and expelling calculi of the bladder.",
      RA, "breaking and expelling calculi of the bladder", part="other", solvent=("wine",), heat="boiled", process="decoction", form="drink",
      ev={"part": "the rind of radishes", "solvent": "the rind of radishes in wine", "heat": "A decoction of the rind", "process": "A decoction of the rind",
          "form": "taken in the morning in doses of three cyathi"}),
    R("A decoction, too, of this rind in vinegar and water, is employed as a liniment for the stings of serpents.", RA, "the stings of serpents", part="other",
      solvent=("vinegar", "water"), heat="boiled", process="decoction", form="ointment", filt="not_applicable",
      ev={"part": "this rind", "solvent": "in vinegar and water", "heat": "A decoction, too, of this rind", "process": "A decoction, too, of this rind",
          "form": "employed as a liniment", "filtered": "employed as a liniment"}),
    R("Taken fasting in the morning with honey, radishes are good for a cough.", RA, "a cough", solvent=("honey",), ev={"solvent": "with honey, radishes"}),
    R(SD, "radish-seed", "pains in the sides", part="seed", heat="warm", heatText="Parched", form="other",
      ev={"part": "Parched radish-seed", "heat": "Parched radish-seed", "form": "radishes themselves, chewed"}),
    R(SD, RA, "pains in the sides", form="other", ev={"form": "radishes themselves, chewed"}),
    R(PH, RA, "phthiriasis", part="leaf", heat="boiled", process="decoction", form="drink",
      ev={"part": "A decoction of the leaves", "heat": "A decoction of the leaves", "process": "A decoction of the leaves", "form": "taken in drink"}),
    R(PH, RA, "phthiriasis", part="juice", form="drink", ev={"part": "the juice of the plant", "form": "the juice of the plant taken in doses of two cyathi"}),
    R("Pounded radishes, too, are employed as a liniment for inflammations under the skin", RA, "inflammations under the skin", process="other",
      form="ointment", filt="not_applicable",
      ev={"process": "Pounded radishes", "form": "employed as a liniment", "filtered": "employed as a liniment"}),
    R("and the rind, mixed with honey, for bruises of recent date", RA, "bruises of recent date", part="other", solvent=("honey",),
      ev={"part": "the rind, mixed with honey", "solvent": "mixed with honey"}),
    R("Lethargic persons are recommended to eat them as hot as possible", RA, "Lethargic persons", heat="warm", heatText="as hot as possible", form="other",
      ev={"heat": "eat them as hot as possible", "form": "to eat them as hot as possible"}),
    R("the seed, parched and then pounded with honey, will give relief to asthmatic patients", RA, "asthmatic patients", part="seed", solvent=("honey",),
      heat="warm", heatText="parched", process="other",
      ev={"part": "the seed, parched", "solvent": "pounded with honey", "heat": "the seed, parched", "process": "parched and then pounded with honey"}),
]
RU = "after having rubbed the hands with radishes or radish-seed, we may handle those reptiles with impunity"
AP = "The two physicians of the name of Apollodorus, prescribe radishes to be given in cases of poisoning by mistletoe; but whereas Apollodorus of Citium recommends radish-seed pounded in water, Apollodorus of Tarentum speaks of the juice"
TV = "taken, too, with vinegar or mustard, they are good for dropsy and lethargy, as well as epilepsy and melancholy"
P["pliny-nh:b20:c013:002"] = [
    R("Radishes, too, are useful as a remedy for poisons, and are employed to counteract the effects of the sting of the cerastes and the scorpion", "Radishes",
      "a remedy for poisons, and are employed to counteract the effects of the sting of the cerastes and the scorpion"),
    R(RU, RA, "we may handle those reptiles with impunity", form="other", ev={"form": "rubbed the hands with radishes"}),
    R(RU, "radish-seed", "we may handle those reptiles with impunity", part="seed", form="other",
      ev={"part": "radish-seed", "form": "rubbed the hands with radishes or radish-seed"}),
    R("Radishes are useful, too, in cases of poisoning by fungi or henbane; and according to Nicander, they are salutary against the effects of bullock’s blood, when drunk.",
      "Radishes", "poisoning by fungi or henbane; and according to Nicander, they are salutary against the effects of bullock’s blood, when drunk"),
    R(AP, "radish-seed", "poisoning by mistletoe", part="seed", solvent=("water",), heat="cold", process="other",
      ev={"part": "radish-seed pounded in water", "solvent": "pounded in water", "heat": "radish-seed pounded in water", "process": "radish-seed pounded in water"}),
    R(AP, RA, "poisoning by mistletoe", part="juice", ev={"part": "speaks of the juice"}),
    R("Radishes diminish the volume of the spleen, and are beneficial for maladies of the liver and pains in the loins", "Radishes",
      "diminish the volume of the spleen, and are beneficial for maladies of the liver and pains in the loins"),
    R(TV, "Radishes", "dropsy and lethargy, as well as epilepsy and melancholy", solvent=("vinegar",), ev={"solvent": "taken, too, with vinegar"}),
    R(TV, "Radishes", "dropsy and lethargy, as well as epilepsy and melancholy", rtype="compound",
      ingredients=[("Radishes", "unknown", "principal", "plant"), ("mustard", "unknown", "co_ingredient", "plant")]),
    R("Praxagoras recommends that radishes should be given for the iliac passion, and Plistonicus for the cœliac disease.", RA,
      "the iliac passion, and Plistonicus for the cœliac disease"),
]   # killing a scorpion by placing a radish on it: not a health use
P["pliny-nh:b20:c013:004"] = [
    R("Radishes have the effect, too, of restoring the skin, when scarred, to its proper colour", "Radishes", "restoring the skin, when scarred, to its proper colour"),
    R("the seed, steeped in water, and applied topically, arrests the progress of ulcers known as phagedænic", "Radishes",
      "arrests the progress of ulcers known as phagedænic", part="seed", solvent=("water",), process="infusion",
      ev={"part": "the seed, steeped in water", "solvent": "steeped in water", "process": "steeped in water"}),
    R("Democritus regards them, taken with the food, as an aphrodisiac", "Radishes", "an aphrodisiac", form="other", ev={"form": "taken with the food"}),
    R("The leaves, but only those of the long radish, are said to have the effect of improving the eye-sight.", "long radish", "improving the eye-sight",
      part="leaf", ev={"part": "The leaves, but only those of the long radish"}),
]
P["pliny-nh:b20:c013:005"] = [
    R("When radishes, employed as a remedy, act too powerfully, it is recommended that hyssop should be given immediately", "hyssop",
      "When radishes, employed as a remedy, act too powerfully"),
    R("For dulness of hearing, too, radish-juice is injected into the ear.", "radish", "dulness of hearing", part="juice", form="other",
      ev={"part": "radish-juice", "form": "injected into the ear"}),
    R("To promote vomiting, it is extremely beneficial to eat radishes fasting.", RA, "To promote vomiting", form="other", ev={"form": "to eat radishes fasting"}),
]
PO = "poppy"
MI = "Mixed with woman’s milk, this seed is used as a liniment for gout: the leaves, too, are employed in a similar manner"
P["pliny-nh:b20:c076:001"] = [
    R("the calyx of the white poppy is pounded, and is taken in wine as a soporific", "white poppy", "a soporific", part="other", solvent=("wine",),
      process="powder", form="drink", filt="no",
      ev={"part": "the calyx of the white poppy", "solvent": "taken in wine", "process": "is pounded", "form": "taken in wine",
          "filtered": "is pounded, and is taken in wine"}),
    R("the seed of it is a cure, also, for elephantiasis", "white poppy", "elephantiasis", part="seed", ev={"part": "the seed of it"}),
    R("The black poppy acts as a soporific, by the juice which exudes from incisions made in the stalk", "black poppy", "acts as a soporific", part="juice",
      process="other", ev={"part": "the juice which exudes", "process": "incisions made in the stalk"}),
    R("Lozenges are also made of ground poppy-seed, which are taken in milk as a soporific.", PO, "a soporific", part="seed", solvent=("other",),
      process="powder", form="other",
      ev={"part": "ground poppy-seed", "solvent": "taken in milk", "process": "ground poppy-seed", "form": "Lozenges are also made"}),
    R("The seed is employed, too, with rose-oil for head-ache", PO, "head-ache", part="seed", solvent=("oil",), ev={"part": "The seed is employed", "solvent": "with rose-oil"}),
    R("in combination with that oil, is injected into the ears for ear-ache", PO, "ear-ache", part="seed", solvent=("oil",), form="other",
      ev={"part": "The seed is employed", "solvent": "in combination with that oil", "form": "injected into the ears"}),
    R(MI, PO, "gout", part="seed", solvent=("other",), form="ointment", filt="not_applicable",
      ev={"part": "this seed", "solvent": "Mixed with woman’s milk", "form": "used as a liniment", "filtered": "used as a liniment"}),
    R(MI, PO, "gout", part="leaf", solvent=("other",), form="ointment", filt="not_applicable",
      ev={"part": "the leaves, too", "solvent": "Mixed with woman’s milk", "form": "used as a liniment", "filtered": "used as a liniment"}),
    R("Taken in vinegar, the seed is prescribed as a cure for erysipelas and wounds.", PO, "erysipelas and wounds", part="seed", solvent=("vinegar",),
      ev={"part": "the seed is prescribed", "solvent": "Taken in vinegar"}),
]   # opium used to end life, and as a poison: not a health use
P["pliny-nh:b20:c076:002"] = [
    R("the black poppy, however, is very generally prescribed, in wine, for cœliac affections", "black poppy", "cœliac affections", solvent=("wine",),
      ev={"solvent": "prescribed, in wine"}),
    R("This head is often boiled, and the decoction of it taken to promote sleep", "wild poppy", "to promote sleep", part="fruit", heat="boiled",
      process="decoction", form="drink",
      ev={"part": "This head is often boiled", "heat": "This head is often boiled", "process": "the decoction of it", "form": "the decoction of it taken"}),
    R("This head is often boiled, and the decoction of it taken to promote sleep, the face being fomented also with the water", "wild poppy", "to promote sleep",
      part="fruit", solvent=("water",), heat="boiled", process="decoction", form="other",
      ev={"part": "This head is often boiled", "solvent": "fomented also with the water", "heat": "This head is often boiled",
          "process": "the decoction of it", "form": "the face being fomented also with the water"}),
]
print(write("approved", 20, P))
