from build_batch import R, write
P = {}
SA = "Sanicle"
qt = "It doth wonderfully help those that have any Tumors in any part of their Bodies, for it represseth and dissipateth the Humors, if the Decoction or Juyce thereof be taken, or the Pouder in drink, and the Juyce used outwardly"
it = "those that have any Tumors in any part of their Bodies"
qg = "For there is not found any Herb that can give such present help either to Man or Beast when the Disease falleth upon the Lungs or Throat, and to heal up all the putrid Malignant Ulcers in the Mouth, Throat, and Privities, by gargling or washing with the Decoction of the Leavs and Root, made in Water, and a little Honey put thereto"
ig = "the Disease falleth upon the Lungs or Throat, and to heal up all the putrid Malignant Ulcers in the Mouth, Throat, and Privities"
P["culpeper-1652:herbal:sanicle:008"] = [
    R("It is exceeding good to heal all green Wounds speedily, or any Ulcers, Impostumes, or bleedings inwardly", SA,
      "to heal all green Wounds speedily, or any Ulcers, Impostumes, or bleedings inwardly", heading=True),
    R(qt, SA, it, heading=True, heat="boiled", process="decoction", form="drink",
      ev={"heat": "the Decoction", "process": "the Decoction", "form": "if the Decoction or Juyce thereof be taken"}),
    R(qt, SA, it, heading=True, part="juice", heat="cold", process="expression", form="drink",
      ev={"part": "Juyce thereof", "heat": "Juyce thereof", "process": "Juyce thereof", "form": "if the Decoction or Juyce thereof be taken"}),
    R(qt, SA, it, heading=True, heat="cold", filt="no", process="powder", form="drink",
      ev={"heat": "the Pouder in drink", "filtered": "the Pouder in drink", "process": "the Pouder", "form": "the Pouder in drink"}),
    R(qt, SA, it, heading=True, part="juice", heat="cold", process="expression", form="other",
      ev={"part": "the Juyce used outwardly", "heat": "the Juyce used outwardly", "process": "the Juyce used outwardly", "form": "used outwardly"}),
    R(qg, SA, ig, heading=True, part="other", solvent=("water", "honey"), heat="boiled", process="decoction", form="gargle",
      ev={"part": "the Leavs and Root", "solvent": ["made in Water", "a little Honey put thereto"], "heat": "the Decoction of the Leavs and Root",
          "process": "the Decoction of the Leavs and Root", "form": "by gargling"}),
    R(qg, SA, ig, heading=True, part="other", solvent=("water", "honey"), heat="boiled", process="decoction", form="other",
      ev={"part": "the Leavs and Root", "solvent": ["made in Water", "a little Honey put thereto"], "heat": "the Decoction of the Leavs and Root",
          "process": "the Decoction of the Leavs and Root", "form": "washing with the Decoction"}),
    R("It helpeth to stay Womens Courses, and all other Fluxes of Blood either by the Mouth, Urine or Stool, and Lasks of the Belly, the Ulceration of the Kidneys also, and the pains in the Bowels, and the Gonorrhea or running of the Reins, being boyled in Wine or Water, and drunk",
      SA, "to stay Womens Courses, and all other Fluxes of Blood either by the Mouth, Urine or Stool, and Lasks of the Belly, the Ulceration of the Kidneys also, and the pains in the Bowels, and the Gonorrhea or running of the Reins",
      heading=True, solvent=("wine", "water"), heat="boiled", process="decoction", form="drink",
      ev={"solvent": "being boyled in Wine or Water", "heat": "being boyled", "process": "boyled in Wine or Water", "form": "and drunk"}),
    R("The same also is no less powerful to help any Ruptures or Burstings, used both inwardly and outwardly", SA, "any Ruptures or Burstings", heading=True),
]
SO = "Sorrel"
P["culpeper-1652:herbal:sorrel:003"] = [
    R("Sorrel is prevalent in all hot Diseases, to cool any Inflamation and heat of Blood in Agues Pestilential or Chollerick, or other sicknesses and sainting, rising from heat, and to refresh the overspent Spirits with the violence of furious or fiery fits of Agues, to quench Thirst, and procure an Appetite in fainting or decayd Stomachs",
      SO, "all hot Diseases, to cool any Inflamation and heat of Blood in Agues Pestilential or Chollerick, or other sicknesses and sainting, rising from heat, and to refresh the overspent Spirits with the violence of furious or fiery fits of Agues, to quench Thirst, and procure an Appetite in fainting or decayd Stomachs"),
    R("the Seed doth more effectually being more drying and binding, and thereby stayeth the hot Fluxes of Womens Courses, or of Humors in the Bloody Flux, or Flux of the Stomach",
      SO, "stayeth the hot Fluxes of Womens Courses, or of Humors in the Bloody Flux, or Flux of the Stomach", heading=True, part="seed", ev={"part": "the Seed"}),
    R("Both Roots and Seed as well as the Herb is held powerful to resist the poyson of the Scorpion", SO, "to resist the poyson of the Scorpion",
      heading=True, part="other", ev={"part": "Both Roots and Seed as well as the Herb"}),
    R("The Decoction of the Roots is taken to help the Jaundice, and to expel Gravel and the Stone in the Reins or Kidneys", SO,
      "to help the Jaundice, and to expel Gravel and the Stone in the Reins or Kidneys", heading=True, part="root", heat="boiled", process="decoction",
      form="drink", ev={"part": "The Decoction of the Roots", "heat": "The Decoction", "process": "The Decoction of the Roots", "form": "is taken"}),
    R("The Decoction of the Flowers made with Wine and drunk helpeth the black Jaundice, as also the inward Ulcers of the Body or Bowels", SO,
      "the black Jaundice, as also the inward Ulcers of the Body or Bowels", heading=True, part="flower", solvent=("wine",), heat="boiled",
      process="decoction", form="drink", ev={"part": "The Decoction of the Flowers", "solvent": "made with Wine", "heat": "The Decoction of the Flowers",
                                            "process": "The Decoction of the Flowers", "form": "made with Wine and drunk"}),
    R("A Syrup made with the Juyce of Sorrel and Fumitary is a Soveraign help to kill those sharp Humors that cause the Itch", SO,
      "to kill those sharp Humors that cause the Itch", rtype="compound",
      ingredients=[(SO, "juice", "principal", "plant"), ("Fumitary", "juice", "co_ingredient", "plant")], part="juice", process="other",
      ev={"part": "the Juyce of Sorrel", "process": "A Syrup made with the Juyce"}),
    R("The Juyce thereof with a little Vinegar serveth well to be used outwardly for the same cause, and is also profitable for Tetters, Ringworms", SO,
      "Tetters, Ringworms", heading=True, part="juice", solvent=("vinegar",), heat="cold", process="expression", form="other",
      ev={"part": "The Juyce thereof", "solvent": "with a little Vinegar", "heat": "The Juyce thereof", "process": "The Juyce thereof",
          "form": "used outwardly"}),
    R("It helpeth also to discuss the Kernels in the Throat", SO, "to discuss the Kernels in the Throat", heading=True),
    R("the Juyce gargled in the Mouth helpeth the Sores therein", SO, "the Sores therein", heading=True, part="juice", heat="cold",
      process="expression", form="gargle", ev={"part": "the Juyce gargled", "heat": "the Juyce gargled", "process": "the Juyce gargled",
                                               "form": "gargled in the Mouth"}),
    R("The Leaves wrapped up in a Colewoort Leaf, and roasted under the Embers, and applied to a hard Impostume, Botch, Boyl, or Plague Sore, both ripeneth and breaketh it",
      SO, "a hard Impostume, Botch, Boyl, or Plague Sore, both ripeneth and breaketh it", heading=True, rtype="compound",
      ingredients=[(SO, "leaf", "principal", "plant"), ("Colewoort", "leaf", "co_ingredient", "plant")], part="leaf", heat="warm",
      heatText="roasted under the Embers", filt="not_applicable", process="other", form="poultice",
      ev={"part": "The Leaves wrapped up", "heat": "roasted under the Embers", "filtered": "applied to a hard Impostume",
          "process": "roasted under the Embers", "form": "applied to a hard Impostume"}),
]
BB = "Butter-Bur"
P["culpeper-1652:herbal:the-butter-bur:006"] = [
    R("The Roots hereof are by long experience found to be very available against the Plague and Pestilential Feavers, by provoking Sweat, if the Pouder therof be taken in Wine",
      BB, "the Plague and Pestilential Feavers", heading=True, part="root", solvent=("wine",), heat="cold", filt="no", process="powder", form="drink",
      ev={"part": "The Roots hereof", "solvent": "taken in Wine", "heat": "the Pouder therof be taken in Wine", "filtered": "the Pouder therof be taken in Wine",
          "process": "the Pouder therof", "form": "taken in Wine"}),
    R("The Root hereof taken with Zedoàry and Angelica, or without them, helps the rising of the Mother", BB, "the rising of the Mother", heading=True,
      rtype="compound", ingredients=[(BB, "root", "principal", "plant"), ("Zedoàry", "unknown", "co_ingredient", "plant"),
                                     ("Angelica", "unknown", "co_ingredient", "plant")], part="root", ev={"part": "The Root hereof"}),
    R("The Root hereof taken with Zedoàry and Angelica, or without them, helps the rising of the Mother", BB, "the rising of the Mother", heading=True,
      part="root", ev={"part": "The Root hereof"}),
    R("The Decoction of the Root in Wine is singular good for those that wheeze much, or are short-winded", BB, "those that wheeze much, or are short-winded",
      heading=True, part="root", solvent=("wine",), heat="boiled", process="decoction",
      ev={"part": "The Decoction of the Root", "solvent": "in Wine", "heat": "The Decoction of the Root", "process": "The Decoction of the Root in Wine"}),
    R("It provoketh Urin also and Womens courses, and killeth the flat and broad Worms in the Belly", BB,
      "provoketh Urin also and Womens courses, and killeth the flat and broad Worms in the Belly", heading=True),
    R("The Pouder of the Root doth wonderfully help to dry up the moisture of sores that are hard to be cured, and taketh away all spots and blemishes of the skin",
      BB, "to dry up the moisture of sores that are hard to be cured, and taketh away all spots and blemishes of the skin", heading=True, part="root",
      heat="cold", process="powder", ev={"part": "The Pouder of the Root", "heat": "The Pouder of the Root", "process": "The Pouder of the Root"}),
]
MU = "Mulberry"
P["culpeper-1652:herbal:the-mulberry-tree:005"] = [
    R("the ripe Berries by reason of their Sweetness and slippery moisture, opening the Belly", MU, "opening the Belly", part="fruit", ev={"part": "the ripe Berries"}),
    R("the unripe binding it, especially when they are dried, and then they are good to stay Fluxes, Lasks, and the abundance of Womens Courses", MU,
      "to stay Fluxes, Lasks, and the abundance of Womens Courses", part="fruit", fod="dried", ev={"part": "the ripe Berries", "freshOrDried": "when they are dried"}),
    R("The Bark of the Root killeth the broad Worms in the Body", MU, "killeth the broad Worms in the Body", part="bark", ev={"part": "The Bark of the Root"}),
    R("The Juyce, or the Syrup made of the Juyce of the Berries, helpeth all Inflamations and Sores in the Mouth or Throat, and the Pallet of the Mouth when it is fallen down",
      MU, "all Inflamations and Sores in the Mouth or Throat, and the Pallet of the Mouth when it is fallen down", part="juice", heat="cold",
      process="expression", ev={"part": "the Juyce of the Berries", "heat": "The Juyce", "process": "The Juyce"}),
    R("The Juyce, or the Syrup made of the Juyce of the Berries, helpeth all Inflamations and Sores in the Mouth or Throat, and the Pallet of the Mouth when it is fallen down",
      MU, "all Inflamations and Sores in the Mouth or Throat, and the Pallet of the Mouth when it is fallen down", part="juice", process="other",
      ev={"part": "the Juyce of the Berries", "process": "the Syrup made of the Juyce"}),
    R("The Juyce of the Leavs is a Remedy against the biting of Serpents, and for those that have taken Aconite", MU,
      "the biting of Serpents, and for those that have taken Aconite", part="juice", heat="cold", process="expression",
      ev={"part": "The Juyce of the Leavs", "heat": "The Juyce of the Leavs", "process": "The Juyce of the Leavs"}),
    R("The Leavs beaten with Vinegar is good to lay on any place that is burnt with fire", MU, "any place that is burnt with fire", part="leaf",
      solvent=("vinegar",), heat="cold", filt="not_applicable", process="other", form="poultice",
      ev={"part": "The Leavs beaten", "solvent": "beaten with Vinegar", "heat": "The Leavs beaten with Vinegar", "filtered": "to lay on any place",
          "process": "The Leavs beaten", "form": "to lay on any place"}),
    R("A Decoction made of the Bark and Leavs, is good to wash the Mouth and Teeth when they ach", MU, "the Mouth and Teeth when they ach", part="other",
      heat="boiled", process="decoction", form="gargle",
      ev={"part": "the Bark and Leavs", "heat": "A Decoction", "process": "A Decoction made of the Bark and Leavs", "form": "to wash the Mouth and Teeth"}),
    R("it will give out a certain Juyce, which being hardned, the next day is of good use to help the Toothach, to dissolve Knots, and purge the Belly", MU,
      "to help the Toothach, to dissolve Knots, and purge the Belly", part="juice", process="other",
      ev={"part": "a certain Juyce", "process": "which being hardned"}),
    R("The Leavs of Mulberries are said to stay bleeding at Mouth or Nose, or the Bleeding of the Piles, or of a Wound being bound unto the places", MU,
      "to stay bleeding at Mouth or Nose, or the Bleeding of the Piles, or of a Wound", part="leaf", solvent=("none",), filt="not_applicable", form="poultice",
      ev={"part": "The Leavs of Mulberries", "solvent": "being bound unto the places", "filtered": "being bound unto the places", "form": "being bound unto the places"}),
    R("A Branch of the Tree taken when the Moon is at the full and bound to the Wrist of a Womans Arm whose Courses come down too much doth stay them in a short space",
      MU, "a Womans Arm whose Courses come down too much doth stay them", part="stem", solvent=("none",), filt="not_applicable", form="other",
      ev={"part": "A Branch of the Tree", "solvent": "bound to the Wrist", "filtered": "bound to the Wrist", "form": "bound to the Wrist of a Womans Arm"}),
]
SC = "Sea Colewort"
P["culpeper-1652:herbal:the-sea-colewort:008"] = [
    R("The Broth or first Decoction of the Sea Colewort doth by the sharp nitrous and bitter qualities therin, open the Belly and purge the Body", SC,
      "open the Belly and purge the Body", heat="boiled", process="decoction", ev={"heat": "first Decoction", "process": "first Decoction"}),
    R("The Seed herof bruised and drunk, killeth Worms", SC, "killeth Worms", part="seed", heat="cold", filt="no", process="other", form="drink",
      ev={"part": "The Seed herof", "heat": "The Seed herof bruised", "filtered": "bruised and drunk", "process": "bruised", "form": "bruised and drunk"}),
    R("The Leavs or the Juyce of them applied to Sores or Ulcers clenseth and healeth them, and dissolveth Swellings, and taketh away Inflamations", SC,
      "Sores or Ulcers clenseth and healeth them, and dissolveth Swellings, and taketh away Inflamations", part="leaf", filt="not_applicable", form="poultice",
      ev={"part": "The Leavs", "filtered": "applied to Sores or Ulcers", "form": "applied to Sores or Ulcers"}),
    R("The Leavs or the Juyce of them applied to Sores or Ulcers clenseth and healeth them, and dissolveth Swellings, and taketh away Inflamations", SC,
      "Sores or Ulcers clenseth and healeth them, and dissolveth Swellings, and taketh away Inflamations", part="juice", heat="cold", process="expression",
      form="other", ev={"part": "the Juyce of them", "heat": "the Juyce of them", "process": "the Juyce of them", "form": "applied to Sores or Ulcers"}),
]
PA = "Pansies"
qv = "It is said also to soder green Wounds, and to help old Sores, the Juyce or distilled Water thereof being drunk"
P["culpeper-1652:herbal:violets:006"] = [
    R("It is conducing in like manner as Violets to the hot Diseases of the Chest and Lungs: for Agues, Convulsions, and Falling-sickness in Children", PA,
      "the hot Diseases of the Chest and Lungs: for Agues, Convulsions, and Falling-sickness in Children"),
    R("The Decoction helpeth Itch and Scabs being bathed therwith", PA, "Itch and Scabs", heat="boiled", process="decoction", form="other",
      ev={"heat": "The Decoction", "process": "The Decoction", "form": "being bathed therwith"}),
    R(qv, PA, "to soder green Wounds, and to help old Sores", part="juice", solvent=("none",), heat="cold", process="expression", form="drink",
      ev={"part": "the Juyce", "solvent": "the Juyce or distilled Water thereof being drunk", "heat": "the Juyce", "process": "the Juyce", "form": "being drunk"}),
    R(qv, PA, "to soder green Wounds, and to help old Sores", solvent=("water",), heat="boiled", process="distillation", form="drink",
      ev={"solvent": "distilled Water", "heat": "distilled Water", "process": "distilled Water", "form": "being drunk"}),
]
WB = "Water-Betony"
P["culpeper-1652:herbal:water-betony:008"] = [
    R("the Leavs bruised and applied are effectual for all old and filthy Ulcers", WB, "all old and filthy Ulcers", heading=True, part="leaf",
      solvent=("none",), heat="cold", filt="not_applicable", process="other", form="poultice",
      ev={"part": "the Leavs bruised", "solvent": "the Leavs bruised and applied", "heat": "the Leavs bruised", "filtered": "bruised and applied",
          "process": "the Leavs bruised", "form": "bruised and applied"}),
    R("the Leavs bruised and applied are effectual for all old and filthy Ulcers; and especially if the Juyce of the Leavs be boyled with a little Honey, and tents dipped therin, and the Sores dressed therwith",
      WB, "all old and filthy Ulcers", heading=True, part="juice", solvent=("honey",), heat="boiled", process="other", form="other",
      ev={"part": "the Juyce of the Leavs", "solvent": "boyled with a little Honey", "heat": "be boyled", "process": "boyled with a little Honey",
          "form": "tents dipped therin, and the Sores dressed therwith"}),
    R("The distilled water of the Leaves is used for the same purposes; as also to bath the Face or Hands spotted or blemished, or discolored by Sunburning",
      WB, "the Face or Hands spotted or blemished, or discolored by Sunburning", heading=True, part="leaf", solvent=("water",), heat="boiled",
      process="distillation", form="other", ev={"part": "The distilled water of the Leaves", "solvent": "The distilled water", "heat": "The distilled water",
                                               "process": "The distilled water", "form": "to bath the Face or Hands"}),
]
WO = "Woad"
P["culpeper-1652:herbal:woad:008"] = [
    R("An Oyntment made thereof stancheth Bleeding", WO, "stancheth Bleeding", heading=True, filt="not_applicable", form="ointment",
      ev={"filtered": "An Oyntment", "form": "An Oyntment made thereof"}),
    R("A Plaister made thereof and applied to the Region of the Spleen (and I pray you take notice, that the Spleen lies on the left side) takes away the hardness and pains thereof",
      WO, "takes away the hardness and pains thereof", heading=True, filt="not_applicable", form="plaster",
      ev={"filtered": "A Plaister", "form": "A Plaister made thereof and applied"}),
    R("The Oyntment is excellent good in such Ulcers as abound with moisture, and takes away the corroding and fretting Humors: It cools Inflamations, quencheth St. Anthonies fire, and stayeth Defluxions of Blood to any part of the Body",
      WO, "such Ulcers as abound with moisture, and takes away the corroding and fretting Humors: It cools Inflamations, quencheth St. Anthonies fire, and stayeth Defluxions of Blood to any part of the Body",
      heading=True, filt="not_applicable", form="ointment", ev={"filtered": "The Oyntment", "form": "The Oyntment"}),
]
P["culpeper-1652:herbal:wood-betony:010"] = []   # astrology only
P["culpeper-1652:herbal:wormwood:020"] = []      # verse, no use
print(write("sample", 2, P))
