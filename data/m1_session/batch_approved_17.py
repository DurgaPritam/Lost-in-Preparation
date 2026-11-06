from build_batch import R, write
P = {}
GP_ = "ground-pine-or-chamepitys"
MS_ = "queen-of-the-meadows-meadow-sweet-or-mead-sweet"
for pid in ("onions:001", f"{GP_}:001", f"{GP_}:002", f"{GP_}:003", f"{MS_}:001", f"{MS_}:002", f"{MS_}:003"):
    P["culpeper-1850:herbal:" + pid] = []   # intro / description / place / time
O = "Onions"
ROAST = "Being roasted under the embers, and eaten with honey or sugar and oil, they much conduce to help an inveterate cough, and expectorate the cough phlegm."
RI = "help an inveterate cough, and expectorate the cough phlegm"
JU = "The juice of Onions is good for either scalding or burning by fire, water, or gunpowder, and used with vinegar, takes away all blemishes, spots and marks in the skin: and dropped in the ears, eases the pains and noise of them."
P["culpeper-1850:herbal:onions:002"] = [
    R("then, being bruised and applied to a plague sore, it is very probable it will do the like", O, "a plague sore", heat="cold", process="other",
      form="poultice", filt="not_applicable",
      ev={"heat": "being bruised and applied", "process": "being bruised and applied", "form": "being bruised and applied to a plague sore",
          "filtered": "being bruised and applied"}),
    R("Onions are flatulent, or windy; yet they do somewhat provoke appetite, increase thirst, ease the belly and bowels, provoke women’s courses", O,
      "provoke appetite, increase thirst, ease the belly and bowels, provoke women’s courses"),
    R("help the biting of a mad dog, and of other venomous creatures, to be used with honey and rue", O, "the biting of a mad dog, and of other venomous creatures",
      rtype="compound", ingredients=[(O, "unknown", "principal", "plant"), ("rue", "unknown", "co_ingredient", "plant")], solvent=("honey",),
      ev={"solvent": "used with honey and rue"}),
    R("increase sperm, especially the seed of them", O, "increase sperm", part="seed", ev={"part": "especially the seed of them"}),
    R("They also kill worms in children if they drink the water fasting wherein they have been steeped all night.", O, "kill worms in children",
      solvent=("water",), dur="all night", process="infusion", form="drink",
      ev={"solvent": "drink the water fasting wherein they have been steeped", "process": "steeped all night", "form": "if they drink the water"}),
    R(ROAST, O, RI, solvent=("honey",), heat="warm", heatText="roasted under the embers", process="other", form="other",
      ev={"solvent": "eaten with honey", "heat": "Being roasted under the embers", "process": "Being roasted under the embers", "form": "eaten with honey"}),
    R(ROAST, O, RI, rtype="compound", ingredients=[(O, "unknown", "principal", "plant"), ("sugar", "unknown", "co_ingredient", "other")], solvent=("oil",),
      heat="warm", heatText="roasted under the embers", process="other", form="other",
      ev={"solvent": "sugar and oil", "heat": "Being roasted under the embers", "process": "Being roasted under the embers", "form": "eaten with honey or sugar and oil"}),
    R("The juice being snuffed up into the nostrils, purges the head, and helps the lethargy", O, "purges the head, and helps the lethargy", part="juice",
      heat="cold", form="inhalation",
      ev={"part": "The juice being snuffed up", "heat": "The juice being snuffed up", "form": "snuffed up into the nostrils"}),
    R("It hath been held by divers country people a great preservative against infection, to eat Onions fasting with bread and salt", O,
      "a great preservative against infection", rtype="compound",
      ingredients=[(O, "unknown", "principal", "plant"), ("bread", "unknown", "co_ingredient", "other"), ("salt", "unknown", "co_ingredient", "mineral")],
      form="other", ev={"form": "to eat Onions fasting"}),
    R("to make a great Onion hollow, filling the place with good treacle, and after to roast it well under the embers, which, after taking away the outermost skin thereof, being beaten together, is a sovereign salve for either plague or sore, or any other putrefied ulcer",
      "Onion", "plague or sore, or any other putrefied ulcer", rtype="compound",
      ingredients=[("Onion", "unknown", "principal", "plant"), ("treacle", "unknown", "co_ingredient", "other")], heat="warm",
      heatText="roast it well under the embers", process="other", form="ointment", filt="not_applicable",
      ev={"heat": "roast it well under the embers", "process": "being beaten together", "form": "a sovereign salve", "filtered": "a sovereign salve"}),
    R(JU, O, "either scalding or burning by fire, water, or gunpowder", part="juice", heat="cold",
      ev={"part": "The juice of Onions", "heat": "The juice of Onions"}),
    R(JU, O, "takes away all blemishes, spots and marks in the skin", part="juice", solvent=("vinegar",), heat="cold",
      ev={"part": "The juice of Onions", "solvent": "used with vinegar", "heat": "The juice of Onions"}),
    R(JU, O, "eases the pains and noise of them", part="juice", heat="cold", form="other",
      ev={"part": "The juice of Onions", "heat": "The juice of Onions", "form": "dropped in the ears"}),
    R("Applied also with figs beaten together, helps to ripen and break imposthumes, and other sores.", O, "to ripen and break imposthumes, and other sores",
      rtype="compound", ingredients=[(O, "unknown", "principal", "plant"), ("figs", "fruit", "co_ingredient", "plant")], heat="cold", process="other",
      form="poultice", filt="not_applicable",
      ev={"heat": "with figs beaten together", "process": "with figs beaten together", "form": "Applied also with figs beaten together",
          "filtered": "Applied also with figs beaten together"}),
]
P["culpeper-1850:herbal:onions:003"] = [
    R("They are a remedy against a surfeit of mushrooms, being baked under the embers and taken", "Leeks", "a surfeit of mushrooms", heat="warm",
      heatText="baked under the embers", process="other", ev={"heat": "being baked under the embers", "process": "being baked under the embers"}),
    R("being boiled and applied very warm, help the piles", "Leeks", "the piles", heat="boiled", heatText="applied very warm", form="poultice",
      filt="not_applicable", ev={"heat": "being boiled and applied very warm", "form": "being boiled and applied", "filtered": "being boiled and applied"}),
]   # Leeks are a different plant from Onions; recorded under their own name
G = "Ground Pine"
JI = "all pains and diseases of the joints, as gouts, cramps, palsies, sciatica, and aches"
DW = "The decoction of the herb in wine taken inwardly, or applied outwardly, or both, for some time together, is also effectual in all pains and diseases of the joints, as gouts, cramps, palsies, sciatica, and aches"
PILLS = [(G, "unknown", "principal", "plant"), ("Hermodactyls", "unknown", "co_ingredient", "plant"), ("Venice Turpentine", "resin", "co_ingredient", "plant")]
GH = "The green herb, or the decoction thereof, being applied, dissolves the hardness of women’s breasts, and all other hard swellings in any other part of the body."
GHI = "dissolves the hardness of women’s breasts, and all other hard swellings in any other part of the body"
GU = "The green herb also applied, or the juice thereof with some honey, not only cleanses putrid, stinking, foul, and malignant ulcers and sores of all sorts, but heals and solders up the lips of green wounds in any part also."
GUI = "cleanses putrid, stinking, foul, and malignant ulcers and sores of all sorts, but heals and solders up the lips of green wounds in any part also"
P[f"culpeper-1850:herbal:{GP_}:004"] = [
    R("The decoction of Ground Pine drank, doth wonderfully prevail against the stranguary, or any inward pains arising from the diseases of the reins and urine, and is especially good for all obstructions of the liver and spleen, and gently opens the body",
      G, "the stranguary, or any inward pains arising from the diseases of the reins and urine, and is especially good for all obstructions of the liver and spleen, and gently opens the body",
      heat="boiled", process="decoction", form="drink",
      ev={"heat": "The decoction of Ground Pine", "process": "The decoction of Ground Pine", "form": "The decoction of Ground Pine drank"}),
    R("gently opens the body; for which purpose they were wont in former times to make pills with the powder thereof, and the pulp of figs", G,
      "gently opens the body", rtype="compound", ingredients=[(G, "unknown", "principal", "plant"), ("figs", "fruit", "co_ingredient", "plant")],
      process="powder", form="other", ev={"process": "pills with the powder thereof", "form": "to make pills"}),
    R("It marvellously helps all the diseases of the mother, inwardly or outwardly applied, procuring women’s courses, and expelling the dead child and after-birth",
      G, "all the diseases of the mother, inwardly or outwardly applied, procuring women’s courses, and expelling the dead child and after-birth"),
    R(DW, G, JI, solvent=("wine",), heat="boiled", process="decoction", form="drink",
      ev={"solvent": "the herb in wine", "heat": "The decoction of the herb", "process": "The decoction of the herb", "form": "taken inwardly"}),
    R(DW, G, JI, solvent=("wine",), heat="boiled", process="decoction",
      ev={"solvent": "the herb in wine", "heat": "The decoction of the herb", "process": "The decoction of the herb"}),
    R("is also effectual in all pains and diseases of the joints, as gouts, cramps, palsies, sciatica, and aches; for which purpose the pills made with powder of Ground Pine, and of Hermodactyls with Venice Turpentine are very effectual",
      G, JI, rtype="compound", ingredients=PILLS, process="powder", form="other",
      ev={"process": "powder of Ground Pine", "form": "the pills made with powder"}),
    R("The pills also, continued for some time, are special good for those that have the dropsy, jaundice, and for griping pains of the joints, belly, or inward parts.",
      G, "those that have the dropsy, jaundice, and for griping pains of the joints, belly, or inward parts", rtype="compound", ingredients=PILLS,
      process="powder", form="other", ev={"process": "powder of Ground Pine", "form": "The pills also"}),
    R("It helps also all diseases of the brain, proceeding of cold and phlegmatic humours and distillations, as also for the falling sickness. It is a special remedy for the poison of the aconites, and other poisonous herbs, as also against the stinging of any venomous creature. It is a good remedy for a cold cough, especially in the beginning.",
      G, "all diseases of the brain, proceeding of cold and phlegmatic humours and distillations, as also for the falling sickness. It is a special remedy for the poison of the aconites, and other poisonous herbs, as also against the stinging of any venomous creature. It is a good remedy for a cold cough"),
    R("For all the purposes aforesaid, the herb being tunned up in new drink and drank, is almost as effectual", G, "all the purposes aforesaid",
      solvent=("other",), form="drink", ev={"solvent": "tunned up in new drink", "form": "in new drink and drank"}),
    R("The distilled water of the herb hath the same effects, but more weakly.", G, "hath the same effects", solvent=("water",), heat="boiled",
      process="distillation", ev={"solvent": "The distilled water of the herb", "heat": "The distilled water", "process": "The distilled water"}),
    R("The conserve of the flowers doth the like, which Matthiolus much commends against the palsy.", G, "doth the like, which Matthiolus much commends against the palsy",
      part="flower", process="other", form="other",
      ev={"part": "The conserve of the flowers", "process": "The conserve of the flowers", "form": "The conserve of the flowers"}),
    R(GH, G, GHI, fod="fresh", heat="cold", form="poultice", filt="not_applicable",
      ev={"freshOrDried": "The green herb", "heat": "The green herb, or the decoction thereof, being applied", "form": "The green herb, or the decoction thereof, being applied",
          "filtered": "The green herb, or the decoction thereof, being applied"}),
    R(GH, G, GHI, heat="boiled", process="decoction", ev={"heat": "the decoction thereof", "process": "the decoction thereof, being applied"}),
    R(GU, G, GUI, fod="fresh", heat="cold", form="poultice", filt="not_applicable",
      ev={"freshOrDried": "The green herb also applied", "heat": "The green herb also applied", "form": "The green herb also applied",
          "filtered": "The green herb also applied"}),
    R(GU, G, GUI, part="juice", solvent=("honey",), heat="cold",
      ev={"part": "the juice thereof", "solvent": "the juice thereof with some honey", "heat": "the juice thereof with some honey"}),
]
print(write("approved", 17, P))
