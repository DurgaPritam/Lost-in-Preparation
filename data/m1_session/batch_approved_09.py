from build_batch import R, write
P = {}
for pid in (f"queen-of-the-meadows-meadow-sweet-or-mead-sweet:010", "saffron:001", "saffron:003", "wormwood:002", "wormwood:003",
            "wormwood:006", "wormwood:008", "wormwood:009"):
    P["culpeper-1652:herbal:" + pid] = []   # astrology / intro / place / description / names
S = "Saffron"
P["culpeper-1652:herbal:saffron:005"] = [
    R("you need not demand a reason why it strengthens the heart so exceedingly", S, "strengthens the heart so exceedingly", heading=True),
    R("It quicken the Brain, for the Sun is exalted in V as well as he hath his House in SL it help Consumption of the Lungs, help difficulty of breathing: it is an excellent thing in Epidemical Diseases, as Pestilences, smal Pox, and Measles: It is a notable expulsive Medicine, and a notable Remedy for the yellow Jaundice",
      S, "It quicken the Brain, for the Sun is exalted in V as well as he hath his House in SL it help Consumption of the Lungs, help difficulty of breathing: it is an excellent thing in Epidemical Diseases, as Pestilences, smal Pox, and Measles: It is a notable expulsive Medicine, and a notable Remedy for the yellow Jaundice",
      heading=True),
    R("the Roots of all Crocus both white and yellow purge Flegm as Hermodactils do", "Crocus", "purge Flegm", part="root",
      ev={"part": "the Roots of all Crocus"}),
]   # "Let not abov ten grains be given at one time": a dose limit, not a use
P["culpeper-1652:herbal:wormwood:004"] = [
    R("The Seed of this Wormwood is that which usually Women give their Children for the Worms", "Seriphium", "for the Worms", part="seed",
      ev={"part": "The Seed of this Wormwood"}),
    R("The Seeds of the common Wormwood are far more prevalent than the Seed of this, to expell Worms in Children, or People of ripe age",
      "common Wormwood", "to expell Worms in Children, or People of ripe age", part="seed", ev={"part": "The Seeds of the common Wormwood"}),
    R("If the Liver be weak and cannot make Blood enonough (I would have said [Sanguifie] if I had written only to Schollers) The Seriphian which is the weakest of Wormwoods is better than the best",
      "Seriphian", "If the Liver be weak and cannot make Blood enonough"),
]   # the principal of this paragraph is Sea Wormwood (Seriphium), recorded under the names as written
print(write("approved", 9, P))
