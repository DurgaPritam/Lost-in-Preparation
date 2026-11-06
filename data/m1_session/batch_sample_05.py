from build_batch import R, write
P = {}
P["pliny-nh:b24:c022:001"] = [
    R("it is mostly that produced by the larch, which is administered in an egg for cough and ulcerations of the viscera", "larch",
      "cough and ulcerations of the viscera", part="resin", solvent=("other",),
      ev={"part": "make use of liquid resin", "solvent": "administered in an egg"}),
]
P["pliny-nh:b24:c027:001"] = [
    R("A decoction in vinegar of the wood of the torch-tree makes a most efficacious gargle for tooth-ache.", "torch-tree", "tooth-ache",
      part="stem", solvent=("vinegar",), heat="boiled", process="decoction", form="gargle",
      ev={"part": "the wood of the torch-tree", "solvent": "A decoction in vinegar", "heat": "A decoction in vinegar",
          "process": "A decoction in vinegar", "form": "makes a most efficacious gargle"}),
]
BR = "brya"
P["pliny-nh:b24:c042:001"] = [
    R("The bark is pounded also, and given for discharges of blood from the mouth, irregularities of the catamenia, and cœliac affections", BR,
      "discharges of blood from the mouth, irregularities of the catamenia, and cœliac affections", part="bark", heat="cold", process="powder",
      ev={"part": "The bark is pounded", "heat": "The bark is pounded", "process": "The bark is pounded"}),
    R("beaten up and applied to the part affected, it checks the increase of all kinds of abscesses", BR, "checks the increase of all kinds of abscesses",
      part="bark", heat="cold", process="other", form="poultice", filt="not_applicable",
      ev={"part": "The bark is pounded also", "heat": "beaten up and applied", "process": "beaten up and applied to the part affected",
          "form": "beaten up and applied to the part affected", "filtered": "beaten up and applied to the part affected"}),
]
ER = "erythrodanus"
P["pliny-nh:b24:c056:001"] = [
    R("Used medicinally, it is a diuretic", ER, "a diuretic"),
    R("employed with hydromel, it is curative of jaundice", ER, "jaundice", solvent=("water", "honey"), ev={"solvent": "employed with hydromel"}),
    R("Employed topically with vinegar, it heals lichens", ER, "lichens", solvent=("vinegar",), ev={"solvent": "Employed topically with vinegar"}),
    R("a potion is prepared from it for sciatica and paralysis, the patient while using it taking a bath daily", ER, "sciatica and paralysis",
      form="drink", ev={"form": "a potion is prepared from it"}),
    R("The root of it and the seed are effectual as an emmenagogue; they act astringently upon the bowels, and disperse gatherings", ER,
      "effectual as an emmenagogue; they act astringently upon the bowels, and disperse gatherings", part="other",
      ev={"part": "The root of it and the seed"}),
    R("The branches, together with the leaves, are applied to wounds inflicted by serpents", ER, "wounds inflicted by serpents", part="other",
      form="poultice", filt="not_applicable",
      ev={"part": "The branches, together with the leaves", "form": "are applied to wounds", "filtered": "are applied to wounds"}),
    R("this shrub is curative of jaundice, even if worn as an amulet only", ER, "jaundice", solvent=("none",), form="other", filt="not_applicable",
      ev={"solvent": "worn as an amulet only", "form": "worn as an amulet only", "filtered": "worn as an amulet only"}),
]   # "the leaves too have the property of staining the hair": cosmetic, no health indication
CH = "chamædrys"
P["pliny-nh:b24:c080:002"] = [
    R("whether taken internally or applied topically, it is extremely efficacious for the stings of venomous serpents, diseases of the stomach, inveterate coughs, collections of phlegm in the throat, ruptures, convulsions, and pains in the sides",
      CH, "the stings of venomous serpents, diseases of the stomach, inveterate coughs, collections of phlegm in the throat, ruptures, convulsions, and pains in the sides"),
    R("It diminishes the volume of the spleen, and acts as a diuretic and emmenagogue; for which reasons it is very useful in incipient dropsy, the usual dose being a handful of the sprigs boiled down to one third in three heminæ of water",
      CH, "It diminishes the volume of the spleen, and acts as a diuretic and emmenagogue; for which reasons it is very useful in incipient dropsy",
      solvent=("water",), heat="boiled", dur="boiled down to one third", process="decoction",
      ev={"solvent": "in three heminæ of water", "heat": "boiled down to one third", "process": "boiled down to one third in three heminæ of water"}),
    R("Lozenges too are made of it for the above-named purposes, by bruising it in water", CH, "the above-named purposes", solvent=("water",),
      heat="cold", process="other", form="other",
      ev={"solvent": "by bruising it in water", "heat": "by bruising it in water", "process": "by bruising it in water",
          "form": "Lozenges too are made of it"}),
    R("In combination with honey, it heals abscesses and inveterate or sordid ulcers", CH, "abscesses and inveterate or sordid ulcers",
      solvent=("honey",), ev={"solvent": "In combination with honey"}),
    R("a wine too is prepared from it for diseases of the chest", CH, "diseases of the chest", solvent=("wine",),
      ev={"solvent": "a wine too is prepared from it"}),
    R("The juice of the leaves, mixed with oil, disperses films on the eyes", CH, "disperses films on the eyes", part="juice", solvent=("oil",),
      heat="cold", ev={"part": "The juice of the leaves", "solvent": "mixed with oil", "heat": "The juice of the leaves"}),
    R("it is taken also, in vinegar, for diseases of the spleen", CH, "diseases of the spleen", solvent=("vinegar",), ev={"solvent": "in vinegar"}),
]   # "employed as a friction, it is of a warming nature": a property, no indication
P["pliny-nh:b24:c107:001"] = []   # "Any plant" gathered by a river: an amulet, but no named material
P["pliny-nh:b25:c006:001"] = []   # keeping birds off crops; no health use
P["pliny-nh:b25:c011:002"] = []   # gathering and grading the juice; no indication
TR = "trichomanes"
P["pliny-nh:b27:c111:001"] = [
    R("A decoction of this plant, taken in white wine, with the addition of wild cummin, is curative of strangury", TR, "strangury", rtype="compound",
      ingredients=[(TR, "unknown", "principal", "plant"), ("wild cummin", "unknown", "co_ingredient", "plant")],
      solvent=("wine",), heat="boiled", process="decoction", form="drink",
      ev={"solvent": "taken in white wine", "heat": "A decoction of this plant", "process": "A decoction of this plant", "form": "taken in white wine"}),
    R("Bruised and applied to the head, it prevents the hair from falling off, and, where it has come off, restores it", TR,
      "prevents the hair from falling off, and, where it has come off, restores it", heat="cold", process="other", form="poultice", filt="not_applicable",
      ev={"heat": "Bruised and applied to the head", "process": "Bruised and applied", "form": "Bruised and applied to the head",
          "filtered": "Bruised and applied to the head"}),
    R("pounded and applied with oil, it effects the cure of alopecy", TR, "alopecy", solvent=("oil",), process="other", form="ointment",
      filt="not_applicable", ev={"solvent": "applied with oil", "process": "pounded and applied with oil", "form": "applied with oil",
                                  "filtered": "pounded and applied with oil"}),
]   # "The mere taste of it is provocative of sneezing": an effect, not a use
P["pliny-nh:b27:c113:002"] = [
    R("The other thlaspi, known by some as “Persicon napy,” has broad leaves and large roots, and is also very useful as an injection for sciatica",
      "Persicon napy", "sciatica", form="other", ev={"form": "as an injection"}),
    R("Both plants are very serviceable for inguinal complaints", "thlaspi", "inguinal complaints"),
    R("Both plants are very serviceable for inguinal complaints", "Persicon napy", "inguinal complaints"),
]
print(write("sample", 5, P))
