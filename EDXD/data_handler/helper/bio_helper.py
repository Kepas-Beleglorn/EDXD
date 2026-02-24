

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
        "Anemone Blatteum Bioluminescent": 1499900,
        "Blatteum Bioluminescent Anemone": 1499900,
        "Anemone Croceum": 3399800,
        "Croceum Anemone": 3399800,
        "Anemone Luteolum": 1499900,
        "Luteolum Anemone": 1499900,
        "Anemone Prasinum Bioluminescent": 1499900,
        "Prasinum Bioluminescent Anemone": 1499900,
        "Anemone Puniceum": 1499900,
        "Puniceum Anemone": 1499900,
        "Anemone Roseum": 1499900,
        "Roseum Anemone": 1499900,
        "Anemone Roseum Bioluminescent": 1499900,
        "Roseum Bioluminescent Anemone": 1499900,
        "Anemone Rubeum Bioluminescent": 1499900,
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
        "Tubas Cavas": 11873200,
        "Tubas Compagibus": 7774700,
        "Tubas Conifer": 2415500,
        "Tubas Rosarium": 2637500,
        "Tubas Sororibus": 5727600,

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

