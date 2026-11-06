from build_batch import R, write
P = {}
BR = "Briony"
P["culpeper-1850:dispensatory:s006-roots:025"] = [
    R("Of Briony both white and black: they are both hot and dry, some say in the third degree, and some say but in the first; they purge flegm and watery humours, but they trouble the stomach much, they are very good for dropsies",
      BR, "purge flegm and watery humours, but they trouble the stomach much, they are very good for dropsies"),
    R("the white is most in use, and is good for the fits of the mother", BR, "the fits of the mother"),
    R("both of them externally used, take away freckles, sunburning, and morphew from the face, and cleanse filthy ulcers", BR,
      "take away freckles, sunburning, and morphew from the face, and cleanse filthy ulcers", form="other", ev={"form": "externally used"}),
]
CE = "Centaury"
ql = "The less is a present remedy for the yellow jaundice, opens stoppings of the liver, gall, and spleen: purges choler, helps gout, clears the sight, purgeth the stomach, helps the dropsy and green sickness. It is only the tops and flowers which are useful, of which you may take a dram inwardly in powder, or half a handful boiled in posset-drink at a time"
il = "the yellow jaundice, opens stoppings of the liver, gall, and spleen: purges choler, helps gout, clears the sight, purgeth the stomach, helps the dropsy and green sickness"
P["culpeper-1850:dispensatory:s009-herbs-and-their-leaves:070"] = [
    R("Centaury the greater and less. They say the greater will do wonders in curing wounds", CE, "curing wounds"),
    R(ql, CE, il, part="other", heat="cold", process="powder",
      ev={"part": "the tops and flowers", "heat": "take a dram inwardly in powder", "process": "in powder"}),
    R(ql, CE, il, part="other", solvent=("other",), heat="boiled", process="decoction", form="drink",
      ev={"part": "the tops and flowers", "solvent": "boiled in posset-drink", "heat": "boiled in posset-drink", "process": "boiled in posset-drink",
          "form": "posset-drink"}),
]
P["culpeper-1850:dispensatory:s009-herbs-and-their-leaves:222"] = [
    R("Fleabane; hot and dry in the third degree, helps the biting of venomous beasts, wounds and swellings, the yellow jaundice, the falling sickness, and such as cannot make water",
      "Fleabane", "the biting of venomous beasts, wounds and swellings, the yellow jaundice, the falling sickness, and such as cannot make water"),
]   # the smoke killing gnats and fleas is a household use, not a health indication
P["culpeper-1850:dispensatory:s025-herbs:010"] = []   # names by degree, no use
P["culpeper-1850:dispensatory:s030-simple-distilled-waters:084"] = [
    R("Scabious water helps pleurises and pains, and pricking in the sides; Aposthumes, coughs, pestilences, and straitness of the breast", "Scabious",
      "pleurises and pains, and pricking in the sides; Aposthumes, coughs, pestilences, and straitness of the breast", solvent=("water",),
      ev={"solvent": "Scabious water"}),
]
P["culpeper-1850:dispensatory:s030-simple-distilled-waters:092"] = [
    R("The water of Marigold flowers is appropriated to most cold diseases of the head, eyes, and stomach", "Marigold",
      "most cold diseases of the head, eyes, and stomach", part="flower", solvent=("water",),
      ev={"part": "Marigold flowers", "solvent": "The water of Marigold flowers"}),
]
P["culpeper-1850:dispensatory:s034-physical-vinegars:003"] = []   # title only
P["culpeper-1850:dispensatory:s039-syrups-made-with-vinegar-and-honey:013"] = []   # preparation without an indication in the passage
P["culpeper-1850:dispensatory:s045-species-or-powders:099"] = []   # indication only by reference to a title; no plant named
P["culpeper-1850:dispensatory:s055-ointments-more-compound:049"] = []   # preparation without an indication
print(write("sample", 3, P))
