from build_batch import R, write
P = {}
for pid in ("wormwood:007", "wormwood:008", "wormwood:009", "wormwood:011", "wormwood:012", "wormwood:013", "wormwood:015"):
    P["culpeper-1850:herbal:" + pid] = []   # description / place / time / verse / commentary
W = "Wormwood"
P["culpeper-1850:herbal:wormwood:010"] = [
    R("It remedies the evils choler can inflict on the body of man by sympathy. It helps the evils Venus and the wanton Boy produce, by antipathy; and it doth something else besides. It cleanses the body of choler (who dares say Mars doth no good?) It provokes urine, helps surfeits, or swellings in the belly; it causes appetite to meat, because Mars rules the attractive faculty in man: The sun never shone upon a better herb for the yellow jaundice than this",
      W, "the evils choler can inflict on the body of man by sympathy. It helps the evils Venus and the wanton Boy produce, by antipathy; and it doth something else besides. It cleanses the body of choler (who dares say Mars doth no good?) It provokes urine, helps surfeits, or swellings in the belly; it causes appetite to meat, because Mars rules the attractive faculty in man: The sun never shone upon a better herb for the yellow jaundice"),
    R("Take of the flowers of Wormwood, Rosemary, and Black Thorn, of each a like quantity, half that quantity of saffron; boil this in Rhenish wine, but put it not in saffron till it is almost boiled; This is the way to keep a man’s body in health",
      W, "to keep a man’s body in health", rtype="compound",
      ingredients=[(W, "flower", "principal", "plant"), ("Rosemary", "flower", "co_ingredient", "plant"), ("Black Thorn", "flower", "co_ingredient", "plant"),
                   ("saffron", "unknown", "co_ingredient", "plant")],
      part="flower", solvent=("wine",), heat="boiled", process="decoction",
      ev={"part": "the flowers of Wormwood", "solvent": "boil this in Rhenish wine", "heat": "boil this in Rhenish wine", "process": "boil this in Rhenish wine"}),
    R("Besides all this, Wormwood provokes the terms.", W, "provokes the terms"),
    R("Wormwood being an herb of Mars, is a present remedy for the biting of rats and mice.", W, "the biting of rats and mice"),
    R("if any have poisoned himself by eating them, Wormwood, an herb of Mars, cures him", W, "poisoned himself by eating them"),
    R("Wheals, pushes, black and blue spots, coming either by bruises or beatings. Wormwood, an herb of Mars, helps", W,
      "Wheals, pushes, black and blue spots, coming either by bruises or beatings"),
    R("Mars eradicates all diseases in the throat by his herbs (for wormwood is one)", W, "all diseases in the throat"),
    R("Suppose a man be bitten or stung by a martial creature, imagine a wasp, a hornet, a scorpion, Wormwood, an herb of Mars, gives you a present cure",
      W, "bitten or stung by a martial creature, imagine a wasp, a hornet, a scorpion"),
    R("Astrologers think Mars causes scabs and itch, and the virgins are angry with him, because wanton Venus told them he deforms their skins; but, quoth Mars, my only desire is, they should know themselves; my herb Wormwood will restore them to the beauty they formerly had",
      W, "scabs and itch"),
    R("they say he causes the cholic (it is well God hath set some body to pull down the pride of man.) He in the Virgin troubles none with the cholic, but them that know not themselves (for who knows himself, may easily know all the world.) Wormwood, an herb of Mars, is a present cure for it",
      W, "the cholic"),
    R("the poor old man lies crying out of his left side. Father Saturn’s angry, Mars comes to him; Come, brother, I confess thou art evil spoken of, and so am I; thou knowest I have my exaltation in thy house, I give him an herb of mine, Wormwood, to cure the old man",
      W, "lies crying out of his left side"),
]   # moths, ink against mice: household uses; the eye and 'ill humours' passages name no condition
P["culpeper-1850:herbal:wormwood:014"] = [
    R("children are much troubled with the worms; she desired a medicine of him, he bid her take his own herb, Wormwood", W, "children are much troubled with the worms"),
    R("I’ll give thee antipathetical cure; Take my herb Wormwood, and thou shall never get a surfeit by drinking", W, "thou shall never get a surfeit by drinking"),
    R("A poor silly countryman hath got an ague, and cannot go about his business: he wishes he had it not, and so do I; but I will tell him a remedy, whereby he shall prevent it; Take the herb of Mars, Wormwood",
      W, "an ague"),
    R("though sometimes a man gets a stinking breath, and yet Jupiter is a fortune, forsooth; up comes Mars to him; Come brother Jupiter, thou knowest I sent thee a couple of trines to thy house last night, the one from Aries, and the other from Scorpio; give me thy leave by sympathy to cure this poor man with drinking a draught of Wormwood beer every morning",
      W, "a stinking breath", solvent=("other",), form="drink",
      ev={"solvent": "a draught of Wormwood beer", "form": "with drinking a draught of Wormwood beer"}),
    R("she gave a man two terrible mischiefs, a dull brain and a weak sight; Mars laid by his sword, and comes to her; Sister Moon, said he, this man hath angered thee, but I beseech thee take notice he is but a fool; prithee be patient, I will with my herb wormwood cure him of both infirmities",
      W, "a dull brain and a weak sight"),
]   # "an antivenerean medicine was the best against the pox": no plant named
CO = "colocynthis"
P["pliny-nh:b20:c008:001"] = [
    R("Employed by itself when dried, it acts as a very powerful purgative", CO, "a very powerful purgative", fod="dried", solvent=("none",),
      ev={"freshOrDried": "when dried", "solvent": "Employed by itself"}),
    R("used as an injection, it is a remedy for all diseases of the intestines, the kidneys, and the loins, as well as for paralysis. The seed being first removed, it is boiled down in hydromel to one half; after which it is used as an injection",
      CO, "all diseases of the intestines, the kidneys, and the loins, as well as for paralysis", part="fruit", solvent=("water", "honey"), heat="boiled",
      dur="boiled down in hydromel to one half", process="decoction", form="other",
      ev={"part": "The seed being first removed", "solvent": "boiled down in hydromel", "heat": "boiled down in hydromel to one half",
          "process": "boiled down in hydromel to one half", "form": "used as an injection"}),
    R("It is good, too, for the stomach, taken in pills composed of the dried powder and boiled honey.", CO, "for the stomach", fod="dried",
      solvent=("honey",), process="powder", form="other",
      ev={"freshOrDried": "the dried powder", "solvent": "boiled honey", "process": "the dried powder", "form": "taken in pills"}),
    R("In jaundice seven seeds of it may be taken with beneficial effects, with a draught of hydromel immediately after.", CO, "jaundice", part="seed",
      solvent=("water", "honey"), ev={"part": "seven seeds of it", "solvent": "a draught of hydromel"}),
]
print(write("approved", 19, P))
