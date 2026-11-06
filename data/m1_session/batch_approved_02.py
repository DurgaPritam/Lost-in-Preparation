from build_batch import R, write
P = {}
for pid in ("wood-betony:006", "wood-betony:009", "caraway:002", "caraway:004", "caraway:006", "celandine:002"):
    P["culpeper-1652:herbal:" + pid] = []   # description / place / time / storage: no indication
B = "Betony"
STOM = "those that loath, or cannot digest their Meat, those that have weak Stomachs, or sower belchings, or continual rising in their Stomach"
Q0 = "It helpeth those that loath, or cannot digest their Meat, those that have weak Stomachs, or sower belchings, or continual rising in their Stomach, using it familiarly either green or dry; either the Herb, the Root, or the Flowers in Broth drunk"
Q1 = Q0 + ", or Meat, or made into Conserve, Syrup, Water Electuary, or Pouder"
DEC_W = "The Decoction therof made in Wine and taken"
P["culpeper-1652:herbal:wood-betony:008"] = [
    R("That it preserveth the Lives and Bodies of Men free from the danger of Epidemical Diseases, and from Wicchcrafts also", B,
      "preserveth the Lives and Bodies of Men free from the danger of Epidemical Diseases, and from Wicchcrafts also"),
    R(Q0, B, STOM, solvent=("other",), form="drink", ev={"solvent": "in Broth drunk", "form": "in Broth drunk"}),
    R(Q0 + ", or Meat", B, STOM, form="other", ev={"form": "in Broth drunk, or Meat"}),
    R(Q1, B, STOM, process="other", form="other", ev={"process": "made into Conserve, Syrup", "form": "made into Conserve, Syrup"}),
    R(Q1, B, STOM, solvent=("water",), ev={"solvent": "Water Electuary"}),
    R(Q1, B, STOM, process="powder", ev={"process": "or Pouder as every one may best frame themselvs unto"}),
    R("It helpeth the Jaundice, Falling-sickness, the Palsie, Convulsions or shrinking of the Sinews, the Gout, and those that are inclined to Dropsies, those that have continual Pains in their Head, although it turn to Phrensie.",
      B, "the Jaundice, Falling-sickness, the Palsie, Convulsions or shrinking of the Sinews, the Gout, and those that are inclined to Dropsies, those that have continual Pains in their Head, although it turn to Phrensie"),
    R("The Pouder mixed with pure Honey is no less available for al sorts of Coughs or Colds, Wheesing or shortness of Breath, Distillations of thin Rhewm upon the Lungues, which causeth Consumptions",
      B, "al sorts of Coughs or Colds, Wheesing or shortness of Breath, Distillations of thin Rhewm upon the Lungues, which causeth Consumptions",
      solvent=("honey",), process="powder", ev={"solvent": "mixed with pure Honey", "process": "The Pouder mixed with pure Honey"}),
    R("The Decoction made with Mead and a little Penyroyal, is good for those that are troubled with putrid Agues, whether Quotidian, Tertian, or Quartan, and to draw down and evacuate the Blood and humors that by falling into the Eyes do hinder the Sight",
      B, "putrid Agues, whether Quotidian, Tertian, or Quartan, and to draw down and evacuate the Blood and humors that by falling into the Eyes do hinder the Sight",
      rtype="compound", ingredients=[(B, "unknown", "principal", "plant"), ("Penyroyal", "unknown", "co_ingredient", "plant")],
      solvent=("other",), heat="boiled", process="decoction",
      ev={"solvent": "made with Mead", "heat": "The Decoction made with Mead", "process": "The Decoction made with Mead"}),
    R(DEC_W + ", killeth the Worms in the Belly, openeth Obstructions both of the Spleen and Liver, careth Stitches and Pains in the Back, or Sides the Torments and griping pains of the Bowels, and the wind Chollick",
      B, "killeth the Worms in the Belly, openeth Obstructions both of the Spleen and Liver, careth Stitches and Pains in the Back, or Sides the Torments and griping pains of the Bowels, and the wind Chollick",
      solvent=("wine",), heat="boiled", process="decoction", form="drink",
      ev={"solvent": "made in Wine", "heat": DEC_W, "process": DEC_W, "form": DEC_W}),
    R("and mixed with Honey purgeth the Belly, helpeth to bring down Womens Courses, and is of especial use for those that are troubled with the falling down of the Mother, and pains therof and causeth an easie and speedy delivery of Women in Childbirth: it helpeth also to break and expel the Stone either in the Bladder or Kidneys",
      B, "purgeth the Belly, helpeth to bring down Womens Courses, and is of especial use for those that are troubled with the falling down of the Mother, and pains therof and causeth an easie and speedy delivery of Women in Childbirth: it helpeth also to break and expel the Stone either in the Bladder or Kidneys",
      solvent=("wine", "honey"), heat="boiled", process="decoction", form="drink",
      ev={"solvent": ["made in Wine", "mixed with Honey"], "heat": DEC_W, "process": DEC_W, "form": DEC_W}),
    R("The Decoction with Wine gargled in the Mouth, easeth the Toothach.", B, "easeth the Toothach", solvent=("wine",), heat="boiled",
      process="decoction", form="gargle",
      ev={"solvent": "The Decoction with Wine", "heat": "The Decoction with Wine", "process": "The Decoction with Wine", "form": "gargled in the Mouth"}),
    R("It is commended against the sting or biting or Venemous Serpents or Mad Dogs.", B, "the sting or biting or Venemous Serpents or Mad Dogs"),
    R("A dram of the Pouder in Betony taken with a little Honey in some Vinegar, doth wonderfully refresh those that are overwearied by travail; it staieth bleedings at the Mouth or Nose, and helpeth those that pise or spit Blood, and those that are Bursten or have a Rupture, and is good for such as are bruised by any fall or otherwise",
      B, "refresh those that are overwearied by travail; it staieth bleedings at the Mouth or Nose, and helpeth those that pise or spit Blood, and those that are Bursten or have a Rupture, and is good for such as are bruised by any fall or otherwise",
      solvent=("honey", "vinegar"), process="powder", form="drink", filt="no",
      ev={"solvent": "taken with a little Honey in some Vinegar", "process": "A dram of the Pouder", "form": "taken with a little Honey in some Vinegar",
          "filtered": "A dram of the Pouder in Betony taken with a little Honey in some Vinegar"}),
    R("The green Herb bruised, or the Juyce applied to any inward hurt or outward green Wound in the Head or Body wil quickly heal and close it up; as also any Veins or Sinews that are cut; and will draw forth any broken Bone, or Splinter, Thorn or other thing gotten into the Flesh",
      B, "any inward hurt or outward green Wound in the Head or Body wil quickly heal and close it up; as also any Veins or Sinews that are cut; and will draw forth any broken Bone, or Splinter, Thorn or other thing gotten into the Flesh",
      fod="fresh", heat="cold", process="other", form="poultice", filt="not_applicable",
      ev={"freshOrDried": "The green Herb bruised", "heat": "The green Herb bruised", "process": "The green Herb bruised",
          "form": "The green Herb bruised", "filtered": "The green Herb bruised"}),
    R("The green Herb bruised, or the Juyce applied to any inward hurt or outward green Wound in the Head or Body wil quickly heal and close it up; as also any Veins or Sinews that are cut; and will draw forth any broken Bone, or Splinter, Thorn or other thing gotten into the Flesh",
      B, "any inward hurt or outward green Wound in the Head or Body wil quickly heal and close it up; as also any Veins or Sinews that are cut; and will draw forth any broken Bone, or Splinter, Thorn or other thing gotten into the Flesh",
      part="juice", heat="cold", form="other", ev={"part": "the Juyce applied", "heat": "the Juyce applied", "form": "the Juyce applied"}),
    R("It is no less profitable for old Sores, or filthy Ulcers, yea, though they be Fistulaus and hollow", B,
      "old Sores, or filthy Ulcers, yea, though they be Fistulaus and hollow"),
    R("Being applied with a little Hogs Lard, it helpeth a Plague-Sore, and other Boyls and Pushes", B, "a Plague-Sore, and other Boyls and Pushes",
      solvent=("other",), ev={"solvent": "applied with a little Hogs Lard"}),
    R("The fumes of the Decoction while it is warm received by a Funnel into the Bars, caseth the pains of them, destroyeth the Worms, and cureth the running Sores in them",
      B, "caseth the pains of them, destroyeth the Worms, and cureth the running Sores in them", heat="boiled", heatText="while it is warm",
      process="decoction", form="inhalation", filt="not_applicable",
      ev={"heat": "The fumes of the Decoction", "process": "The fumes of the Decoction", "form": "The fumes of the Decoction while it is warm received by a Funnel",
          "filtered": "The fumes of the Decoction"}),
    R("The Juyce dropped into them doth the same.", B, "doth the same", part="juice", heat="cold", form="other",
      ev={"part": "The Juyce dropped into them", "heat": "The Juyce dropped into them", "form": "The Juyce dropped into them"}),
]
C = "Caraway"
P["culpeper-1652:herbal:caraway:008"] = [
    R("Caraway Seed hath a moderat sharp quality wherby it breaketh Wind and provoketh Urin", C, "breaketh Wind and provoketh Urin", part="seed",
      ev={"part": "Caraway Seed"}),
    R("Caraway Seed hath a moderat sharp quality wherby it breaketh Wind and provoketh Urin, which also the Herb doth", C, "breaketh Wind and provoketh Urin"),
    R("The Root is better food than the Parsnep, and is pleasant & comfortable to the Stomach, helping digestion", C,
      "pleasant & comfortable to the Stomach, helping digestion", part="root", form="other",
      ev={"part": "The Root is better food", "form": "The Root is better food than the Parsnep"}),
    R("The Seed is conducing to all the cold griefs of Head and Stomach, the Bowels or Mother, as also the wind in them, and helpeth to sharpen the Eye-sight",
      C, "all the cold griefs of Head and Stomach, the Bowels or Mother, as also the wind in them, and helpeth to sharpen the Eye-sight", part="seed",
      ev={"part": "The Seed is conducing"}),
    R("The Pouder of the Seed put into a Pultis, taketh away black and blue spots of Blows or Bruises", C, "black and blue spots of Blows or Bruises",
      rtype="unknown", part="seed", heat="cold", process="powder", form="poultice", filt="not_applicable",
      ev={"part": "The Pouder of the Seed", "heat": "The Pouder of the Seed", "process": "The Pouder of the Seed", "form": "put into a Pultis",
          "filtered": "put into a Pultis"}),
    R("The Herb it self, or with some of the Seed bruised and fryed, laid hot in a bag or double cloth to the lower part of the Belly, easeth the pains of the wind Chollick",
      C, "easeth the pains of the wind Chollick", heat="warm", heatText="fryed, laid hot", process="other", form="other", filt="not_applicable",
      ev={"heat": "bruised and fryed, laid hot", "process": "bruised and fryed", "form": "laid hot in a bag or double cloth",
          "filtered": "laid hot in a bag or double cloth"}),
]
P["culpeper-1652:herbal:caraway:009"] = [
    R("The Roots of Caraways eaten as men eat Parsnips, strengthen the Stomacks of ancient people exceedingly", "Caraways",
      "strengthen the Stomacks of ancient people exceedingly", part="root", form="other",
      ev={"part": "The Roots of Caraways", "form": "eaten as men eat Parsnips"}),
]
P["culpeper-1652:herbal:caraway:010"] = [
    R("Caraway Comfects, once only dipped in Sugar, and half a spoonful of them eaten in the morning fasting, and as many after each meal is a most admirable Remedy for such as are troubled with Wind.",
      C, "such as are troubled with Wind", rtype="compound",
      ingredients=[(C, "unknown", "principal", "plant"), ("Sugar", "unknown", "co_ingredient", "other")], process="other", form="other",
      ev={"process": "Caraway Comfects, once only dipped in Sugar", "form": "half a spoonful of them eaten"}),
]
print(write("approved", 2, P))
