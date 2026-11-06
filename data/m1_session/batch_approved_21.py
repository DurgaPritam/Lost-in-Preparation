from build_batch import R, write
P = {}
P["pliny-nh:b20:c076:005"] = []   # keeping opium
for c in ("001", "002", "003", "004"):
    P[f"pliny-nh:b21:c017:{c}"] = []   # saffron: growing, grading, adulteration tests, perfume; no health use
CR = "coriander"
AM = "Taken in drink and applied to the wound, it is a remedy for the sting of one kind of serpent, known as the amphisbæna"
AMI = "the sting of one kind of serpent, known as the amphisbæna"
HR = "Employed in the same state with honey or raisins, it disperses all tumours and gatherings"
TF = "Some persons recommend three grains of it to be taken for tertian fevers, just before the fit comes on, or else in larger quantities, to be bruised and applied to the forehead"
P["pliny-nh:b20:c082:001"] = [
    R(AM, CR, AMI, form="drink", ev={"form": "Taken in drink"}),
    R(AM, CR, AMI, form="poultice", filt="not_applicable", ev={"form": "applied to the wound", "filtered": "applied to the wound"}),
    R("pounded, it is healing also for other wounds, as well as for epinyctis and blisters", CR, "other wounds, as well as for epinyctis and blisters",
      process="other", ev={"process": "pounded, it is healing"}),
    R(HR, CR, "disperses all tumours and gatherings", solvent=("honey",), process="other",
      ev={"solvent": "with honey or raisins", "process": "Employed in the same state"}),
    R(HR, CR, "disperses all tumours and gatherings", rtype="compound",
      ingredients=[(CR, "unknown", "principal", "plant"), ("raisins", "fruit", "co_ingredient", "plant")], process="other",
      ev={"process": "Employed in the same state"}),
    R("and, beaten up in vinegar, it removes abscesses of an inflammatory nature", CR, "abscesses of an inflammatory nature", solvent=("vinegar",),
      process="other", ev={"solvent": "beaten up in vinegar", "process": "beaten up in vinegar"}),
    R(TF, CR, "tertian fevers", part="seed", ev={"part": "three grains of it"}),
    R(TF, CR, "tertian fevers", heat="cold", process="other", form="poultice", filt="not_applicable",
      ev={"heat": "to be bruised and applied", "process": "to be bruised and applied", "form": "bruised and applied to the forehead",
          "filtered": "bruised and applied to the forehead"}),
]   # coriander under the pillow: no indication named in that sentence
HRA = "Combined with honey or raisins, it is an excellent remedy for spreading ulcers, as also for diseases of the testes, burns, carbuncles, and maladies of the ears"
HRI = "spreading ulcers, as also for diseases of the testes, burns, carbuncles, and maladies of the ears"
P["pliny-nh:b20:c082:002"] = [
    R(HRA, CR, HRI, solvent=("honey",), ev={"solvent": "Combined with honey"}),
    R(HRA, CR, HRI, rtype="compound", ingredients=[(CR, "unknown", "principal", "plant"), ("raisins", "fruit", "co_ingredient", "plant")]),
    R("Applied with woman’s milk, it is good for defluxions of the eyes", CR, "defluxions of the eyes", solvent=("other",),
      ev={"solvent": "Applied with woman’s milk"}),
    R("for fluxes of the belly and intestines, the seed is taken with water in drink", CR, "fluxes of the belly and intestines", part="seed",
      solvent=("water",), form="drink", ev={"part": "the seed is taken", "solvent": "taken with water in drink", "form": "taken with water in drink"}),
    R("it is also taken in drink for cholera, with rue", CR, "cholera", rtype="compound",
      ingredients=[(CR, "unknown", "principal", "plant"), ("rue", "unknown", "co_ingredient", "plant")], form="drink", ev={"form": "taken in drink"}),
    R("Coriander seed, used as a potion with pomegranate juice and oil, expels worms in the intestines.", "Coriander", "expels worms in the intestines",
      rtype="compound", ingredients=[("Coriander", "seed", "principal", "plant"), ("pomegranate", "juice", "co_ingredient", "plant")], part="seed",
      solvent=("oil",), form="drink", ev={"part": "Coriander seed", "solvent": "pomegranate juice and oil", "form": "used as a potion"}),
]   # "While green, it is possessed of very cooling and refreshing properties": a property, no indication
P["pliny-nh:b20:c082:003"] = [
    R("if a woman takes one grain of this seed, the menstrual discharge will be retarded one day", CR, "the menstrual discharge will be retarded one day",
      part="seed", ev={"part": "one grain of this seed"}),
]   # keeping meat with coriander: not a health use
GL = "glycyrrhiza"
ROOT = "the root of it is sweet, and this is the only part that is used"
P["pliny-nh:b22:c011:001"] = [
    R("Sometimes, also, it is used pounded, and it is in this form that it is applied as a liniment for wounds and all affections of the throat", GL,
      "wounds and all affections of the throat", part="root", process="other", form="ointment", filt="not_applicable",
      ev={"part": ROOT, "process": "it is used pounded", "form": "applied as a liniment", "filtered": "applied as a liniment"}),
    R("The juice of it is also very good for the voice, for which purpose it is thickened and then placed beneath the tongue: it is good, too, for the chest and liver.",
      GL, "very good for the voice, for which purpose it is thickened and then placed beneath the tongue: it is good, too, for the chest and liver",
      part="juice", process="other", form="other",
      ev={"part": "The juice of it", "process": "it is thickened", "form": "placed beneath the tongue"}),
]   # pessaries and the honey-thick decoction: no indication named
P["pliny-nh:b22:c011:002"] = [
    R("this plant has the effect of allaying hunger and thirst: hence it is that some authors have given it the name of “adipsos,” and have prescribed it for dropsical patients, to allay thirst",
      "adipsos", "allaying hunger and thirst: hence it is that some authors have given it the name of “adipsos,” and have prescribed it for dropsical patients, to allay thirst",
      heading=True),
    R("It is for this reason, too, that it is chewed as a stomatic", "adipsos", "a stomatic", heading=True, form="other", ev={"form": "it is chewed"}),
    R("the powder of it is often sprinkled on ulcerous sores of the mouth and films on the eyes", "adipsos", "ulcerous sores of the mouth and films on the eyes",
      heading=True, solvent=("none",), heat="cold", process="powder",
      ev={"solvent": "the powder of it is often sprinkled", "heat": "the powder of it", "process": "the powder of it"}),
    R("it heals, too, excrescences of the bladder, pains in the kidneys, condylomata, and ulcerous sores of the genitals", "adipsos",
      "excrescences of the bladder, pains in the kidneys, condylomata, and ulcerous sores of the genitals", heading=True),
    R("Some persons have given it in potions for quartan fevers, the doses being two drachmæ, mixed with pepper in one hemina of water.", "adipsos",
      "quartan fevers", heading=True, rtype="compound",
      ingredients=[("adipsos", "unknown", "principal", "plant"), ("pepper", "unknown", "co_ingredient", "plant")], solvent=("water",), form="drink",
      ev={"solvent": "in one hemina of water", "form": "given it in potions"}),
    R("Chewed, and applied to wounds, it arrests hæmorrhage", "adipsos", "arrests hæmorrhage", heading=True, process="other", form="poultice",
      filt="not_applicable", ev={"process": "Chewed, and applied", "form": "Chewed, and applied to wounds", "filtered": "Chewed, and applied to wounds"}),
    R("some authors have asserted, also, that it expels calculi of the bladder", "adipsos", "expels calculi of the bladder", heading=True),
]
P["pliny-nh:b24:c020:001"] = [
    R("The chamæpitys, called in Latin “abiga,” because it promotes abortion", "chamæpitys", "promotes abortion"),
]
print(write("approved", 21, P))
