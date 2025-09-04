

def bioGetRange(genus_name: str):
    if genus_name in ["$Codex_Ent_Fumerolas_Genus_Name;"]:
        return 100

    if genus_name in ["$Codex_Ent_Aleoids_Genus_Name;",
                      "$Codex_Ent_Clypeus_Genus_Name;",
                      "$Codex_Ent_Conchas_Genus_Name;",
                      "$Codex_Ent_Shrubs_Genus_Name;",
                      "$Codex_Ent_Recepta_Genus_Name;"]:
        return 150

    if genus_name in ["$Codex_Ent_Tussocks_Genus_Name;"]:
        return 200

    if genus_name in ["$Codex_Ent_Cactoid_Genus_Name;",
                      "$Codex_Ent_Fungoids_Genus_Name;"]:
        return 300

    if genus_name in ["$Codex_Ent_Bacterial_Genus_Name;",
                      "$Codex_Ent_Fonticulus_Genus_Name;",
                      "$Codex_Ent_Stratum_Genus_Name;"]:
        return 500

    if genus_name in ["$Codex_Ent_Osseus_Genus_Name;",
                      "$Codex_Ent_Tubus_Genus_Name;"]:
        return 800

    if genus_name in ["$Codex_Ent_Electricae_Genus_Name;"]:
        return 1000

    # From Horizons
    if genus_name in ["$Codex_Ent_Vents_Name;",
                      "$Codex_Ent_Sphere_Name;",
                      "$Codex_Ent_Cone_Name;",
                      "$Codex_Ent_Brancae_Name;",
                      "$Codex_Ent_Ground_Struct_Ice_Name;",
                      "$Codex_Ent_Tube_Name;"]:
        return 100

    # Odyssey Thargoid
    if genus_name in ["$Codex_Ent_Barnacles_Name;",
                      "$Codex_Ent_Thargoid_Coral_Name;",
                      "$Codex_Ent_Thargoid_Tower_Name;"]:
        return 85

    # fall back, if all else fails
    else:
        return 50

