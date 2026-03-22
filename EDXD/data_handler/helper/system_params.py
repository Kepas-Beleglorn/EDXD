from enum import Enum
from typing import Set, Optional, List

# ---------------------------------------------------------------------------
# Enums derived from Journal Data (elite_all_constants.csv)
# ---------------------------------------------------------------------------

class StarClass(Enum):
    # Main Sequence & Giants
    O = "O"
    B = "B"
    A = "A"
    F = "F"
    G = "G"
    K = "K"
    M = "M"
    # Special Types
    L = "L"
    T = "T"
    Y = "Y"
    # White Dwarfs
    D = "D"
    DA = "DA"
    DAB = "DAB"
    DB = "DB"
    DC = "DC"
    DCV = "DCV"
    DQ = "DQ"
    # Exotic / Rare
    AeBe = "AeBe"
    N = "N"
    S = "S"
    TTS = "TTS"
    H = "H"
    SupermassiveBlackHole = "SupermassiveBlackHole"
    # Variants found in CSV
    A_BlueWhiteSuperGiant = "A_BlueWhiteSuperGiant"
    K_OrangeGiant = "K_OrangeGiant"
    M_RedGiant = "M_RedGiant"
    M_RedSuperGiant = "M_RedSuperGiant"

class StarLuminosity(Enum):
    I = "I"
    Iab = "Iab"
    Ib = "Ib"
    II = "II"
    IIIab = "IIIab"
    IIIb = "IIIb"
    III = "III"
    IVab = "IVab"
    IVb = "IVb"
    IV = "IV"
    Va = "Va"
    Vab = "Vab"
    Vb = "Vb"
    V = "V"
    Vz = "Vz"
    VI = "VI"
    VII = "VII"
    # Fallback for non-standard entries like 'O' in luminosity field if any
    O = "O"

class Atmosphere(Enum):
    NONE = "None"
    # Standard
    AMMONIA = "Ammonia"
    ARGON = "Argon"
    ARGON_RICH = "ArgonRich"
    CARBON_DIOXIDE = "CarbonDioxide"
    CARBON_DIOXIDE_RICH = "CarbonDioxideRich"
    HELIUM = "Helium"
    METHANE = "Methane"
    METHANE_RICH = "MethaneRich"
    NEON = "Neon"
    NEON_RICH = "NeonRich"
    NITROGEN = "Nitrogen"
    OXYGEN = "Oxygen"
    SILICATE_VAPOUR = "SilicateVapour"
    SULPHUR_DIOXIDE = "SulphurDioxide"
    WATER = "Water"
    WATER_RICH = "WaterRich"
    METALLIC_VAPOUR = "MetallicVapour"
    EARTH_LIKE = "EarthLike"
    AMMONIA_OXYGEN = "AmmoniaOxygen"
    # Thick variants
    THICK_AMMONIA = "Thick Ammonia" # Note: CSV had spaces in some, normalize if needed
    THICK_AMMONIA_RICH = "Thick AmmoniaRich"
    THICK_ARGON = "Thick Argon"
    THICK_ARGON_RICH = "Thick ArgonRich"
    THICK_CARBON_DIOXIDE = "Thick CarbonDioxide"
    THICK_CARBON_DIOXIDE_RICH = "Thick CarbonDioxideRich"
    THICK_HELIUM = "Thick Helium"
    THICK_METHANE = "Thick Methane"
    THICK_METHANE_RICH = "Thick MethaneRich"
    THICK_NITROGEN = "Thick Nitrogen"
    THICK_SULPHUR_DIOXIDE = "Thick SulphurDioxide"
    THICK_WATER = "Thick Water"
    THICK_WATER_RICH = "Thick WaterRich"
    THICK_EMPTY = "Thick  " # CSV had "thick  atmosphere" -> type might be "Thick  "
    # Thin variants
    THIN_AMMONIA = "Thin Ammonia"
    THIN_ARGON = "Thin Argon"
    THIN_ARGON_RICH = "Thin ArgonRich"
    THIN_CARBON_DIOXIDE = "Thin CarbonDioxide"
    THIN_CARBON_DIOXIDE_RICH = "Thin CarbonDioxideRich"
    THIN_HELIUM = "Thin Helium"
    THIN_METHANE = "Thin Methane"
    THIN_METHANE_RICH = "Thin MethaneRich"
    THIN_NEON = "Thin Neon"
    THIN_NEON_RICH = "Thin NeonRich"
    THIN_NITROGEN = "Thin Nitrogen"
    THIN_OXYGEN = "Thin Oxygen"
    THIN_SULPHUR_DIOXIDE = "Thin SulphurDioxide"
    THIN_WATER = "Thin Water"
    THIN_WATER_RICH = "Thin WaterRich"
    THIN_EMPTY = "Thin  "
    # Hot variants
    HOT_CARBON_DIOXIDE = "Hot CarbonDioxide"
    HOT_CARBON_DIOXIDE_RICH = "Hot CarbonDioxideRich"
    HOT_SILICATE_VAPOUR = "Hot SilicateVapour"
    HOT_SULPHUR_DIOXIDE = "Hot SulphurDioxide"
    HOT_THICK_AMMONIA = "Hot Thick Ammonia"
    HOT_THICK_AMMONIA_RICH = "Hot Thick AmmoniaRich"
    HOT_THICK_ARGON_RICH = "Hot Thick ArgonRich"
    HOT_THICK_CARBON_DIOXIDE = "Hot Thick CarbonDioxide"
    HOT_THICK_CARBON_DIOXIDE_RICH = "Hot Thick CarbonDioxideRich"
    HOT_THICK_METALLIC_VAPOUR = "Hot Thick MetallicVapour"
    HOT_THICK_METHANE_RICH = "Hot Thick MethaneRich"
    HOT_THICK_SILICATE_VAPOUR = "Hot Thick SilicateVapour"
    HOT_THICK_SULPHUR_DIOXIDE = "Hot Thick SulphurDioxide"
    HOT_THICK_WATER = "Hot Thick Water"
    HOT_THICK_WATER_RICH = "Hot Thick WaterRich"
    HOT_THIN_CARBON_DIOXIDE = "Hot Thin CarbonDioxide"
    HOT_THIN_SILICATE_VAPOUR = "Hot Thin SilicateVapour"
    HOT_THIN_SULPHUR_DIOXIDE = "Hot Thin SulphurDioxide"
    HOT_WATER = "Hot Water"
    HOT_AMMONIA = "Hot Ammonia" # Inferred
    HOT_ARGON = "Hot Argon"     # Inferred
    HOT_HELIUM = "Hot Helium"   # Inferred
    HOT_METHANE = "Hot Methane" # Inferred
    HOT_NITROGEN = "Hot Nitrogen" # Inferred
    HOT_OXYGEN = "Hot Oxygen"   # Inferred
    HOT_NEON = "Hot Neon"       # Inferred

class PlanetType(Enum):
    ROCKY = "Rocky body"
    HMC = "High metal content body"
    METAL_RICH = "Metal rich body"
    ROCKY_ICE = "Rocky ice body"
    ICY = "Icy body"
    EARTH_LIKE = "Earthlike body"
    WATER_WORLD = "Water world"
    AMMONIA_WORLD = "Ammonia world"
    # Gas Giants (Non-landable, but needed for system flags)
    GAS_GIANT_WATER_LIFE = "Gas giant with water based life"
    GAS_GIANT_AMMONIA_LIFE = "Gas giant with ammonia based life"
    SUDARSKY_I = "Sudarsky class I gas giant"
    SUDARSKY_II = "Sudarsky class II gas giant"
    SUDARSKY_III = "Sudarsky class III gas giant"
    SUDARSKY_IV = "Sudarsky class IV gas giant"
    SUDARSKY_V = "Sudarsky class V gas giant"
    HELIUM_RICH_GIANT = "Helium rich gas giant"
    WATER_GIANT = "Water giant"

class Volcanism(Enum):
    NONE = "None"
    # Water
    WATER_GEYSERS = "water geysers volcanism"
    WATER_MAGMA = "water magma volcanism"
    MAJOR_WATER_GEYSERS = "major water geysers volcanism"
    MAJOR_WATER_MAGMA = "major water magma volcanism"
    MINOR_WATER_GEYSERS = "minor water geysers volcanism"
    MINOR_WATER_MAGMA = "minor water magma volcanism"
    # Carbon Dioxide
    CO2_GEYSERS = "carbon dioxide geysers volcanism"
    MINOR_CO2_GEYSERS = "minor carbon dioxide geysers volcanism"
    # Silicate
    SILICATE_VAPOUR_GEYSERS = "silicate vapour geysers volcanism"
    MAJOR_SILICATE_VAPOUR_GEYSERS = "major silicate vapour geysers volcanism"
    MINOR_SILICATE_VAPOUR_GEYSERS = "minor silicate vapour geysers volcanism"
    # Metallic
    METALLIC_MAGMA = "metallic magma volcanism"
    MAJOR_METALLIC_MAGMA = "major metallic magma volcanism"
    MINOR_METALLIC_MAGMA = "minor metallic magma volcanism"
    # Rocky
    ROCKY_MAGMA = "rocky magma volcanism"
    MAJOR_ROCKY_MAGMA = "major rocky magma volcanism"
    MINOR_ROCKY_MAGMA = "minor rocky magma volcanism"
    # Ammonia
    MINOR_AMMONIA_MAGMA = "minor ammonia magma volcanism"
    # Methane
    MINOR_METHANE_MAGMA = "minor methane magma volcanism"
    # Nitrogen
    MINOR_NITROGEN_MAGMA = "minor nitrogen magma volcanism"

# ---------------------------------------------------------------------------
# Helper Sets for Logic
# ---------------------------------------------------------------------------

# Atmosphere Groups
ATM_GROUP_CARBON: Set[Atmosphere] = {
    Atmosphere.CARBON_DIOXIDE, Atmosphere.CARBON_DIOXIDE_RICH,
    Atmosphere.THICK_CARBON_DIOXIDE, Atmosphere.THICK_CARBON_DIOXIDE_RICH,
    Atmosphere.THIN_CARBON_DIOXIDE, Atmosphere.THIN_CARBON_DIOXIDE_RICH,
    Atmosphere.HOT_CARBON_DIOXIDE, Atmosphere.HOT_CARBON_DIOXIDE_RICH,
    Atmosphere.HOT_THICK_CARBON_DIOXIDE, Atmosphere.HOT_THICK_CARBON_DIOXIDE_RICH,
    Atmosphere.HOT_THIN_CARBON_DIOXIDE,
}

ATM_GROUP_WATER: Set[Atmosphere] = {
    Atmosphere.WATER, Atmosphere.WATER_RICH,
    Atmosphere.THICK_WATER, Atmosphere.THICK_WATER_RICH,
    Atmosphere.THIN_WATER, Atmosphere.THIN_WATER_RICH,
    Atmosphere.HOT_WATER, Atmosphere.HOT_THICK_WATER, Atmosphere.HOT_THICK_WATER_RICH,
}

ATM_GROUP_METHANE: Set[Atmosphere] = {
    Atmosphere.METHANE, Atmosphere.METHANE_RICH,
    Atmosphere.THICK_METHANE, Atmosphere.THICK_METHANE_RICH,
    Atmosphere.THIN_METHANE, Atmosphere.THIN_METHANE_RICH,
    Atmosphere.HOT_THICK_METHANE_RICH,
}

ATM_GROUP_NEON: Set[Atmosphere] = {
    Atmosphere.NEON, Atmosphere.NEON_RICH,
    Atmosphere.THIN_NEON, Atmosphere.THIN_NEON_RICH,
}

ATM_GROUP_ARGON: Set[Atmosphere] = {
    Atmosphere.ARGON, Atmosphere.ARGON_RICH,
    Atmosphere.THICK_ARGON, Atmosphere.THICK_ARGON_RICH,
    Atmosphere.THIN_ARGON, Atmosphere.THIN_ARGON_RICH,
    Atmosphere.HOT_THICK_ARGON_RICH,
}

ATM_GROUP_RARE_GAS: Set[Atmosphere] = {
    Atmosphere.HELIUM, Atmosphere.THICK_HELIUM, Atmosphere.THIN_HELIUM,
    *ATM_GROUP_NEON, *ATM_GROUP_ARGON
}

ATM_GROUP_ALL_BACTERIA: Set[Atmosphere] = {
    Atmosphere.HELIUM, Atmosphere.THICK_HELIUM, Atmosphere.THIN_HELIUM,
    *ATM_GROUP_NEON, *ATM_GROUP_ARGON, *ATM_GROUP_METHANE,
    Atmosphere.NITROGEN, Atmosphere.THICK_NITROGEN, Atmosphere.THIN_NITROGEN,
    Atmosphere.OXYGEN, Atmosphere.THIN_OXYGEN,
    Atmosphere.AMMONIA, Atmosphere.THICK_AMMONIA,
    *ATM_GROUP_CARBON, *ATM_GROUP_WATER,
    Atmosphere.SULPHUR_DIOXIDE, Atmosphere.THICK_SULPHUR_DIOXIDE, Atmosphere.THIN_SULPHUR_DIOXIDE,
    Atmosphere.HOT_SULPHUR_DIOXIDE, Atmosphere.HOT_THICK_SULPHUR_DIOXIDE, Atmosphere.HOT_THIN_SULPHUR_DIOXIDE,
    Atmosphere.HOT_SILICATE_VAPOUR, Atmosphere.HOT_THICK_SILICATE_VAPOUR, Atmosphere.HOT_THIN_SILICATE_VAPOUR,
    Atmosphere.METALLIC_VAPOUR, Atmosphere.HOT_THICK_METALLIC_VAPOUR,
}

# Planet Type Groups
PT_GROUP_LANDABLE_ROCKY: Set[PlanetType] = {
    PlanetType.ROCKY, PlanetType.HMC, PlanetType.METAL_RICH, PlanetType.ROCKY_ICE
}
PT_GROUP_HMC_ROCKY: Set[PlanetType] = {PlanetType.ROCKY, PlanetType.HMC}
PT_GROUP_ICE: Set[PlanetType] = {PlanetType.ICY, PlanetType.ROCKY_ICE}

# Volcanism Groups
VOLC_GROUP_GAS_ICE: Set[Volcanism] = {
    Volcanism.MINOR_NITROGEN_MAGMA, Volcanism.MINOR_AMMONIA_MAGMA,
    # Add specific geysers if logic requires
}
VOLC_GROUP_CARBON_ICE: Set[Volcanism] = {
    Volcanism.MINOR_METHANE_MAGMA,
    Volcanism.CO2_GEYSERS, Volcanism.MINOR_CO2_GEYSERS
}
VOLC_GROUP_HOT_ROCK: Set[Volcanism] = {
    Volcanism.METALLIC_MAGMA, Volcanism.MAJOR_METALLIC_MAGMA, Volcanism.MINOR_METALLIC_MAGMA,
    Volcanism.ROCKY_MAGMA, Volcanism.MAJOR_ROCKY_MAGMA, Volcanism.MINOR_ROCKY_MAGMA,
    Volcanism.SILICATE_VAPOUR_GEYSERS, Volcanism.MAJOR_SILICATE_VAPOUR_GEYSERS, Volcanism.MINOR_SILICATE_VAPOUR_GEYSERS,
}
VOLC_GROUP_INERT: Set[Volcanism] = {
    Volcanism.NONE,
    # Helium is Atmosphere, but logic treats it as inert volcanism source sometimes
}