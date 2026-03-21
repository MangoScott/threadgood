import json
import os

with open("data/reports/tommy-hilfiger.json", "r") as f:
    data = json.load(f)

# Downgrade Tommy Hilfiger metrics
data["analysis"]["where"]["oar_participation"] = "no"
data["analysis"]["where"]["supply_chain_tiers_disclosed"] = "1"
data["analysis"]["who"]["living_wage_status"] = "not_disclosed"
data["analysis"]["who"]["audit_results_disclosed"] = "no"
data["analysis"]["what"]["sustainable_materials_percentage"] = "20%"
data["analysis"]["what"]["certifications_mentioned"] = []
data["analysis"]["after"]["circularity_goals"] = "no"
data["analysis"]["after"]["takeback_program"] = "no"

with open("data/reports/tommy-hilfiger.json", "w") as f:
    json.dump(data, f, indent=2)

with open("data/fti/tommy-hilfiger.json", "r") as f:
    fti = json.load(f)
fti["transparency_score"] = 55.0  # PVH is around 55
with open("data/fti/tommy-hilfiger.json", "w") as f:
    json.dump(fti, f, indent=2)

print("Tommy Hilfiger downgraded successfully!")
