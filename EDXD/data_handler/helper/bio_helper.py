
def bio_get_range(genus_name: str) -> int:
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
        return 10000

# ---------------------------------------------------------------------------
# Mapping Bridge (Localised Name -> Codex Key)
# ---------------------------------------------------------------------------
SPECIES_TO_CODEX = {
    # Aleoida
    "Aleoida Arcus": "$Codex_Ent_Aleoids_Genus_Name;",
    "Aleoida Coronamus": "$Codex_Ent_Aleoids_Genus_Name;",
    "Aleoida Gravis": "$Codex_Ent_Aleoids_Genus_Name;",
    "Aleoida Laminiae": "$Codex_Ent_Aleoids_Genus_Name;",
    "Aleoida Spica": "$Codex_Ent_Aleoids_Genus_Name;",

    # Amphora Plant (Shrubs)
    "Amphora Plant": "$Codex_Ent_Shrubs_Genus_Name;",

    # Anemone (Clypeus)
    "Blatteum Bioluminescent Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Croceum Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Luteolum Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Prasinum Bioluminescent Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Puniceum Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Roseum Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Roseum Bioluminescent Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Rubeum Bioluminescent Anemone": "$Codex_Ent_Clypeus_Genus_Name;",

    # Bacterium
    "Bacterium Nebulus": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Acies": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Omentum": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Scopulum": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Verrata": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Bullaris": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Vesicula": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Informem": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Volu": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Alcyoneum": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Aurasus": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Cerbrus": "$Codex_Ent_Bacterial_Genus_Name;",
    "Bacterium Tela": "$Codex_Ent_Bacterial_Genus_Name;",

    # Bark Mound (Shrubs)
    "Bark Mound": "$Codex_Ent_Shrubs_Genus_Name;",

    # Brain Tree (Shrubs)
    "Brain Tree Aureum": "$Codex_Ent_Shrubs_Genus_Name;",
    "Brain Tree Gypseeum": "$Codex_Ent_Shrubs_Genus_Name;",
    "Brain Tree Lindigoticum": "$Codex_Ent_Shrubs_Genus_Name;",
    "Brain Tree Lividum": "$Codex_Ent_Shrubs_Genus_Name;",
    "Brain Tree Ostrinum": "$Codex_Ent_Shrubs_Genus_Name;",
    "Brain Tree Puniceum": "$Codex_Ent_Shrubs_Genus_Name;",
    "Brain Tree Roseum": "$Codex_Ent_Shrubs_Genus_Name;",
    "Brain Tree Viride": "$Codex_Ent_Shrubs_Genus_Name;",

    # Cactoida
    "Cactoida Cortexum": "$Codex_Ent_Cactoid_Genus_Name;",
    "Cactoida Lapis": "$Codex_Ent_Cactoid_Genus_Name;",
    "Cactoida Peperatis": "$Codex_Ent_Cactoid_Genus_Name;",
    "Cactoida Pullulanta": "$Codex_Ent_Cactoid_Genus_Name;",
    "Cactoida Vermis": "$Codex_Ent_Cactoid_Genus_Name;",

    # Clypeus
    "Clypeus Lacrimam": "$Codex_Ent_Clypeus_Genus_Name;",
    "Clypeus Margaritus": "$Codex_Ent_Clypeus_Genus_Name;",
    "Clypeus Speculumi": "$Codex_Ent_Clypeus_Genus_Name;",

    # Concha
    "Concha Aureolas": "$Codex_Ent_Conchas_Genus_Name;",
    "Concha Biconcavis": "$Codex_Ent_Conchas_Genus_Name;",
    "Concha Labiata": "$Codex_Ent_Conchas_Genus_Name;",
    "Concha Renibus": "$Codex_Ent_Conchas_Genus_Name;",

    # Crystalline Shard (Shrubs)
    "Crystalline Shard": "$Codex_Ent_Shrubs_Genus_Name;",

    # Electricae
    "Electricae Pluma": "$Codex_Ent_Electricae_Genus_Name;",
    "Electricae Radialem": "$Codex_Ent_Electricae_Genus_Name;",

    # Fonticulua
    "Fonticulua Campestris": "$Codex_Ent_Fonticulus_Genus_Name;",
    "Fonticulua Digitos": "$Codex_Ent_Fonticulus_Genus_Name;",
    "Fonticulua Fluctus": "$Codex_Ent_Fonticulus_Genus_Name;",
    "Fonticulua Lapida": "$Codex_Ent_Fonticulus_Genus_Name;",
    "Fonticulua Segmentatus": "$Codex_Ent_Fonticulus_Genus_Name;",
    "Fonticulua Upupam": "$Codex_Ent_Fonticulus_Genus_Name;",

    # Frutexa (Shrubs)
    "Frutexa Acus": "$Codex_Ent_Shrubs_Genus_Name;",
    "Frutexa Collum": "$Codex_Ent_Shrubs_Genus_Name;",
    "Frutexa Fera": "$Codex_Ent_Shrubs_Genus_Name;",
    "Frutexa Flabellum": "$Codex_Ent_Shrubs_Genus_Name;",
    "Frutexa Flammasis": "$Codex_Ent_Shrubs_Genus_Name;",
    "Frutexa Metallicum": "$Codex_Ent_Shrubs_Genus_Name;",
    "Frutexa Sponsae": "$Codex_Ent_Shrubs_Genus_Name;",

    # Fumerola
    "Fumerola Aquatis": "$Codex_Ent_Fumerolas_Genus_Name;",
    "Fumerola Carbosis": "$Codex_Ent_Fumerolas_Genus_Name;",
    "Fumerola Extremus": "$Codex_Ent_Fumerolas_Genus_Name;",
    "Fumerola Nitris": "$Codex_Ent_Fumerolas_Genus_Name;",

    # Fungoida
    "Fungoida Bullarum": "$Codex_Ent_Fungoids_Genus_Name;",
    "Fungoida Gelata": "$Codex_Ent_Fungoids_Genus_Name;",
    "Fungoida Setisis": "$Codex_Ent_Fungoids_Genus_Name;",
    "Fungoida Stabitis": "$Codex_Ent_Fungoids_Genus_Name;",

    # Osseus
    "Osseus Cornibus": "$Codex_Ent_Osseus_Genus_Name;",
    "Osseus Discus": "$Codex_Ent_Osseus_Genus_Name;",
    "Osseus Fractus": "$Codex_Ent_Osseus_Genus_Name;",
    "Osseus Pellebantus": "$Codex_Ent_Osseus_Genus_Name;",
    "Osseus Pumice": "$Codex_Ent_Osseus_Genus_Name;",
    "Osseus Spiralis": "$Codex_Ent_Osseus_Genus_Name;",

    # Recepta
    "Recepta Conditivus": "$Codex_Ent_Recepta_Genus_Name;",
    "Recepta Deltahedronix": "$Codex_Ent_Recepta_Genus_Name;",
    "Recepta Umbrux": "$Codex_Ent_Recepta_Genus_Name;",

    # Sinuous Tuber (Tubus)
    "Sinuous Tuber Albidum": "$Codex_Ent_Tubus_Genus_Name;",
    "Sinuous Tuber Blatteum": "$Codex_Ent_Tubus_Genus_Name;",
    "Sinuous Tuber Caeruleum": "$Codex_Ent_Tubus_Genus_Name;",
    "Sinuous Tuber Lindigoticum": "$Codex_Ent_Tubus_Genus_Name;",
    "Sinuous Tuber Prasinum": "$Codex_Ent_Tubus_Genus_Name;",
    "Sinuous Tuber Roseus": "$Codex_Ent_Tubus_Genus_Name;",
    "Sinuous Tuber Violaceum": "$Codex_Ent_Tubus_Genus_Name;",
    "Sinuous Tuber Viride": "$Codex_Ent_Tubus_Genus_Name;",

    # Stratum
    "Stratum Araneamus": "$Codex_Ent_Stratum_Genus_Name;",
    "Stratum Cucumisis": "$Codex_Ent_Stratum_Genus_Name;",
    "Stratum Excutitus": "$Codex_Ent_Stratum_Genus_Name;",
    "Stratum Frigus": "$Codex_Ent_Stratum_Genus_Name;",
    "Stratum Laminamus": "$Codex_Ent_Stratum_Genus_Name;",
    "Stratum Limaxus": "$Codex_Ent_Stratum_Genus_Name;",
    "Stratum Paleas": "$Codex_Ent_Stratum_Genus_Name;",
    "Stratum Tectonicas": "$Codex_Ent_Stratum_Genus_Name;",

    # Tubus
    "Tubas Cavas": "$Codex_Ent_Tubus_Genus_Name;",
    "Tubas Compagibus": "$Codex_Ent_Tubus_Genus_Name;",
    "Tubas Conifer": "$Codex_Ent_Tubus_Genus_Name;",
    "Tubas Rosarium": "$Codex_Ent_Tubus_Genus_Name;",
    "Tubas Sororibus": "$Codex_Ent_Tubus_Genus_Name;",

    # Tussock
    "Tussock Albata": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Capillum": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Caputus": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Catena": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Cultro": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Divisa": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Ignis": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Pennata": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Pennatis": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Propagito": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Serrati": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Stigmasis": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Triticum": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Ventusa": "$Codex_Ent_Tussocks_Genus_Name;",
    "Tussock Virgam": "$Codex_Ent_Tussocks_Genus_Name;",

    # Thargoid (Odyssey)
    "Thargoid Spires": "$Codex_Ent_Thargoid_Tower_Name;",
    "Thargoid Mega Barnacles": "$Codex_Ent_Barnacles_Name;",
    "Thargoid Coral Tree": "$Codex_Ent_Thargoid_Coral_Name;",
    "Thargoid Coral Root": "$Codex_Ent_Thargoid_Coral_Name;",
}

# ---------------------------------------------------------------------------
# NEW: Wrapper Function for Estimator
# ---------------------------------------------------------------------------
def get_scan_range_for_species(species_localised: str) -> int:
    """
    Bridges the gap: Localised Species Name -> Codex Key -> Range.
    """
    codex_key = SPECIES_TO_CODEX.get(species_localised)
    if not codex_key:
        # Fallback for unknown species (e.g. new DLC or typo)
        return 10000
    return bio_get_range(codex_key)

def get_genus_value(species_localised: str) -> int:
    """
    Returns the base scan value for a given species (localised name).

    Args:
        species_localised (str): The localised species name (e.g., "Concha Labiata").

    Returns:
        int: The base scan value for the species.
    """
    full_species_value_mapping = {
        # Aleoida
        "Aleoida Arcus": 7252500,
        "Aleoida Coronamus": 6284600,
        "Aleoida Gravis": 12934900,
        "Aleoida Laminiae": 3385200,
        "Aleoida Spica": 3385200,

        # Amphora Plant
        "Amphora Plant": 3626400,

        # Anemone
        "Blatteum Bioluminescent Anemone": 1499900,
        "Croceum Anemone": 3399800,
        "Luteolum Anemone": 1499900,
        "Prasinum Bioluminescent Anemone": 1499900,
        "Puniceum Anemone": 1499900,
        "Roseum Anemone": 1499900,
        "Roseum Bioluminescent Anemone": 1499900,
        "Rubeum Bioluminescent Anemone": 1499900,

        # Bacterium
        "Bacterium Nebulus": 9116600,
        "Bacterium Acies": 1000000,
        "Bacterium Omentum": 4638900,
        "Bacterium Scopulum": 8633800,
        "Bacterium Verrata": 3897000,
        "Bacterium Bullaris": 1152500,
        "Bacterium Vesicula": 1000000,
        "Bacterium Informem": 8418000,
        "Bacterium Volu": 7774700,
        "Bacterium Alcyoneum": 1658500,
        "Bacterium Aurasus": 1000000,
        "Bacterium Cerbrus": 1689800,
        "Bacterium Tela": 1949000,

        # Bark Mound
        "Bark Mound": 1471900,

        # Brain Tree
        "Brain Tree Aureum": 3565100,
        "Brain Tree Gypseeum": 3565100,
        "Brain Tree Lindigoticum": 3565100,
        "Brain Tree Lividum": 1593700,
        "Brain Tree Ostrinum": 3565100,
        "Brain Tree Puniceum": 3565100,
        "Brain Tree Roseum": 1593700,
        "Brain Tree Viride": 1593700,

        # Cactoida
        "Cactoida Cortexum": 3667600,
        "Cactoida Lapis": 2483600,
        "Cactoida Peperatis": 2483600,
        "Cactoida Pullulanta": 3667600,
        "Cactoida Vermis": 16202800,

        # Clypeus
        "Clypeus Lacrimam": 8418000,
        "Clypeus Margaritus": 11873200,
        "Clypeus Speculumi": 16202800,

        # Concha
        "Concha Aureolas": 7774700,
        "Concha Biconcavis": 16777215,
        "Concha Labiata": 2352400,
        "Concha Renibus": 4572400,

        # Crystalline Shard
        "Crystalline Shard": 3626400,

        # Electricae
        "Electricae Pluma": 6284600,
        "Electricae Radialem": 6284600,

        # Fonticulua
        "Fonticulua Campestris": 1000000,
        "Fonticulua Digitos": 1804100,
        "Fonticulua Fluctus": 16777215,
        "Fonticulua Lapida": 3111000,
        "Fonticulua Segmentatus": 19010800,
        "Fonticulua Upupam": 5727600,

        # Frutexa
        "Frutexa Acus": 7774700,
        "Frutexa Collum": 1639800,
        "Frutexa Fera": 1632500,
        "Frutexa Flabellum": 1808900,
        "Frutexa Flammasis": 10326000,
        "Frutexa Metallicum": 1632500,
        "Frutexa Sponsae": 5988000,

        # Fumerola
        "Fumerola Aquatis": 6284600,
        "Fumerola Carbosis": 6284600,
        "Fumerola Extremus": 16202800,
        "Fumerola Nitris": 7500900,

        # Fungoida
        "Fungoida Bullarum": 3703200,
        "Fungoida Gelata": 3330300,
        "Fungoida Setisis": 1670100,
        "Fungoida Stabitis": 2680300,

        # Osseus
        "Osseus Cornibus": 1483000,
        "Osseus Discus": 12934900,
        "Osseus Fractus": 4027800,
        "Osseus Pellebantus": 9739000,
        "Osseus Pumice": 3156300,
        "Osseus Spiralis": 2404700,

        # Recepta
        "Recepta Conditivus": 14313700,
        "Recepta Deltahedronix": 16202800,
        "Recepta Umbrux": 12934900,

        # Sinuous Tuber
        "Sinuous Tuber Albidum": 3425600,
        "Sinuous Tuber Blatteum": 1514500,
        "Sinuous Tuber Caeruleum": 1514500,
        "Sinuous Tuber Lindigoticum": 1514500,
        "Sinuous Tuber Prasinum": 1514500,
        "Sinuous Tuber Roseus": 1514500,
        "Sinuous Tuber Violaceum": 1514500,
        "Sinuous Tuber Viride": 1514500,

        # Stratum
        "Stratum Araneamus": 2448900,
        "Stratum Cucumisis": 16202800,
        "Stratum Excutitus": 2448900,
        "Stratum Frigus": 2637500,
        "Stratum Laminamus": 2788300,
        "Stratum Limaxus": 1362000,
        "Stratum Paleas": 1362000,
        "Stratum Tectonicas": 19010800,

        # Tubas
        "Tubus Cavas": 11873200,
        "Tubus Compagibus": 7774700,
        "Tubus Conifer": 2415500,
        "Tubus Rosarium": 2637500,
        "Tubus Sororibus": 5727600,

        # Tussock
        "Tussock Albata": 3252500,
        "Tussock Capillum": 7025800,
        "Tussock Caputus": 3472400,
        "Tussock Catena": 1766600,
        "Tussock Cultro": 1766600,
        "Tussock Divisa": 1766600,
        "Tussock Ignis": 1849000,
        "Tussock Pennata": 5853800,
        "Tussock Pennatis": 1000000,
        "Tussock Propagito": 1000000,
        "Tussock Serrati": 4447100,
        "Tussock Stigmasis": 19010800,
        "Tussock Triticum": 7774700,
        "Tussock Ventusa": 3277700,
        "Tussock Virgam": 14313700,

        # Thargoid
        "Thargoid Spires": 2247100,
        "Thargoid Mega Barnacles": 2313500,
        "Thargoid Coral Tree": 1896800,
        "Thargoid Coral Root": 1924600,
    }
    return full_species_value_mapping.get(species_localised, 0)
