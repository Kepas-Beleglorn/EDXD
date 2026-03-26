from enum import Enum
from typing import Set

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
    BlackHole = "Black Hole"
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

# Star class groups
SC_WHITE_DWARFS: Set[StarClass] = {
    StarClass.D,
    StarClass.DA,
    StarClass.DAB,
    StarClass.DB,
    StarClass.DC,
    StarClass.DCV,
    StarClass.DQ,
}