from build_batch import R, write
P = {}
for pid in ("wood-betony:002", "wood-betony:003", "wood-betony:005", "carraway:001", "carraway:002", "carraway:003", "carraway:004"):
    P["culpeper-1850:herbal:" + pid] = []   # place / time / storage / intro / description
B = "Betony"
STOM = "those that loath and cannot digest their meat, those that have weak stomachs and sour belchings, or continual rising in their stomachs"
Q0 = "it helps those that loath and cannot digest their meat, those that have weak stomachs and sour belchings, or continual rising in their stomachs, using it familiarly either green or dry; either the herb, or root, or the flowers, in broth"
Q1 = Q0 + ", drink, or meat"
Q2 = Q1 + ", or made into conserve, syrup, water, electuary, or powder"
DW = "the decoction thereof made in wine and taken"
GH = "The green herb bruised, or the juice applied to any inward hurt, or outward green wound in the head or body, will quickly heal and close it up; as also any vein or sinews that are cut, and will draw forth any broken bone or splinter, thorn or other things got into the flesh"
GHI = "any inward hurt, or outward green wound in the head or body, will quickly heal and close it up; as also any vein or sinews that are cut, and will draw forth any broken bone or splinter, thorn or other things got into the flesh"
P["culpeper-1850:herbal:wood-betony:004"] = [
    R("that it preserves the liver and bodies of men from the danger of epidemical diseases, and from witchcraft also", B,
      "preserves the liver and bodies of men from the danger of epidemical diseases, and from witchcraft also"),
    R(Q0, B, STOM, solvent=("other",), ev={"solvent": "the flowers, in broth"}),
    R(Q1, B, STOM, form="drink", ev={"form": "in broth, drink"}),
    R(Q1, B, STOM, form="other", ev={"form": "drink, or meat"}),
    R(Q2, B, STOM, process="other", form="other", ev={"process": "made into conserve, syrup", "form": "made into conserve, syrup"}),
    R(Q2, B, STOM, solvent=("water",), ev={"solvent": "syrup, water, electuary"}),
    R(Q2, B, STOM, process="powder", ev={"process": "electuary, or powder"}),
    R("taken any of the aforesaid ways, it helps the jaundice, falling sickness, the palsy, convulsions, or shrinking of the sinews, the gout and those that are inclined to dropsy, those that have continual pains in their heads, although it turn to phrensy.",
      B, "the jaundice, falling sickness, the palsy, convulsions, or shrinking of the sinews, the gout and those that are inclined to dropsy, those that have continual pains in their heads, although it turn to phrensy"),
    R("The powder mixed with pure honey is no less available for all sorts of coughs or colds, wheesing, or shortness of breath, distillations of thin rheum upon the lungs, which causes consumptions.",
      B, "all sorts of coughs or colds, wheesing, or shortness of breath, distillations of thin rheum upon the lungs, which causes consumptions",
      solvent=("honey",), process="powder", ev={"solvent": "mixed with pure honey", "process": "The powder mixed with pure honey"}),
    R("The decoction made with Mead, and a little Pennyroyal, is good for those that are troubled with putrid agues, whether quotidian, tertian, or quartan, and to draw down and evacuate the blood and humours, that by falling into the eyes, do hinder the sight",
      B, "putrid agues, whether quotidian, tertian, or quartan, and to draw down and evacuate the blood and humours, that by falling into the eyes, do hinder the sight",
      rtype="compound", ingredients=[(B, "unknown", "principal", "plant"), ("Pennyroyal", "unknown", "co_ingredient", "plant")],
      solvent=("other",), heat="boiled", process="decoction",
      ev={"solvent": "made with Mead", "heat": "The decoction made with Mead", "process": "The decoction made with Mead"}),
    R(DW + ", kills the worms in the belly, opens obstructions both of the spleen and liver; cures stitches, and pains in the back and sides, the torments and griping pains in the bowels, and the wind cholic",
      B, "kills the worms in the belly, opens obstructions both of the spleen and liver; cures stitches, and pains in the back and sides, the torments and griping pains in the bowels, and the wind cholic",
      solvent=("wine",), heat="boiled", process="decoction", form="drink",
      ev={"solvent": "made in wine", "heat": DW, "process": DW, "form": DW}),
    R("and mixed with honey purges the belly, helps to bring down women’s courses, and is of special use for those that are troubled with the falling down of the mother, and pains thereof, and causes an easy and speedy delivery of women in child-birth",
      B, "purges the belly, helps to bring down women’s courses, and is of special use for those that are troubled with the falling down of the mother, and pains thereof, and causes an easy and speedy delivery of women in child-birth",
      solvent=("wine", "honey"), heat="boiled", process="decoction", form="drink",
      ev={"solvent": ["made in wine", "mixed with honey"], "heat": DW, "process": DW, "form": DW}),
    R("It helps also to break and expel the stone, either in the bladder or kidneys.", B, "to break and expel the stone, either in the bladder or kidneys"),
    R("The decoction with wine gargled in the mouth, eases the tooth-ache.", B, "eases the tooth-ache", solvent=("wine",), heat="boiled", process="decoction",
      form="gargle", ev={"solvent": "The decoction with wine", "heat": "The decoction with wine", "process": "The decoction with wine", "form": "gargled in the mouth"}),
    R("It is commended against the stinging and biting of venomous serpents, or mad dogs, being used inwardly and applied outwardly to the place.", B,
      "the stinging and biting of venomous serpents, or mad dogs"),
    R("A dram of the powder of Betony taken with a little honey in some vinegar, does wonderfully refresh those that are over wearied by travelling.", B,
      "refresh those that are over wearied by travelling", solvent=("honey", "vinegar"), process="powder", form="drink", filt="no",
      ev={"solvent": "taken with a little honey in some vinegar", "process": "A dram of the powder of Betony", "form": "taken with a little honey in some vinegar",
          "filtered": "A dram of the powder of Betony taken with a little honey in some vinegar"}),
    R("It stays bleeding at the mouth or nose, and helps those that void or spit blood, and those that are bursten or have a rupture, and is good for such as are bruised by any fall or otherwise.",
      B, "bleeding at the mouth or nose, and helps those that void or spit blood, and those that are bursten or have a rupture, and is good for such as are bruised by any fall or otherwise"),
    R(GH, B, GHI, fod="fresh", heat="cold", process="other", form="poultice", filt="not_applicable",
      ev={"freshOrDried": "The green herb bruised", "heat": "The green herb bruised", "process": "The green herb bruised", "form": "The green herb bruised",
          "filtered": "The green herb bruised"}),
    R(GH, B, GHI, part="juice", heat="cold", form="other", ev={"part": "the juice applied", "heat": "the juice applied", "form": "the juice applied"}),
    R("It is no less profitable for old sores or filthy ulcers, yea, tho’ they be fistulous and hollow.", B, "old sores or filthy ulcers, yea, tho’ they be fistulous and hollow"),
    R("It is no less profitable for old sores or filthy ulcers, yea, tho’ they be fistulous and hollow. But some do advise to put a little salt for this purpose",
      B, "old sores or filthy ulcers, yea, tho’ they be fistulous and hollow", rtype="compound",
      ingredients=[(B, "unknown", "principal", "plant"), ("salt", "unknown", "co_ingredient", "mineral")]),
    R("being applied with a little hog’s lard, it helps a plague sore, and other boils and pushes", B, "a plague sore, and other boils and pushes",
      solvent=("other",), ev={"solvent": "applied with a little hog’s lard"}),
    R("The fumes of the decoction while it is warm, received by a funnel into the ears, eases the pains of them, destroys the worms and cures the running sores in them.",
      B, "eases the pains of them, destroys the worms and cures the running sores in them", heat="boiled", heatText="while it is warm", process="decoction",
      form="inhalation", filt="not_applicable",
      ev={"heat": "The fumes of the decoction", "process": "The fumes of the decoction", "form": "The fumes of the decoction while it is warm, received by a funnel",
          "filtered": "The fumes of the decoction"}),
    R("The juice dropped into them does the same.", B, "does the same", part="juice", heat="cold", form="other",
      ev={"part": "The juice dropped into them", "heat": "The juice dropped into them", "form": "The juice dropped into them"}),
]
C = "Carraway"
P["culpeper-1850:herbal:carraway:005"] = [
    R("Carraway seed has a moderate sharp quality, whereby it breaks wind and provokes urine", C, "breaks wind and provokes urine", part="seed",
      ev={"part": "Carraway seed"}),
    R("Carraway seed has a moderate sharp quality, whereby it breaks wind and provokes urine, which also the herb doth", C, "breaks wind and provokes urine"),
    R("The root is better food than the parsnip; it is pleasant and comfortable to the stomach, and helps digestion.", C,
      "pleasant and comfortable to the stomach, and helps digestion", part="root", form="other",
      ev={"part": "The root is better food", "form": "The root is better food than the parsnip"}),
    R("The seed is conducing to all cold griefs of the head and stomach, bowels, or mother, as also the wind in them, and helps to sharpen the eye-sight.",
      C, "all cold griefs of the head and stomach, bowels, or mother, as also the wind in them, and helps to sharpen the eye-sight", part="seed",
      ev={"part": "The seed is conducing"}),
    R("The powder of the seed put into a poultice, takes away black and blue spots of blows and bruises.", C, "black and blue spots of blows and bruises",
      rtype="unknown", part="seed", heat="cold", process="powder", form="poultice", filt="not_applicable",
      ev={"part": "The powder of the seed", "heat": "The powder of the seed", "process": "The powder of the seed", "form": "put into a poultice",
          "filtered": "put into a poultice"}),
    R("The herb itself, or with some of the seed bruised and fried, laid hot in a bag or double cloth, to the lower parts of the belly, eases the pains of the wind cholic.",
      C, "eases the pains of the wind cholic", heat="warm", heatText="fried, laid hot", process="other", form="other", filt="not_applicable",
      ev={"heat": "bruised and fried, laid hot", "process": "bruised and fried", "form": "laid hot in a bag or double cloth",
          "filtered": "laid hot in a bag or double cloth"}),
]
P["culpeper-1850:herbal:carraway:006"] = [
    R("The roots of Carraway eaten as men do parsnips, strengthen the stomach of ancient people exceedingly", C,
      "strengthen the stomach of ancient people exceedingly", part="root", form="other",
      ev={"part": "The roots of Carraway", "form": "eaten as men do parsnips"}),
]
print(write("approved", 12, P))
