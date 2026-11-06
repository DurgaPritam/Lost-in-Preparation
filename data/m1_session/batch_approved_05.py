from build_batch import R, write
P = {}
CV = "cleavers-or-goosgrass"
for pid in ("clary:010", f"{CV}:002", f"{CV}:004", f"{CV}:006", "henbane:002", "henbane:004", "henbane:006"):
    P["culpeper-1652:herbal:" + pid] = []   # comment / description / place / time
P["culpeper-1652:herbal:clary:011"] = [
    R("We will grant that Clary strengthens the Back", "Clary", "strengthens the Back"),
]
C = "Cleavers"
P[f"culpeper-1652:herbal:{CV}:008"] = [
    R("The Juyce of the Herb, and Seed together taken in Wine, helpeth those that are bitten with an Adder, by preserving the Heart from the Venom",
      C, "those that are bitten with an Adder, by preserving the Heart from the Venom", heading=True, part="other", solvent=("wine",), form="drink",
      ev={"part": "The Juyce of the Herb, and Seed together", "solvent": "taken in Wine", "form": "taken in Wine"}),
    R("It is familiarly taken in Broth to keep them lean; and lank that are apt to grow fat", C, "to keep them lean; and lank that are apt to grow fat",
      heading=True, solvent=("other",), form="drink", ev={"solvent": "taken in Broth", "form": "taken in Broth"}),
    R("The distilled Water drunk twice a day helpeth the yellow Jaundice", C, "the yellow Jaundice", heading=True, solvent=("water",), heat="boiled",
      process="distillation", form="drink",
      ev={"solvent": "The distilled Water", "heat": "The distilled Water", "process": "The distilled Water", "form": "The distilled Water drunk"}),
    R("the Decoction of the Herb in experience found to do the same, and stayeth Lasks and Bloody Fluxes", C,
      "to do the same, and stayeth Lasks and Bloody Fluxes", heading=True, heat="boiled", process="decoction",
      ev={"heat": "the Decoction of the Herb", "process": "the Decoction of the Herb"}),
    R("The Juyce of the Leavs, or they a little bruisep and applied to any bleeding wound, stayeth the Bleeding", C,
      "any bleeding wound, stayeth the Bleeding", heading=True, part="juice", heat="cold",
      ev={"part": "The Juyce of the Leavs", "heat": "The Juyce of the Leavs"}),
    R("The Juyce of the Leavs, or they a little bruisep and applied to any bleeding wound, stayeth the Bleeding", C,
      "any bleeding wound, stayeth the Bleeding", heading=True, part="leaf", heat="cold", process="other", form="poultice", filt="not_applicable",
      ev={"part": "The Juyce of the Leavs, or they a little bruisep", "heat": "a little bruisep and applied", "process": "a little bruisep and applied",
          "form": "a little bruisep and applied to any bleeding wound", "filtered": "a little bruisep and applied"}),
    R("The Juyce is also very good to close up the Lips of green Wounds", C, "to close up the Lips of green Wounds", heading=True, part="juice",
      heat="cold", ev={"part": "The Juyce is also very good", "heat": "The Juyce is also very good"}),
    R("the Pouder of the dried Herb strewed therupon doth the same, and likewise helpeth old Ulcers", C, "doth the same, and likewise helpeth old Ulcers",
      heading=True, fod="dried", solvent=("none",), heat="cold", process="powder",
      ev={"freshOrDried": "the dried Herb", "solvent": "the Pouder of the dried Herb strewed therupon", "heat": "the Pouder of the dried Herb",
          "process": "the Pouder of the dried Herb"}),
    R("Being boyled with Hogs Greas, it healeth al sorts of hard Swellings or Kernels in the Throat, being anointed therwith", C,
      "al sorts of hard Swellings or Kernels in the Throat", heading=True, solvent=("other",), heat="boiled", process="other", form="ointment",
      filt="not_applicable",
      ev={"solvent": "Being boyled with Hogs Greas", "heat": "Being boyled with Hogs Greas", "process": "Being boyled with Hogs Greas",
          "form": "being anointed therwith", "filtered": "being anointed therwith"}),
    R("The Juyce dropped into the Ears taketh away the pains of them.", C, "taketh away the pains of them", heading=True, part="juice", heat="cold",
      form="other", ev={"part": "The Juyce dropped into the Ears", "heat": "The Juyce dropped into the Ears", "form": "The Juyce dropped into the Ears"}),
]
P[f"culpeper-1652:herbal:{CV}:009"] = [
    R("It is a good remedy in the Spring, eaten (being first chopped smal and boyled well) in Water-gruel, to clens the Blood, and strengthen the Liver, thereby keeping the Body in health, and fitting it for that change of Season that is coming",
      C, "to clens the Blood, and strengthen the Liver, thereby keeping the Body in health, and fitting it for that change of Season that is coming",
      heading=True, solvent=("other",), heat="boiled", form="other",
      ev={"solvent": "in Water-gruel", "heat": "being first chopped smal and boyled well", "form": "eaten (being first chopped smal and boyled well)"}),
]
print(write("approved", 5, P))
