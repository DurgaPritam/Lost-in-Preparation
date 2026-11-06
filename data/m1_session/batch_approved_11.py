from build_batch import R, write
P = {}
for pid in ("agrimony:001", "agrimony:002", "agrimony:003", "agrimony:009", "wood-betony:001"):
    P["culpeper-1850:herbal:" + pid] = []   # description / place / time / commentary
A = "AGRIMONY"
G = "must needs be good for the gout, either used outwardly in oil or ointment"
P["culpeper-1850:herbal:agrimony:004"] = [
    R(G, A, "the gout", heading=True, solvent=("oil",), form="ointment", filt="not_applicable",
      ev={"solvent": "used outwardly in oil or ointment", "form": "in oil or ointment", "filtered": "used outwardly in oil or ointment"}),
    R(G + ", or inwardly in an electuary, or syrup", A, "the gout", heading=True, process="other", form="other",
      ev={"process": "inwardly in an electuary, or syrup", "form": "inwardly in an electuary"}),
    R(G + ", or inwardly in an electuary, or syrup, or concerted juice", A, "the gout", heading=True, part="juice", process="other",
      ev={"part": "concerted juice", "process": "concerted juice"}),
]
P["culpeper-1850:herbal:agrimony:005"] = [
    R("It opens and cleanses the liver, helps the jaundice, and is very beneficial to the bowels, healing all inward wounds, bruises, hurts, and other distempers.",
      A, "opens and cleanses the liver, helps the jaundice, and is very beneficial to the bowels, healing all inward wounds, bruises, hurts, and other distempers",
      heading=True),
    R("The decoction of the herb made with wine, and drank, is good against the biting and stinging of serpents, and helps them that make foul, troubled or bloody water.",
      A, "the biting and stinging of serpents, and helps them that make foul, troubled or bloody water", heading=True, solvent=("wine",), heat="boiled",
      process="decoction", form="drink",
      ev={"solvent": "made with wine", "heat": "The decoction of the herb", "process": "The decoction of the herb", "form": "made with wine, and drank"}),
]
P["culpeper-1850:herbal:agrimony:006"] = [
    R("This herb also helps the cholic, cleanses the breast, and rids away the cough.", A, "helps the cholic, cleanses the breast, and rids away the cough",
      heading=True),
    R("A draught of the decoction taken warm before the fit, first removes, and in time rids away the tertian or quartan agues.", A,
      "the tertian or quartan agues", heading=True, heat="boiled", heatText="taken warm", process="decoction", form="drink",
      ev={"heat": "A draught of the decoction taken warm", "process": "A draught of the decoction", "form": "A draught of the decoction"}),
    R("The leaves and seeds taken in wine, stays the bloody flux", A, "stays the bloody flux", heading=True, part="other", solvent=("wine",),
      form="drink", ev={"part": "The leaves and seeds", "solvent": "taken in wine", "form": "taken in wine"}),
    R("outwardly applied, being stamped with old swine’s grease, it helps old sores, cancers, and inveterate ulcers, and draws forth thorns and splinters of wood, nails, or any other such things gotten in the flesh",
      A, "old sores, cancers, and inveterate ulcers, and draws forth thorns and splinters of wood, nails, or any other such things gotten in the flesh",
      heading=True, solvent=("other",), process="other", ev={"solvent": "stamped with old swine’s grease", "process": "being stamped with old swine’s grease"}),
    R("It helps to strengthen the members that be out of joint", A, "strengthen the members that be out of joint", heading=True),
    R("being bruised and applied, or the juice dropped in it, helps foul and imposthumed ears", A, "foul and imposthumed ears", heading=True,
      heat="cold", process="other", form="poultice", filt="not_applicable",
      ev={"heat": "being bruised and applied", "process": "being bruised and applied", "form": "being bruised and applied", "filtered": "being bruised and applied"}),
    R("being bruised and applied, or the juice dropped in it, helps foul and imposthumed ears", A, "foul and imposthumed ears", heading=True,
      part="juice", heat="cold", form="other",
      ev={"part": "the juice dropped in it", "heat": "the juice dropped in it", "form": "the juice dropped in it"}),
]
P["culpeper-1850:herbal:agrimony:007"] = [
    R("The distilled water of the herb is good to all the said purposes, either inward or outward, but a great deal weaker.", A,
      "good to all the said purposes", heading=True, solvent=("water",), heat="boiled", process="distillation",
      ev={"solvent": "The distilled water of the herb", "heat": "The distilled water", "process": "The distilled water"}),
]
P["culpeper-1850:herbal:agrimony:008"] = [
    R("It is a most admirable remedy for such whose livers are annoyed either by heat or cold.", "Agrimony", "such whose livers are annoyed either by heat or cold"),
]
print(write("approved", 11, P))
