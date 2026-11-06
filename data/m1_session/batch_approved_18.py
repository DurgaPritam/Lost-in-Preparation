from build_batch import R, write
P = {}
for pid in ("saffron:001", "saffron:002", "wormwood:001", "wormwood:003", "wormwood:004", "wormwood:005"):
    P["culpeper-1850:herbal:" + pid] = []   # intro / place / description
M = "MEADOW SWEET"
AG = "It is said to alter and take away the fits of the quartan agues, and to make a merry heart, for which purpose some use the flowers, and some the leaves."
P["culpeper-1850:herbal:queen-of-the-meadows-meadow-sweet-or-mead-sweet:004"] = [
    R("It is used to stay all manner of bleedings, fluxes, vomitings, and women’s courses, also their whites", M,
      "stay all manner of bleedings, fluxes, vomitings, and women’s courses, also their whites", heading=True),
    R(AG, M, "alter and take away the fits of the quartan agues, and to make a merry heart", heading=True, part="flower", ev={"part": "some use the flowers"}),
    R(AG, M, "alter and take away the fits of the quartan agues, and to make a merry heart", heading=True, part="leaf", ev={"part": "and some the leaves"}),
    R("It helps speedily those that are troubled with the cholic", M, "those that are troubled with the cholic", heading=True),
    R("being boiled in wine, and with a little honey, taken warm, it opens the belly", M, "it opens the belly", heading=True, solvent=("wine", "honey"),
      heat="boiled", heatText="taken warm", process="decoction", form="drink",
      ev={"solvent": ["being boiled in wine", "with a little honey"], "heat": "being boiled in wine", "process": "being boiled in wine",
          "form": "with a little honey, taken warm"}),
    R("but boiled in red wine, and drank, it stays the flux of the belly", M, "stays the flux of the belly", heading=True, solvent=("wine",), heat="boiled",
      process="decoction", form="drink",
      ev={"solvent": "boiled in red wine", "heat": "boiled in red wine", "process": "boiled in red wine, and drank", "form": "boiled in red wine, and drank"}),
    R("Outwardly applied, it helps old ulcers that are cankerous, or hollow fistulous, for which it is by many much commended, as also for the sores in the mouth or secret parts.",
      M, "old ulcers that are cankerous, or hollow fistulous, for which it is by many much commended, as also for the sores in the mouth or secret parts",
      heading=True),
    R("The water thereof helps the heat and inflammation in the eyes.", M, "the heat and inflammation in the eyes", heading=True, solvent=("water",),
      ev={"solvent": "The water thereof"}),
]   # leaves raising blisters: an effect reported from Tragus, not a use
S = "Saffron"
P["culpeper-1850:herbal:saffron:003"] = [
    R("you need not demand a reason why it strengthens the heart so exceedingly", S, "strengthens the heart so exceedingly"),
    R("It quickens the brain, for the Sun is exalted in Aries, as he hath his house in Leo. It helps consumptions of the lungs, and difficulty of breathing. It is excellent in epidemical diseases, as pestilence, small-pox, and measles. It is a notable expulsive medicine, and a notable remedy for the yellow jaundice.",
      S, "It quickens the brain, for the Sun is exalted in Aries, as he hath his house in Leo. It helps consumptions of the lungs, and difficulty of breathing. It is excellent in epidemical diseases, as pestilence, small-pox, and measles. It is a notable expulsive medicine, and a notable remedy for the yellow jaundice"),
    R("the roots of all crocus, both white and yellow, purge phlegm as hermodactyls do", "crocus", "purge phlegm", part="root", ev={"part": "the roots of all crocus"}),
]   # dose limit (ten grains) is not a use
P["culpeper-1850:herbal:wormwood:002"] = [
    R("The seed of this Wormwood is that which women usually give their children for the worms.", "Sea Wormwood", "for the worms", part="seed",
      ev={"part": "The seed of this Wormwood"}),
    R("The seeds of the common Wormwood are far more prevalent than the seed of this, to expel worms in children, or people of ripe age", "common Wormwood",
      "to expel worms in children, or people of ripe age", part="seed", ev={"part": "The seeds of the common Wormwood"}),
    R("if the liver be weak, and cannot make blood enough, I would have said, Sanguify, if I had written only to scholars, the Seriphian, which is the weakest of Wormwoods, is better than the best",
      "Seriphian", "if the liver be weak, and cannot make blood enough"),
]
P["culpeper-1850:herbal:wormwood:006"] = [
    R("It may be so called, because it is good for a stinking breath", "Roman Wormwood", "a stinking breath"),
]
print(write("approved", 18, P))
