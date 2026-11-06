from build_batch import R, write
P = {}
for pid in ("wormwood:012", "wormwood:014", "wormwood:016", "wormwood:019", "wormwood:021", "wormwood:022", "wormwood:024"):
    P["culpeper-1652:herbal:" + pid] = []   # description / place / time / verse / commentary
W = "Wormwood"
P["culpeper-1652:herbal:wormwood:010"] = [
    R("It may be it was so called because 'tis special good for a stinking Brcarh", "Romane Wormwood", "a stinking Brcarh"),
]
P["culpeper-1652:herbal:wormwood:018"] = [
    R("It remedies the evils Choller can inflict on the Body of man by Sympathy. It helps the evils Venus and her wanton Girls produce, by Antipathy; and it doth somthing else besides; It clenseth the Body of Choller (and who dares say Mars doth no good?) It provokes Urine, helps Surfets, Swellings in the Belly; it causeth an Appetite to meat, because Mars rules the Attractive faculty in Man: The Sun never shone upon a better Herb for the yellow Jaundice than this is",
      W, "the evils Choller can inflict on the Body of man by Sympathy. It helps the evils Venus and her wanton Girls produce, by Antipathy; and it doth somthing else besides; It clenseth the Body of Choller (and who dares say Mars doth no good?) It provokes Urine, helps Surfets, Swellings in the Belly; it causeth an Appetite to meat, because Mars rules the Attractive faculty in Man: The Sun never shone upon a better Herb for the yellow Jaundice"),
    R("Take of the Flowers of Wormwood, Rosemary, and black Thorn, of each a like quantity, half that quantity of saffron, boyl this in Renish Wine, but put not in the Saffron till it is almost boyled; This is the way to keep a Mans Body in health",
      W, "to keep a Mans Body in health", rtype="compound",
      ingredients=[(W, "flower", "principal", "plant"), ("Rosemary", "flower", "co_ingredient", "plant"), ("black Thorn", "flower", "co_ingredient", "plant"),
                   ("saffron", "unknown", "co_ingredient", "plant")],
      part="flower", solvent=("wine",), heat="boiled", process="decoction",
      ev={"part": "the Flowers of Wormwood", "solvent": "boyl this in Renish Wine", "heat": "boyl this in Renish Wine", "process": "boyl this in Renish Wine"}),
    R("Besides all this, Wormwood provokes the Terms.", W, "provokes the Terms"),
    R("Wormwood being an Herb of Mars is a present Remedy for the biting of Rats and Mice.", W, "the biting of Rats and Mice"),
    R("if any have poyson'd himself by eating them, Wormwood an Herb of Mars cures him", W, "poyson'd himself by eating them"),
    R("Wheals, Pushes black & blew Spots coming eitheir by bruises or beatings, Wormwood an Herb of Mars helps", W,
      "Wheals, Pushes black & blew Spots coming eitheir by bruises or beatings"),
    R("Mars eradicates all Diseases in the Throat by his Herbs (of which Wormwood is one)", W, "all Diseases in the Throat"),
    R("Suppose a man be bitten or s⟦?⟧ung by a martial Creature, imagine a Wasp, a Hornet or Scorpion, Wormwood an H⟦??⟧b of Mars gives you a present cure",
      W, "bitten or s⟦?⟧ung by a martial Creature, imagine a Wasp, a Hornet or Scorpion"),
    R("Astrologers say Mars causeth Scabs and Itch, and the Virgins are angry with him, because wanton V⟦?⟧nus told them he desorms their Skin: But quoth Mars, my only desire is they should know themselves; my Herb Wormwood will restore them to the beauty they formerly had",
      W, "Scabs and Itch"),
    R("they say he usually causeth the Chollick ('tis well God hath set some body to pul down the pride of Man) He in the Virgin troubles none wth the Chollick but them that know not themselves (for who knows himself may easily know all the world:) Wormwood an Herb of Mars is a present cure for it",
      W, "the Chollick"),
    R("The poor old man lies crying cut of his left side, Father Sarwn's angry, Mars comes to him, come Bic⟦??⟧er, I confess thou an evil spoken of, and so am I th⟦?⟧ knowest I have my exaltation in thy House, I'le give him an Herb of mine, Wormwood, to cure t⟦??⟧ poor man",
      W, "crying cut of his left side"),
]   # moths among clothes and ink against mice: household uses; the eye and 'ill Humors' passages name no condition
P["culpeper-1652:herbal:wormwood:023"] = [
    R("Children are much troubled with the Worms, she desued a Medicine of him, he bad her take his own Herb Wormwood", W, "Children are much troubled with the Worms"),
    R("I'le give thee an Antipathetical Cure, take my Herb Wormwood, thou shalt never get a Surfet by drinking", W, "thou shalt never get a Surfet by drinking"),
    R("A poor silly Countryman hath got an Ague and cannot go about his business, he wishes he had it not, and so do I, but I'le tell him a Remedy whereby he may prevent it. Take the Herb of Mars Wormwood",
      W, "an Ague"),
    R("yet a man somtimes gets a stinking breath, and yet Jupiter is a Fortune forsooth; up comes Mars to him, Come Brother Jupiter, thou knowest I sent thee a couple of Trines to thy Houses last night, the one from Aries, and the other from Scorpio, give me thy leave by Sympathy to cure the poor man by drinking a draught of Wormwood Beer every morning",
      W, "a stinking breath", solvent=("other",), form="drink",
      ev={"solvent": "a draught of Wormwood Beer", "form": "by drinking a draught of Wormwood Beer"}),
    R("she gave a man two terrible mischiefs, a dull Brain, and a weak sight, Mars l⟦?⟧ies by his Sword and comes to her, Sister Moon saith he, This man hath anger'd thee, but I beseech thee take notice he is but a Fool, prithee be patient, I will with my Herb Wormwood cure him of both Infirmities",
      W, "a dull Brain, and a weak sight"),
]   # "an Antivenerial Medicine was the best against the Pox": no plant named
print(write("approved", 10, P))
