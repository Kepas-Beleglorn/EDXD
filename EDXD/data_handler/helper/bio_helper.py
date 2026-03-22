
from enum import Enum
from typing import List, Optional, Set

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
    "Anemone Blatteum Bioluminescent": "$Codex_Ent_Clypeus_Genus_Name;",
    "Blatteum Bioluminescent Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Anemone Croceum": "$Codex_Ent_Clypeus_Genus_Name;",
    "Croceum Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Anemone Luteolum": "$Codex_Ent_Clypeus_Genus_Name;",
    "Luteolum Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Anemone Prasinum Bioluminescent": "$Codex_Ent_Clypeus_Genus_Name;",
    "Prasinum Bioluminescent Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Anemone Puniceum": "$Codex_Ent_Clypeus_Genus_Name;",
    "Puniceum Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Anemone Roseum": "$Codex_Ent_Clypeus_Genus_Name;",
    "Roseum Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Anemone Roseum Bioluminescent": "$Codex_Ent_Clypeus_Genus_Name;",
    "Roseum Bioluminescent Anemone": "$Codex_Ent_Clypeus_Genus_Name;",
    "Anemone Rubeum Bioluminescent": "$Codex_Ent_Clypeus_Genus_Name;",
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

# ---------------------------------------------------------------------------
# Enums for System Properties
# ---------------------------------------------------------------------------

class StarClass(Enum):
    A = "A"
    B = "B"
    O = "O"
    F = "F"
    G = "G"
    K = "K"
    M = "M"
    S = "S"
    D = "D"
    BH = "black hole"


class StarLuminosity(Enum):
    I = "I"
    II = "II"
    III = "III"
    IV = "IV"
    V = "V"
    VI = "VI"
    VII = "VII"


class Atmosphere(Enum):
    NONE = "None"
    CO2 = "CarbonDioxide"
    CO2_RICH = "CarbonDioxideRich"
    AMMONIA = "Ammonia"
    WATER = "Water"
    WATER_RICH = "WaterRich"
    METHANE = "Methane"
    METHANE_RICH = "MethaneRich"
    NITROGEN = "Nitrogen"
    OXYGEN = "Oxygen"
    HELIUM = "Helium"
    NEON = "Neon"
    NEON_RICH = "NeonRich"
    ARGON = "Argon"
    ARGON_RICH = "ArgonRich"
    SO2 = "SulphurDioxide"


class PlanetType(Enum):
    ROCKY = "Rocky body"
    HMC = "High metal content body"
    METAL_RICH = "Metal rich body"
    ROCKY_ICE = "Rocky ice body"
    ICY = "Icy body"
    EARTH_LIKE = "Earthlike body"
    WATER_WORLD = "Water world"  # For system flags


class Volcanism(Enum):
    NONE = "None"
    WATER = "Water"
    METHANE = "Methane"
    CO2 = {"carbon dioxide geysers volcanism", "minor carbon dioxide geysers volcanism"}

    NITROGEN = "Nitrogen"
    AMMONIA = "Ammonia"
    SILICATE = "Silicate"
    IRON = "Iron"
    ROCKY = "Rocky"
    SILICATE_MAGMA = "Silicate Magma"
    CARBON = "Carbon"


# ---------------------------------------------------------------------------
# Helper Sets for Cleaner Logic (Optional but recommended)
# ---------------------------------------------------------------------------

ATM_GROUP_CARBON: Set[Atmosphere] = {Atmosphere.CO2, Atmosphere.CO2_RICH}
ATM_GROUP_WATER: Set[Atmosphere] = {Atmosphere.WATER, Atmosphere.WATER_RICH}
ATM_GROUP_METHANE: Set[Atmosphere] = {Atmosphere.METHANE, Atmosphere.METHANE_RICH}
ATM_GROUP_NEON: Set[Atmosphere] = {Atmosphere.NEON, Atmosphere.NEON_RICH}
ATM_GROUP_ARGON: Set[Atmosphere] = {Atmosphere.ARGON, Atmosphere.ARGON_RICH}
ATM_GROUP_RARE_GAS: Set[Atmosphere] = {Atmosphere.HELIUM, Atmosphere.NEON, Atmosphere.NEON_RICH, Atmosphere.ARGON, Atmosphere.ARGON_RICH}
ATM_GROUP_ALL_BACTERIA: Set[Atmosphere] = {
    Atmosphere.HELIUM, Atmosphere.NEON, Atmosphere.NEON_RICH,
    Atmosphere.METHANE, Atmosphere.METHANE_RICH,
    Atmosphere.ARGON, Atmosphere.ARGON_RICH,
    Atmosphere.NITROGEN, Atmosphere.OXYGEN,
    Atmosphere.AMMONIA, Atmosphere.CO2, Atmosphere.CO2_RICH,
    Atmosphere.WATER, Atmosphere.SO2
}

PT_GROUP_LANDABLE_ROCKY: Set[PlanetType] = {PlanetType.ROCKY, PlanetType.HMC, PlanetType.METAL_RICH, PlanetType.ROCKY_ICE}
PT_GROUP_HMC_ROCKY: Set[PlanetType] = {PlanetType.ROCKY, PlanetType.HMC}
PT_GROUP_ICE: Set[PlanetType] = {PlanetType.ICY, PlanetType.ROCKY_ICE}

VOLC_GROUP_GAS_ICE: Set[Volcanism] = {Volcanism.NITROGEN, Volcanism.AMMONIA}
VOLC_GROUP_CARBON_ICE: Set[Volcanism] = {Volcanism.CARBON, Volcanism.METHANE}
VOLC_GROUP_HOT_ROCK: Set[Volcanism] = {Volcanism.SILICATE, Volcanism.IRON, Volcanism.ROCKY}
VOLC_GROUP_INERT: Set[Volcanism] = {Volcanism.NONE, Atmosphere.HELIUM, Volcanism.IRON, Volcanism.SILICATE}


# Note: Helium is in Atmosphere, but sometimes appears as volcanism in logic. Kept for compatibility.

# ---------------------------------------------------------------------------
# Main Function
# ---------------------------------------------------------------------------

def estimate_biosigns(
        planet_type: PlanetType,
        atmosphere: Atmosphere,
        mean_temp_k: float,
        star_class: Optional[StarClass] = None,
        star_luminosity: Optional[StarLuminosity] = None,
        volcanism: Optional[Volcanism] = None,
        gravity: Optional[float] = None,
        in_nebula: bool = False,
        system_has_earth_like: bool = False,
        system_has_ammonia_world: bool = False,
        system_has_water_giant: bool = False,
        system_has_gas_giant_with_water_life: bool = False,
        system_has_gas_giant_with_ammonia_life: bool = False,
        distance_from_star_ls: Optional[float] = None,
) -> List[str]:
    """
    Estimates probable biosigns based on world parameters using Enum types.

    Args:
        planet_type: Enum PlanetType
        atmosphere: Enum Atmosphere
        mean_temp_k: Float temperature in Kelvin
        star_class: Enum StarClass (optional)
        star_luminosity: Enum StarLuminosity (optional)
        volcanism: Enum Volcanism (optional)
        gravity: Float in Gs (optional)
        in_nebula: Boolean
        system_has_*: Boolean system-wide flags
        distance_from_star_ls: Float distance in Light Seconds (optional)

    Returns:
        List of localised species names (strings).
    """
    possible_species: List[str] = []

    # Aleoida
    if planet_type in PT_GROUP_HMC_ROCKY and gravity is not None and gravity <= 0.27:
        if atmosphere in ATM_GROUP_CARBON:
            if 175 <= mean_temp_k <= 180:
                possible_species.append("Aleoida Arcus")
            if 180 <= mean_temp_k <= 190:
                possible_species.append("Aleoida Coronamus")
            if 190 <= mean_temp_k <= 195:
                possible_species.append("Aleoida Gravis")
        if atmosphere == Atmosphere.AMMONIA:
            possible_species.extend(["Aleoida Laminiae", "Aleoida Spica"])

    # Amphora Plant
    if (atmosphere == Atmosphere.NONE and star_class == StarClass.A and
            (system_has_earth_like or system_has_ammonia_world or system_has_water_giant or
             system_has_gas_giant_with_water_life or system_has_gas_giant_with_ammonia_life)):
        possible_species.append("Amphora Plant")

    # Anemone
    if star_class in [StarClass.A, StarClass.B, StarClass.O]:
        if star_class == StarClass.A:
            if star_luminosity == StarLuminosity.III:
                if planet_type == PlanetType.ROCKY:
                    possible_species.append("Croceum Anemone")
                if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]:
                    possible_species.append("Rubeum Bioluminescent Anemone")

        if star_class == StarClass.B:
            if star_luminosity in [StarLuminosity.I, StarLuminosity.II, StarLuminosity.III] and \
                    planet_type in [PlanetType.METAL_RICH, PlanetType.HMC, PlanetType.ROCKY]:
                possible_species.extend(["Roseum Bioluminescent Anemone", "Roseum Anemone"])
            if star_luminosity in [StarLuminosity.IV, StarLuminosity.V] and \
                    planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]:
                possible_species.append("Blatteum Bioluminescent Anemone")
            if star_luminosity == StarLuminosity.VI:
                if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]:
                    possible_species.append("Rubeum Bioluminescent Anemone")
                if planet_type == PlanetType.ROCKY:
                    possible_species.append("Croceum Anemone")

        if star_class == StarClass.O:
            if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC, PlanetType.ROCKY, PlanetType.ROCKY_ICE, PlanetType.ICY]:
                possible_species.append("Puniceum Anemone")
            if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC, PlanetType.ROCKY]:
                possible_species.append("Prasinum Bioluminescent Anemone")

    # Bacterium
    if atmosphere in ATM_GROUP_ALL_BACTERIA:
        if atmosphere == Atmosphere.HELIUM:
            possible_species.append("Bacterium Nebulus")

        if atmosphere in ATM_GROUP_NEON:
            if volcanism in VOLC_GROUP_GAS_ICE:
                possible_species.append("Bacterium Omentum")
            elif volcanism in VOLC_GROUP_CARBON_ICE:
                possible_species.append("Bacterium Scopulum")
            elif volcanism == Volcanism.WATER:
                possible_species.append("Bacterium Verrata")
            else:
                possible_species.append("Bacterium Acies")

        if atmosphere in ATM_GROUP_METHANE:
            possible_species.append("Bacterium Bullaris")
        if atmosphere in ATM_GROUP_ARGON:
            possible_species.append("Bacterium Vesicula")
        if atmosphere == Atmosphere.NITROGEN:
            possible_species.append("Bacterium Informem")
        if atmosphere == Atmosphere.OXYGEN:
            possible_species.append("Bacterium Volu")
        if atmosphere == Atmosphere.AMMONIA:
            possible_species.append("Bacterium Alcyoneum")
        if atmosphere in ATM_GROUP_CARBON:
            possible_species.append("Bacterium Aurasus")
        if atmosphere in [Atmosphere.WATER, Atmosphere.SO2]:
            possible_species.append("Bacterium Cerbrus")

        if volcanism in VOLC_GROUP_INERT:
            possible_species.append("Bacterium Tela")

    # Bark Mound
    if atmosphere == Atmosphere.NONE and in_nebula:
        possible_species.append("Bark Mound")

    # Brain Tree
    if (planet_type in PT_GROUP_LANDABLE_ROCKY and
            (200 <= mean_temp_k <= 500 or atmosphere in [Atmosphere.AMMONIA, Atmosphere.WATER, Atmosphere.WATER_RICH])):

        if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC] and 300 <= mean_temp_k <= 500:
            possible_species.append("Brain Tree Aureum")
        if planet_type == PlanetType.ROCKY and 200 <= mean_temp_k <= 300:
            possible_species.append("Brain Tree Gypseeum")
        if planet_type in [PlanetType.HMC, PlanetType.ROCKY] and 300 <= mean_temp_k <= 500:
            possible_species.append("Brain Tree Lindigoticum")
        if planet_type == PlanetType.ROCKY and 300 <= mean_temp_k <= 500:
            possible_species.append("Brain Tree Lividum")
        if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]:
            possible_species.extend(["Brain Tree Ostrinum", "Brain Tree Puniceum"])
        if planet_type == PlanetType.ROCKY_ICE and 100 <= mean_temp_k <= 270:
            possible_species.append("Brain Tree Viride")
        if (system_has_earth_like or system_has_gas_giant_with_water_life) or \
                atmosphere in [Atmosphere.AMMONIA, Atmosphere.WATER, Atmosphere.WATER_RICH]:
            possible_species.append("Brain Tree Roseum")

    # Cactoida
    if planet_type in PT_GROUP_HMC_ROCKY:
        if atmosphere in ATM_GROUP_CARBON:
            possible_species.extend(["Cactoida Cortexum", "Cactoida Pullulanta"])
        if atmosphere == Atmosphere.AMMONIA:
            possible_species.extend(["Cactoida Lapis", "Cactoida Peperatis"])
        if atmosphere == Atmosphere.WATER:
            possible_species.append("Cactoida Vermis")

    # Clypeus
    if (planet_type in PT_GROUP_HMC_ROCKY and
            atmosphere in [Atmosphere.WATER, Atmosphere.CO2, Atmosphere.CO2_RICH] and
            mean_temp_k > 190 and
            (gravity is None or gravity <= 0.27)):
        possible_species.extend(["Clypeus Lacrimam", "Clypeus Margaritus"])
        if distance_from_star_ls and distance_from_star_ls > 2500:
            possible_species.append("Clypeus Speculumi")

    # Concha
    if planet_type in PT_GROUP_HMC_ROCKY:
        if atmosphere == Atmosphere.AMMONIA:
            possible_species.append("Concha Aureolas")
        if atmosphere == Atmosphere.NITROGEN:
            possible_species.append("Concha Biconcavis")
        if atmosphere in ATM_GROUP_CARBON and mean_temp_k < 190:
            possible_species.append("Concha Labiata")
        if atmosphere in [Atmosphere.WATER, Atmosphere.WATER_RICH, Atmosphere.CO2, Atmosphere.CO2_RICH] and 180 <= mean_temp_k <= 195:
            possible_species.append("Concha Renibus")

    # Crystalline Shard
    if (atmosphere == Atmosphere.NONE and star_class in [StarClass.A, StarClass.F, StarClass.G, StarClass.K, StarClass.M, StarClass.S] and
            (system_has_earth_like or system_has_ammonia_world or system_has_water_giant or
             system_has_gas_giant_with_water_life or system_has_gas_giant_with_ammonia_life) and
            (distance_from_star_ls is None or distance_from_star_ls > 12000)):
        possible_species.append("Crystalline Shard")

    # Electricae
    if planet_type == PlanetType.ICY and atmosphere in ATM_GROUP_RARE_GAS and (gravity is None or gravity <= 0.27):
        if star_class == StarClass.A and star_luminosity in [StarLuminosity.V, StarLuminosity.VI]:
            possible_species.append("Electricae Pluma")
        if in_nebula:
            possible_species.append("Electricae Radialem")

    # Fonticulua
    if atmosphere == Atmosphere.ARGON:
        possible_species.append("Fonticulua Campestris")
    if atmosphere == Atmosphere.METHANE:
        possible_species.append("Fonticulua Digitos")
    if atmosphere == Atmosphere.OXYGEN:
        possible_species.append("Fonticulua Fluctus")
    if atmosphere == Atmosphere.NITROGEN:
        possible_species.append("Fonticulua Lapida")
    if atmosphere in ATM_GROUP_NEON:
        possible_species.append("Fonticulua Segmentatus")
    if atmosphere == Atmosphere.ARGON_RICH:
        possible_species.append("Fonticulua Upupam")

    # Frutexa
    if planet_type == PlanetType.ROCKY:
        if atmosphere in ATM_GROUP_CARBON and mean_temp_k < 195:
            possible_species.extend(["Frutexa Fera", "Frutexa Acus"])
        if atmosphere == Atmosphere.AMMONIA:
            possible_species.extend(["Frutexa Flabellum", "Frutexa Flammasis"])
        if atmosphere in [Atmosphere.AMMONIA, Atmosphere.CO2, Atmosphere.CO2_RICH] and mean_temp_k < 195:
            possible_species.append("Frutexa Metallicum")
        if atmosphere in ATM_GROUP_WATER:
            possible_species.append("Frutexa Sponsae")

    # Fumerola
    if volcanism:
        if planet_type in PT_GROUP_ICE and volcanism == Volcanism.WATER:
            possible_species.append("Fumerola Aquatis")
        if planet_type in PT_GROUP_ICE and volcanism in [Volcanism.METHANE, Volcanism.CO2]:
            possible_species.append("Fumerola Carbosis")
        if planet_type in PT_GROUP_HMC_ROCKY and volcanism in VOLC_GROUP_HOT_ROCK:
            possible_species.append("Fumerola Extremus")
        if planet_type in PT_GROUP_ICE and volcanism in VOLC_GROUP_GAS_ICE:
            possible_species.append("Fumerola Nitris")

    # Fungoida
    if planet_type in PT_GROUP_HMC_ROCKY:
        if atmosphere in ATM_GROUP_ARGON:
            possible_species.append("Fungoida Bullarum")
        if atmosphere in [Atmosphere.CO2, Atmosphere.CO2_RICH, Atmosphere.WATER] and 180 <= mean_temp_k <= 195:
            possible_species.append("Fungoida Gelata")
        if atmosphere in [Atmosphere.AMMONIA, Atmosphere.METHANE, Atmosphere.METHANE_RICH]:
            possible_species.append("Fungoida Setisis")
        if atmosphere in [Atmosphere.CO2, Atmosphere.CO2_RICH, Atmosphere.WATER] and 180 <= mean_temp_k <= 195:
            possible_species.append("Fungoida Stabitis")

    # Osseus
    if planet_type in PT_GROUP_HMC_ROCKY:
        if atmosphere in ATM_GROUP_CARBON and 180 <= mean_temp_k <= 195:
            possible_species.extend(["Osseus Cornibus", "Osseus Fractus", "Osseus Pellebantus"])
        if atmosphere in ATM_GROUP_WATER:
            possible_species.append("Osseus Discus")
        if atmosphere == Atmosphere.AMMONIA:
            possible_species.append("Osseus Spiralis")
        if planet_type == PlanetType.ROCKY_ICE and atmosphere in [Atmosphere.METHANE, Atmosphere.METHANE_RICH, Atmosphere.ARGON, Atmosphere.ARGON_RICH, Atmosphere.NITROGEN]:
            possible_species.append("Osseus Pumice")

    # Recepta
    if atmosphere == Atmosphere.SO2 and (gravity is None or gravity < 0.27):
        if planet_type in PT_GROUP_ICE:
            possible_species.append("Recepta Conditivus")
        if planet_type in PT_GROUP_HMC_ROCKY:
            possible_species.extend(["Recepta Deltahedronix", "Recepta Umbrux"])

    # Sinuous Tuber
    if volcanism and volcanism != Volcanism.NONE and atmosphere == Atmosphere.NONE:
        if planet_type == PlanetType.ROCKY:
            possible_species.extend(["Sinuous Tuber Albidum", "Sinuous Tuber Caeruleum", "Sinuous Tuber Lindigoticum"])
        if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]:
            possible_species.extend(["Sinuous Tuber Blatteum", "Sinuous Tuber Prasinum", "Sinuous Tuber Violaceum", "Sinuous Tuber Viride"])
        if volcanism == Volcanism.SILICATE_MAGMA:
            possible_species.append("Sinuous Tuber Roseus")

    # Stratum
    if planet_type == PlanetType.ROCKY:
        if atmosphere in [Atmosphere.SO2, Atmosphere.CO2, Atmosphere.CO2_RICH] and mean_temp_k > 165:
            possible_species.extend(["Stratum Araneamus", "Stratum Cucumisis", "Stratum Excutitus", "Stratum Frigus"])
        if atmosphere == Atmosphere.AMMONIA and mean_temp_k > 165:
            possible_species.append("Stratum Laminamus")
        if atmosphere in [Atmosphere.SO2, Atmosphere.CO2, Atmosphere.CO2_RICH] and 165 <= mean_temp_k <= 190:
            possible_species.append("Stratum Limaxus")
        if atmosphere in [Atmosphere.AMMONIA, Atmosphere.WATER, Atmosphere.WATER_RICH] and mean_temp_k > 165:
            possible_species.append("Stratum Paleas")

    if planet_type == PlanetType.HMC and mean_temp_k > 165:
        possible_species.append("Stratum Tectonicas")

    # Tubus
    if planet_type in PT_GROUP_HMC_ROCKY:
        if atmosphere in [Atmosphere.CO2, Atmosphere.CO2_RICH] and 160 <= mean_temp_k <= 190:
            possible_species.extend(["Tubus Cavas", "Tubus Compagibus", "Tubus Conifer"])
        if atmosphere == Atmosphere.AMMONIA and mean_temp_k > 160:
            possible_species.append("Tubus Rosarium")
        if planet_type == PlanetType.HMC and atmosphere in [Atmosphere.AMMONIA, Atmosphere.CO2, Atmosphere.CO2_RICH] and 160 <= mean_temp_k <= 190:
            possible_species.append("Tubus Sororibus")

    # Tussock
    if planet_type == PlanetType.ROCKY:
        if atmosphere in ATM_GROUP_CARBON:
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

        if atmosphere in [Atmosphere.METHANE, Atmosphere.METHANE_RICH, Atmosphere.ARGON, Atmosphere.ARGON_RICH]:
            possible_species.append("Tussock Capillum")
        if atmosphere == Atmosphere.AMMONIA:
            possible_species.extend(["Tussock Catena", "Tussock Cultro", "Tussock Divisa"])
        if atmosphere == Atmosphere.SO2:
            possible_species.append("Tussock Stigmasis")
        if atmosphere in ATM_GROUP_WATER:
            possible_species.append("Tussock Virgam")

    return possible_species