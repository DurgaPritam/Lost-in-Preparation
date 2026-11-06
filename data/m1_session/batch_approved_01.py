from build_batch import R, write
P = {}
AG = "Agrimony"
for pid in ("agrimony:002", "agrimony:004", "agrimony:006", "agrimony:012", "wood-betony:002", "wood-betony:004"):
    P["culpeper-1652:herbal:" + pid] = []   # description / place / time / commentary: no use
P["culpeper-1652:herbal:agrimony:008"] = [
    R("It openeth and clenseth the Liver, helpeth the Jaundice, and is very beneficial to the Bowels, healing all inward Wounds, Bruises, Hurts, and other distempers",
      AG, "openeth and clenseth the Liver, helpeth the Jaundice, and is very beneficial to the Bowels, healing all inward Wounds, Bruises, Hurts, and other distempers",
      heading=True),
    R("The Decoction of the Herb made with Wine and drunk is good against the stinging and biting of Serpents, and helps them that have foul, troubled, or bloody waters, and makes them piss cleer spedily; It also helpeth the Chollick, clenseth the Breast, and rids away the Cough",
      AG, "the stinging and biting of Serpents, and helps them that have foul, troubled, or bloody waters, and makes them piss cleer spedily; It also helpeth the Chollick, clenseth the Breast, and rids away the Cough",
      heading=True, solvent=("wine",), heat="boiled", process="decoction", form="drink",
      ev={"solvent": "made with Wine", "heat": "The Decoction of the Herb", "process": "The Decoction of the Herb", "form": "made with Wine and drunk"}),
    R("A draught of the Decoction taken warm before the Fit, first removes, and in time rids away the Tertian or Quartan Agues", AG,
      "the Tertian or Quartan Agues", heading=True, solvent=("wine",), heat="boiled", heatText="taken warm", process="decoction", form="drink",
      ev={"solvent": "The Decoction of the Herb made with Wine", "heat": "A draught of the Decoction taken warm", "process": "A draught of the Decoction",
          "form": "A draught of the Decoction"}),
    R("The Leaves and Seed taken in Wine, Stayeth the Bloody Flu", AG, "Stayeth the Bloody Flu", heading=True,
      ingredients=[(AG, "other", "principal", "plant")], part="other", solvent=("wine",), form="drink",
      ev={"part": "The Leaves and Seed", "solvent": "taken in Wine", "form": "taken in Wine"}),
    R("being stamped with old Swines grease, it helpeth old sores, Cancers, and inveterate Ulcers; and draweth forth Thorns, Splinters of Wood, Nails, or any other such thing gotten into the Flesh; it helpeth to strengthen the Members that be out of joynt",
      AG, "it helpeth old sores, Cancers, and inveterate Ulcers; and draweth forth Thorns, Splinters of Wood, Nails, or any other such thing gotten into the Flesh; it helpeth to strengthen the Members that be out of joynt",
      heading=True, solvent=("other",), process="other",
      ev={"solvent": "stamped with old Swines grease", "process": "being stamped with old Swines grease"}),
    R("being bruised and applied, or the Juyce dropped in, it helpeth foul and imposthu⟦?⟧ned Ears", AG, "foul and imposthu⟦?⟧ned Ears", heading=True,
      heat="cold", process="other", form="poultice", filt="not_applicable",
      ev={"heat": "being bruised and applied", "process": "being bruised and applied", "form": "being bruised and applied",
          "filtered": "being bruised and applied"}),
    R("being bruised and applied, or the Juyce dropped in, it helpeth foul and imposthu⟦?⟧ned Ears", AG, "foul and imposthu⟦?⟧ned Ears", heading=True,
      ingredients=[(AG, "juice", "principal", "plant")], part="juice", heat="cold", form="other",
      ev={"part": "the Juyce dropped in", "heat": "the Juyce dropped in", "form": "the Juyce dropped in"}),
]
P["culpeper-1652:herbal:agrimony:009"] = [
    R("The distilled Water of the Herb is good to all the said purposes, either inward or outward, but a great deal weaker.", AG,
      "good to all the said purposes", heading=True, solvent=("water",), heat="boiled", process="distillation",
      ev={"solvent": "The distilled Water of the Herb", "heat": "The distilled Water", "process": "The distilled Water"}),
]
P["culpeper-1652:herbal:agrimony:010"] = [
    R("must needs be good for the Gout, either used ⟦?⟧outwardly in an Oyl or Oyntment", AG, "the Gout", heading=True, solvent=("oil",),
      form="ointment", filt="not_applicable",
      ev={"solvent": "in an Oyl or Oyntment", "form": "in an Oyl or Oyntment", "filtered": "in an Oyl or Oyntment"}),
    R("must needs be good for the Gout, either used ⟦?⟧outwardly in an Oyl or Oyntment, or inwardly in an Electuary or Syrup", AG, "the Gout",
      heading=True, process="other", form="other", ev={"process": "inwardly in an Electuary or Syrup", "form": "inwardly in an Electuary"}),
    R("must needs be good for the Gout, either used ⟦?⟧outwardly in an Oyl or Oyntment, or inwardly in an Electuary or Syrup, or concreated Juyce",
      AG, "the Gout", heading=True, ingredients=[(AG, "juice", "principal", "plant")], part="juice", process="other",
      ev={"part": "concreated Juyce", "process": "concreated Juyce"}),
]
P["culpeper-1652:herbal:agrimony:011"] = [
    R("It is a most admirable remedy for such whole Livers are annoyed either by heat or cold.", AG,
      "such whole Livers are annoyed either by heat or cold", heading=True),
]
print(write("approved", 1, P))
