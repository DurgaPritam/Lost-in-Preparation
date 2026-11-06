from build_batch import R, write
P = {}
for pid in ("celandine:004", "celandine:006", "celandine:010", "celandine:011", "celandine:012", "celandine:013",
            "the-iesser-celondine-usually-known-by-the-name-of-pilewort:001"):
    P["culpeper-1652:herbal:" + pid] = []   # place / time / argument against corrosive eye medicines / name origin / intro
CE = "Celandine"
P["culpeper-1652:herbal:celandine:008"] = [
    R("The herb or Roots boyled in white-Wine and drunk, a few Aniseeds being boyled therwith, openeth Obstructions of the Liver and Gall, helpeth the yellow Jaundice: and the often using it, helps the Dropsie, and the Itch, and those that have old Sores in their Legs, or other parts of the Body",
      CE, "openeth Obstructions of the Liver and Gall, helpeth the yellow Jaundice: and the often using it, helps the Dropsie, and the Itch, and those that have old Sores in their Legs, or other parts of the Body",
      heading=True, rtype="compound", ingredients=[(CE, "unknown", "principal", "plant"), ("Aniseeds", "seed", "co_ingredient", "plant")],
      solvent=("wine",), heat="boiled", process="decoction", form="drink",
      ev={"solvent": "boyled in white-Wine", "heat": "boyled in white-Wine", "process": "boyled in white-Wine and drunk", "form": "boyled in white-Wine and drunk",
          "recipeType": "a few Aniseeds being boyled therwith"}),
    R("The Juyce thereof taken fasting, is held to be of singular good use against the Pestilence", CE, "the Pestilence", heading=True,
      part="juice", solvent=("none",), heat="cold", form="drink",
      ev={"part": "The Juyce thereof", "solvent": "The Juyce thereof taken fasting", "heat": "The Juyce thereof taken fasting",
          "form": "The Juyce thereof taken fasting"}),
    R("The distilled Water, with a little Sugar, and a little good Triacle mixed therwith (the party upon the taking being laid down to sweat a little) hath the same effect",
      CE, "hath the same effect", heading=True, rtype="compound",
      ingredients=[(CE, "unknown", "principal", "plant"), ("Sugar", "unknown", "co_ingredient", "other"), ("Triacle", "unknown", "co_ingredient", "other")],
      solvent=("water",), heat="boiled", process="distillation",
      ev={"solvent": "The distilled Water", "heat": "The distilled Water", "process": "The distilled Water"}),
    R("The Juyce dropped into the Eyes clenseth them from Films and cloudiness which darken the sight, but it is best to allay the sharpnes of the Juyce with a little Breast-milk",
      CE, "clenseth them from Films and cloudiness which darken the sight", heading=True, part="juice", solvent=("other",), heat="cold", form="other",
      ev={"part": "The Juyce dropped into the Eyes", "solvent": "allay the sharpnes of the Juyce with a little Breast-milk",
          "heat": "The Juyce dropped into the Eyes", "form": "The Juyce dropped into the Eyes"}),
    R("It is good in old filthy corroding creeping Ulcers whersoever, to stay their malignity of fretting and running, and to cause them to heal the more speedily",
      CE, "old filthy corroding creeping Ulcers whersoever, to stay their malignity of fretting and running, and to cause them to heal the more speedily",
      heading=True),
    R("The Juyce often applied to Tetters, Ring worms, or other such like spreading Cancers, will quickly heal them, and rubbed often upon Warts will take them away",
      CE, "Tetters, Ring worms, or other such like spreading Cancers, will quickly heal them, and rubbed often upon Warts will take them away",
      heading=True, part="juice", heat="cold", form="other",
      ev={"part": "The Juyce often applied", "heat": "The Juyce often applied", "form": "The Juyce often applied"}),
    R("The Herb with the Roots bruised and heated with Oyl of Camomel, and applied to the Navel, taketh away the griping pain in the Belly and Bowels, and all the pains of the Mother: and applied to Womens Breasts stayeth the overmuch flowing of their Courses",
      CE, "taketh away the griping pain in the Belly and Bowels, and all the pains of the Mother: and applied to Womens Breasts stayeth the overmuch flowing of their Courses",
      heading=True, part="other", solvent=("oil",), heat="warm", heatText="heated", process="other", form="poultice", filt="not_applicable",
      ev={"part": "The Herb with the Roots", "solvent": "heated with Oyl of Camomel", "heat": "bruised and heated", "process": "bruised and heated",
          "form": "applied to the Navel", "filtered": "bruised and heated with Oyl of Camomel, and applied"}),
    R("The Juyce Decoction of the Herb gargled between the Teeth that ake, easeth the pain", CE, "the Teeth that ake, easeth the pain", heading=True,
      heat="boiled", process="decoction", form="gargle",
      ev={"heat": "Decoction of the Herb", "process": "Decoction of the Herb", "form": "gargled between the Teeth"}),
    R("the Pouder of the dryed Root, laid upon an aching hollow, or loos Tooth, wil caus it to fal out", CE,
      "an aching hollow, or loos Tooth, wil caus it to fal out", heading=True, part="root", fod="dried", solvent=("none",), heat="cold",
      process="powder",
      ev={"part": "the Pouder of the dryed Root", "freshOrDried": "the dryed Root", "solvent": "laid upon an aching hollow",
          "heat": "the Pouder of the dryed Root", "process": "the Pouder of the dryed Root"}),
    R("The Juyce mixed with som Pouder of Brimstone, is not only good against the Itch, but taketh away al discolourings of the Skin whatsoever",
      CE, "the Itch, but taketh away al discolourings of the Skin whatsoever", heading=True, rtype="compound",
      ingredients=[(CE, "juice", "principal", "plant"), ("Brimstone", "unknown", "co_ingredient", "mineral")], part="juice", heat="cold",
      ev={"part": "The Juyce mixed with som Pouder of Brimstone", "heat": "The Juyce mixed with som Pouder of Brimstone"}),
]   # the vinegar bath helps an itching CAUSED by the juice: not a use of the plant
P["culpeper-1652:herbal:celandine:009"] = [
    R("then may you make it into an Oyl or Oyntment which you please to anoint your sore Eyes withal", CE, "sore Eyes", heading=True,
      solvent=("oil",), form="ointment", filt="not_applicable",
      ev={"solvent": "make it into an Oyl or Oyntment", "form": "anoint your sore Eyes", "filtered": "make it into an Oyl or Oyntment"}),
]
P["culpeper-1652:herbal:celandine:014"] = [
    R("the Herb being gathered as I shewed before, and the Elements drawn apart from it by the art of the Alchyraist; and after they are drawn apart, rectified, the earthy quality still in rectifying them, added to the Terra damnata (as Alchymists call it) or Terra sacratissima (as som Phylosophers call it) the Elements so rectified are sufficient for the Cure of al Diseases",
      CE, "the Cure of al Diseases", heading=True, process="other",
      ev={"process": "the Elements drawn apart from it by the art of the Alchyraist"}),
]
print(write("approved", 3, P))
