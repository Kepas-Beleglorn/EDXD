from EDXD.data_handler.helper.system_property_constants import STAR_CLASS as SC
from EDXD.data_handler.helper.system_property_constants import STAR_LUMINOSITY as SL

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

def estimate_biosigns(
    planet_type: str,
    atmosphere: str,
    mean_temp_k: float,
    star_class: str = None,
    star_luminosity: str = None,
    volcanism: str = None,
    gravity: float = None,
    in_nebulas: bool = False,
    system_has_earth_like: bool = False,
    system_has_ammonia_world: bool = False,
    system_has_water_giant: bool = False,
    system_has_gas_giant_with_water_life: bool = False,
    system_has_gas_giant_with_ammonia_life: bool = False,
    distance_from_star_ls: float = None,
) -> list[str]:
    """
    Estimates probable biosigns based on world parameters, using precise criteria for each genus and species.
    Genuses are ordered alphabetically for clarity.
    """
    possible_species = []

    # Aleoida
    if planet_type in ["Rocky", "High Metal Content"] and (gravity is not None and gravity <= 0.27):
        if atmosphere in ["CO2-Rich", "CO2"]:
            if 175 <= mean_temp_k <= 180:
                possible_species.append("Aleoida Arcus")
            if 180 <= mean_temp_k <= 190:
                possible_species.append("Aleoida Coronamus")
            if 190 <= mean_temp_k <= 195:
                possible_species.append("Aleoida Gravis")
        if atmosphere == "Ammonia":
            possible_species.extend(["Aleoida Laminiae", "Aleoida Spica"])

    # Amphora Plant
    if (atmosphere == "None" and star_class == SC.A and
            (system_has_earth_like or system_has_ammonia_world or system_has_water_giant or system_has_gas_giant_with_water_life or system_has_gas_giant_with_ammonia_life)):
        possible_species.append("Amphora Plant")

    # Anemone
    if star_class in [SC.A, SC.B, SC.O]:
        # A-type stars
        if star_class == SC.A:
            if star_luminosity == SL.III:
                if planet_type == "Rocky":
                    possible_species.append("Croceum Anemone")
                if planet_type in ["Metal-Rich", "High Metal Content"]:
                    possible_species.append("Rubeum Bioluminescent Anemone")
        # B-type stars
        if star_class == SC.B:
            if star_luminosity in [SL.I, SL.II, SL.III] and planet_type in ["Metal-Rich", "High Metal Content", "Rocky"]:
                possible_species.append(["Roseum Bioluminescent Anemone", "Roseum Anemone"])
            if star_luminosity in [SL.IV, SL.V] and planet_type in ["Metal-Rich", "High Metal Content"]:
                possible_species.append("Blatteum Bioluminescent Anemone")
            if star_luminosity == SL.VI:
                if planet_type in ["Metal-Rich", "High Metal Content"]:
                    possible_species.append("Rubeum Bioluminescent Anemone")
                if planet_type in ["Rocky"]:
                    possible_species.append("Croceum Anemone")
        # O-type stars
        if star_class == "O":
            if planet_type in ["Metal-Rich", "High Metal Content", "Rocky", "Rocky Ice", "Icy"]:
                possible_species.extend(["Puniceum Anemone"])
            if planet_type in ["Metal-Rich", "High Metal Content", "Rocky"]:
                possible_species.extend(["Prasinum Bioluminescent Anemone"])

    # Bacterium
    if atmosphere in ["Helium", "Neon", "Neon-Rich", "Methane", "Methane-Rich", "Argon", "Argon-Rich", "Nitrogen", "Oxygen", "Ammonia", "CO2-Rich", "CO2", "Water", "SO2"]:
        if atmosphere in ["Helium"]:
            possible_species.append("Bacterium Nebulus")
        if atmosphere in ["Neon", "Neon-Rich"]:
            if volcanism in ["Nitrogen", "Ammonia"]:
                possible_species.append("Bacterium Omentum")
            elif volcanism in ["Carbon", "Methane"]:
                possible_species.append("Bacterium Scopulum")
            elif volcanism == "Water":
                possible_species.append("Bacterium Verrata")
            else:
                possible_species.append("Bacterium Acies")
        if atmosphere in ["Methane", "Methane-Rich"]:
            possible_species.append("Bacterium Bullaris")
        if atmosphere in ["Argon", "Argon-Rich"]:
            possible_species.append("Bacterium Vesicula")
        if atmosphere == "Nitrogen":
            possible_species.append("Bacterium Informem")
        if atmosphere == "Oxygen":
            possible_species.append("Bacterium Volu")
        if atmosphere == "Ammonia":
            possible_species.append("Bacterium Alcyoneum")
        if atmosphere in ["CO2-Rich", "CO2"]:
            possible_species.append("Bacterium Aurasus")
        if atmosphere in ["Water", "SO2"]:
            possible_species.append("Bacterium Cerbrus")
        if volcanism in ["None", "Helium", "Iron", "Silicate"]:
            possible_species.append("Bacterium Tela")

    # Bark Mound
    if atmosphere == "None" and in_nebulas:
        possible_species.append("Bark Mound")

    # Brain Tree
    if (planet_type in ["Rocky", "High Metal Content", "Metal-Rich", "Rocky Ice"] and
            (200 <= mean_temp_k <= 500 or atmosphere in ["Ammonia", "Water", "Water-Rich"])):
        if planet_type in ["Metal-Rich", "High Metal Content"] and 300 <= mean_temp_k <= 500:
            possible_species.append("Brain Tree Aureum")
        if planet_type == "Rocky" and 200 <= mean_temp_k <= 300:
            possible_species.append("Brain Tree Gypseeum")
        if planet_type in ["High Metal Content", "Rocky"] and 300 <= mean_temp_k <= 500:
            possible_species.append("Brain Tree Lindigoticum")
        if planet_type == "Rocky" and 300 <= mean_temp_k <= 500:
            possible_species.append("Brain Tree Lividum")
        if planet_type in ["Metal-Rich", "High Metal Content"]:
            possible_species.extend(["Brain Tree Ostrinum", "Brain Tree Puniceum"])
        if planet_type == "Rocky Ice" and 100 <= mean_temp_k <= 270:
            possible_species.append("Brain Tree Viride")
        if (system_has_earth_like or system_has_gas_giant_with_water_life) or atmosphere in ["Ammonia", "Water", "Water-Rich"]:
            possible_species.append("Brain Tree Roseum")

    # Cactoida
    if planet_type in ["Rocky", "High Metal Content"]:
        if atmosphere in ["CO2-Rich", "CO2"]:
            possible_species.extend(["Cactoida Cortexum", "Cactoida Pullulanta"])
        if atmosphere == "Ammonia":
            possible_species.extend(["Cactoida Lapis", "Cactoida Peperatis"])
        if atmosphere == "Water":
            possible_species.append("Cactoida Vermis")

    # Clypeus
    if (planet_type in ["Rocky", "High Metal Content"] and
            atmosphere in ["Water", "CO2-Rich", "CO2"] and
            mean_temp_k > 190 and
            (gravity is None or gravity <= 0.27)):
        possible_species.extend(["Clypeus Lacrimam", "Clypeus Margaritus"])
        if distance_from_star_ls and distance_from_star_ls > 2500:
            possible_species.append("Clypeus Speculumi")

    # Concha
    if planet_type in ["Rocky", "High Metal Content"]:
        if atmosphere == "Ammonia":
            possible_species.append("Concha Aureolas")
        if atmosphere == "Nitrogen":
            possible_species.append("Concha Biconcavis")
        if atmosphere in ["CO2-Rich", "CO2"] and mean_temp_k < 190:
            possible_species.append("Concha Labiata")
        if atmosphere in ["Water", "Water-Rich", "CO2-Rich", "CO2"] and 180 <= mean_temp_k <= 195:
            possible_species.append("Concha Renibus")

    # Crystalline Shard
    if (atmosphere == "None" and star_class in ["A", "F", "G", "K", "M", "S"] and
            (system_has_earth_like or system_has_ammonia_world or system_has_water_giant or system_has_gas_giant_with_water_life or system_has_gas_giant_with_ammonia_life) and
            (distance_from_star_ls is None or distance_from_star_ls > 12000)):
        possible_species.append("Crystalline Shard")

    # Electricae
    if planet_type == "Icy" and atmosphere in ["Helium", "Neon", "Argon"] and (gravity is None or gravity <= 0.27):
        if star_class == "A" and star_luminosity in ["V", "VI"]:
            possible_species.append("Electricae Pluma")
        if in_nebulas:
            possible_species.append("Electricae Radialem")

    # Fonticulua
    if atmosphere in ["Argon"]:
        possible_species.append("Fonticulua Campestris")
    if atmosphere == "Methane":
        possible_species.append("Fonticulua Digitos")
    if atmosphere == "Oxygen":
        possible_species.append("Fonticulua Fluctus")
    if atmosphere == "Nitrogen":
        possible_species.append("Fonticulua Lapida")
    if atmosphere in ["Neon", "Neon-Rich"]:
        possible_species.append("Fonticulua Segmentatus")
    if atmosphere == "Argon-Rich":
        possible_species.append("Fonticulua Upupam")

    # Frutexa
    if planet_type == "Rocky":
        if atmosphere in ["CO2-Rich", "CO2"] and mean_temp_k < 195:
            possible_species.extend(["Frutexa Fera", "Frutexa Acus"])
        if atmosphere == "Ammonia":
            possible_species.extend(["Frutexa Flabellum", "Frutexa Flammasis"])
        if atmosphere in ["Ammonia", "CO2-Rich", "CO2"] and mean_temp_k < 195:
            possible_species.append("Frutexa Metallicum")
        if atmosphere in ["Water", "Water-Rich"]:
            possible_species.append("Frutexa Sponsae")

    # Fumerola
    if volcanism:
        if planet_type in ["Icy", "Rocky Ice"] and volcanism == "Water":
            possible_species.append("Fumerola Aquatis")
        if planet_type in ["Icy", "Rocky Ice"] and volcanism in ["Methane", "CO2"]:
            possible_species.append("Fumerola Carbosis")
        if planet_type in ["Rocky", "High Metal Content"] and volcanism in ["Silicate", "Iron", "Rocky"]:
            possible_species.append("Fumerola Extremus")
        if planet_type in ["Icy", "Rocky Ice"] and volcanism in ["Nitrogen", "Ammonia"]:
            possible_species.append("Fumerola Nitris")

    # Fungoida
    if planet_type in ["Rocky", "High Metal Content"]:
        if atmosphere in ["Argon", "Argon-Rich"]:
            possible_species.append("Fungoida Bullarum")
        if atmosphere in ["CO2-Rich", "CO2", "Water"] and 180 <= mean_temp_k <= 195:
            possible_species.append("Fungoida Gelata")
        if atmosphere in ["Ammonia", "Methane", "Methane-Rich"]:
            possible_species.append("Fungoida Setisis")
        if atmosphere in ["CO2-Rich", "CO2", "Water"] and 180 <= mean_temp_k <= 195:
            possible_species.append("Fungoida Stabitis")

    # Osseus
    if planet_type in ["Rocky", "High Metal Content"]:
        if atmosphere in ["CO2-Rich", "CO2"] and 180 <= mean_temp_k <= 195:
            possible_species.extend(["Osseus Cornibus", "Osseus Fractus", "Osseus Pellebantus"])
        if atmosphere in ["Water", "Water-Rich"]:
            possible_species.append("Osseus Discus")
        if atmosphere == "Ammonia":
            possible_species.append("Osseus Spiralis")
        if planet_type == "Rocky Ice" and atmosphere in ["Methane", "Methane-Rich", "Argon", "Argon-Rich", "Nitrogen"]:
            possible_species.append("Osseus Pumice")

    # Recepta
    if atmosphere == "SO2" and (gravity is None or gravity < 0.27):
        if planet_type in ["Icy", "Rocky Ice"]:
            possible_species.append("Recepta Conditivus")
        if planet_type in ["Rocky", "High Metal Content"]:
            possible_species.extend(["Recepta Deltahedronix", "Recepta Umbrux"])

    # Sinuous Tuber
    if volcanism not in ["None", None] and atmosphere == "None":
        if planet_type == "Rocky":
            possible_species.extend(["Sinuous Tuber Albidum", "Sinuous Tuber Caeruleum", "Sinuous Tuber Lindigoticum"])
        if planet_type in ["Metal-Rich", "High Metal Content"]:
            possible_species.extend(["Sinuous Tuber Blatteum", "Sinuous Tuber Prasinum", "Sinuous Tuber Violaceum", "Sinuous Tuber Viride"])
        if volcanism == "Silicate Magma":
            possible_species.append("Sinuous Tuber Roseus")

    # Stratum
    if planet_type == "Rocky":
        if atmosphere in ["SO2", "CO2-Rich", "CO2"] and mean_temp_k > 165:
            possible_species.extend(["Stratum Araneamus", "Stratum Cucumisis", "Stratum Excutitus", "Stratum Frigus"])
        if atmosphere == "Ammonia" and mean_temp_k > 165:
            possible_species.append("Stratum Laminamus")
        if atmosphere in ["SO2", "CO2-Rich", "CO2"] and 165 <= mean_temp_k <= 190:
            possible_species.append("Stratum Limaxus")
        if atmosphere in ["Ammonia", "Water", "Water-Rich"] and mean_temp_k > 165:
            possible_species.append("Stratum Paleas")
    if planet_type == "High Metal Content" and mean_temp_k > 165:
        possible_species.append("Stratum Tectonicas")

    # Tubus
    if planet_type in ["Rocky", "High Metal Content"]:
        if atmosphere in ["CO2", "CO2-Rich"] and 160 <= mean_temp_k <= 190:
            possible_species.extend(["Tubus Cavas", "Tubus Compagibus", "Tubus Conifer"])
        if atmosphere == "Ammonia" and mean_temp_k > 160:
            possible_species.append("Tubus Rosarium")
        if planet_type == "High Metal Content" and atmosphere in ["Ammonia", "CO2", "CO2-Rich"] and 160 <= mean_temp_k <= 190:
            possible_species.append("Tubus Sororibus")

    # Tussock
    if planet_type == "Rocky":
        if atmosphere in ["CO2-Rich", "CO2"]:
            if 175 <= mean_temp_k <= 180:
                possible_species.append("Tussock Albata")
            if 180 <= mean_temp_k <= 190:
                possible_species.append("Tussock Caputus")
            if 160 <= mean_temp_k <= 170:
                possible_species.append("Tussock Ignis")
            if 145 <= mean_temp_k <= 155:
                possible_species.append("Tussock Pennata")
            if mean_temp_k < 195:
                possible_species.extend(["Tussock Pennatis", "Tussock Propagito"])
            if 170 <= mean_temp_k <= 175:
                possible_species.append("Tussock Serrati")
            if 190 <= mean_temp_k <= 195:
                possible_species.append("Tussock Triticum")
            if 155 <= mean_temp_k <= 160:
                possible_species.append("Tussock Ventusa")
        if atmosphere in ["Methane", "Methane-Rich", "Argon", "Argon-Rich"]:
            possible_species.append("Tussock Capillum")
        if atmosphere == "Ammonia":
            possible_species.extend(["Tussock Catena", "Tussock Cultro", "Tussock Divisa"])
        if atmosphere == "SO2":
            possible_species.append("Tussock Stigmasis")
        if atmosphere in ["Water", "Water-Rich"]:
            possible_species.append("Tussock Virgam")

    return possible_species

