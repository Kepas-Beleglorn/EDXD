from typing import List, Optional, Dict, Any, Set
from EDXD.data_handler.helper.system_params import (
    StarClass, StarLuminosity, PlanetType,
    PT_GROUP_HMC_ROCKY, PT_GROUP_ICE,
    SC_WHITE_DWARFS
)
from EDXD.data_handler.helper.bio_helper import (
    get_genus_value,
    get_scan_range_for_species
)

import EDXD.data_handler.helper.data_helper as dh

STR_LIST_NONE = {None, "", "None", "none"}
# ---------------------------------------------------------------------------
# Helper: Map Codex Key to Species Prefix
# ---------------------------------------------------------------------------
def get_genus_prefix_from_codex(codex_key: str) -> str:
    """
    Extracts the genus name from the Codex Key to filter species.
    Example: "$Codex_Ent_Bacterial_Genus_Name;" -> "Bacterium"
    """
    # Simple mapping based on your bio_get_range keys
    mapping = {
        "$Codex_Ent_Fumerolas_Genus_Name;": "Fumerola",
        "$Codex_Ent_Aleoids_Genus_Name;": "Aleoida",
        "$Codex_Ent_Clypeus_Genus_Name;": "Clypeus",  # Note: Anemone maps to Clypeus in some logic, but species start with Anemone
        "$Codex_Ent_Conchas_Genus_Name;": "Concha",
        "$Codex_Ent_Shrubs_Genus_Name;": "Shrubs",  # Covers Brain Tree, Bark Mound, Frutexa, Amphora
        "$Codex_Ent_Recepta_Genus_Name;": "Recepta",
        "$Codex_Ent_Tussocks_Genus_Name;": "Tussock",
        "$Codex_Ent_Cactoid_Genus_Name;": "Cactoida",
        "$Codex_Ent_Fungoids_Genus_Name;": "Fungoida",
        "$Codex_Ent_Bacterial_Genus_Name;": "Bacterium",
        "$Codex_Ent_Fonticulus_Genus_Name;": "Fonticulua",
        "$Codex_Ent_Stratum_Genus_Name;": "Stratum",
        "$Codex_Ent_Osseus_Genus_Name;": "Osseus",
        "$Codex_Ent_Tubus_Genus_Name;": "Tubus",
        "$Codex_Ent_Electricae_Genus_Name;": "Electricae",
        "$Codex_Ent_Vents_Name;": "Vents",
        "$Codex_Ent_Sphere_Name;": "Sphere",
        "$Codex_Ent_Cone_Name;": "Cone",
        "$Codex_Ent_Brancae_Name;": "Brancae",
        "$Codex_Ent_Ground_Struct_Ice_Name;": "Ice",
        "$Codex_Ent_Tube_Name;": "Tube",
        "$Codex_Ent_Barnacles_Name;": "Barnacles",
        "$Codex_Ent_Thargoid_Coral_Name;": "Thargoid",
        "$Codex_Ent_Thargoid_Tower_Name;": "Thargoid",
    }
    return mapping.get(codex_key, "")


def _get_shrubs_prefixes() -> Set[str]:
    """Shrubs genus covers multiple distinct species prefixes."""
    return {"Brain Tree", "Bark Mound", "Frutexa", "Amphora Plant", "Crystalline Shard"}


# ---------------------------------------------------------------------------
# Updated Estimator
# ---------------------------------------------------------------------------

def estimate_system_biosigns(model_bodies: Dict[str, Any]) -> Dict[str, List[Dict]]:
    results = {}

    # 1. System Flags (Same as before)
    system_has_earth_like = False
    system_has_ammonia_world = False
    system_has_water_giant = False
    system_has_gas_giant_with_water_life = False
    system_has_gas_giant_with_ammonia_life = False
    star_class_enum = None
    star_luminosity_enum = None

    for b in model_bodies.values():
        b_type = b.body_type if isinstance(b.body_type, str) else str(b.body_type)
        if b_type == "Earthlike body": system_has_earth_like = True
        if b_type == "Ammonia world": system_has_ammonia_world = True
        if b_type == "Water world": system_has_water_giant = True
        if "water based life" in b_type.lower(): system_has_gas_giant_with_water_life = True
        if "ammonia based life" in b_type.lower(): system_has_gas_giant_with_ammonia_life = True

        is_star = b.is_star

        # TODO: #221 create dictionary with star-ID (body_XX), star class and luminosity.
        #       Body should be able to determine it's parent stars via body_XX
        if is_star and star_class_enum is None:
            s_type = b.body_type
            star_class_enum = _safe_get_enum(s_type, StarClass, None)
            if star_class_enum is None and "_" in s_type:
                star_class_enum = _safe_get_enum(s_type.split("_")[0], StarClass, None)
            lum_raw = getattr(b, 'luminosity', None) or getattr(b, 'raw_luminosity', None)
            if lum_raw:
                star_luminosity_enum = _safe_get_enum(dh.get_clean_luminosity(lum_raw), StarLuminosity, None)

    in_nebula = False

    for body_id, body in model_bodies.items():
        if not getattr(body, 'landable', False):
            continue

        if not getattr(body, 'biosignals', None):
            continue

        # TODO: #221 get current body's parent star(s)

        # 2. Map Body Data
        atm_raw = _safe_get_atmosphere_type(body.atmosphere)
        pt_raw = body.body_type if isinstance(body.body_type, str) else str(body.body_type)
        pt_enum = _safe_get_enum(pt_raw, PlanetType, PlanetType.ROCKY)
        volc_raw = getattr(body, 'volcanism', None) or "None"

        gravity = getattr(body, 'g_force', 0.0)
        mean_temp = getattr(body, 'mean_temp', 0.0)
        distance_ls = getattr(body, 'distance', None)
        body_name = getattr(body, 'body_name', body_id)

        # 3. Check DSS & Codex Data
        bio_found_data = getattr(body, 'bio_found', {})
        scanned_genus_keys = list(bio_found_data.keys()) if bio_found_data else []

        # New: Track Confirmed Species
        confirmed_species_names = set()
        confirmed_variants = {}  # Map species_name -> color

        if scanned_genus_keys:
            for key, data in bio_found_data.items():
                # data is a dict: { "genusid": "...", "variant_localised": "Bacterium Cerbrus - Green", ... }
                variant_raw = data.variant_localised
                if variant_raw:
                    # Parse "Bacterium Cerbrus - Green" -> "Bacterium Cerbrus", "Green"
                    if " - " in variant_raw:
                        sp_name, color = variant_raw.rsplit(" - ", 1)
                    else:
                        sp_name, color = variant_raw, "Unknown"

                    confirmed_species_names.add(sp_name)
                    confirmed_variants[sp_name] = color

        # 4. Generate Candidates
        try:
            potential_species = estimate_biosigns(
                planet_type=pt_enum, atmosphere=atm_raw, mean_temp_k=mean_temp,
                star_class=star_class_enum, star_luminosity=star_luminosity_enum,
                volcanism=volc_raw, gravity=gravity, in_nebula=in_nebula,
                system_has_earth_like=system_has_earth_like,
                system_has_ammonia_world=system_has_ammonia_world,
                system_has_water_giant=system_has_water_giant,
                system_has_gas_giant_with_water_life=system_has_gas_giant_with_water_life,
                system_has_gas_giant_with_ammonia_life=system_has_gas_giant_with_ammonia_life,
                distance_from_star_ls=distance_ls,
            )
        except Exception as e:
            print(f"Error estimating {body_id}: {e}")
            potential_species = []

        # 5. Filter & Refine based on Codex Data
        final_species = []

        if confirmed_species_names:
            # CODEX PHASE: We know exactly what is here.
            # 1. Keep ONLY the confirmed species.
            # 2. Discard all other candidates of the same genus.
            for sp in potential_species:
                if sp in confirmed_species_names:
                    final_species.append(sp)
                # Optional: If you want to keep "theoretical" siblings until 100% complete,
                # you can skip the 'else' block. But usually, 1 species found = others impossible.
        elif scanned_genus_keys:
            # DSS PHASE (Genus known, species unknown): Filter by Genus Prefix (as before)
            allowed_prefixes = set()
            for key in scanned_genus_keys:
                prefix = get_genus_prefix_from_codex(key)
                if prefix == "Shrubs":
                    allowed_prefixes.update(_get_shrubs_prefixes())
                elif prefix == "Thargoid":
                    allowed_prefixes.update(["Thargoid"])
                elif prefix:
                    allowed_prefixes.add(prefix)

            for sp in potential_species:
                matches = any(sp.startswith(p) for p in allowed_prefixes)
                # Special Anemone/Clypeus handling
                if "Anemone" in sp and "Clypeus" in allowed_prefixes: matches = True
                if matches: final_species.append(sp)
        else:
            # PRE-SCAN PHASE: Keep all physics candidates
            final_species = potential_species

        # 6. Enrich Results
        if final_species:
            results[body_id] = []
            for species_name in final_species:
                # If confirmed, probability is 100%, otherwise calculate.
                if species_name in confirmed_species_names:
                    prob = 1.0
                else:
                    # Inside the loop where you calculate prob:
                    prob = calculate_probability(
                        species_name=species_name,
                        planet_type=pt_enum,
                        atmosphere=atm_raw,
                        mean_temp_k=mean_temp,
                        volcanism=volc_raw,
                        gravity=gravity,  # Pass these new args
                        star_class=star_class_enum,
                        star_luminosity=star_luminosity_enum
                    )

                results[body_id].append({
                    "body_id": body_id,
                    "body_name": body_name,
                    "name": species_name,
                    "base_value": get_genus_value(species_name),
                    "scan_range": get_scan_range_for_species(species_name),
                    "probability": round(prob, 2),
                    "confirmed_by_dss": scanned_genus_keys and not confirmed_species_names,  # True if only genus known
                    "confirmed_by_codex": species_name in confirmed_species_names,  # True if exact species known
                    "variant_color": confirmed_variants.get(species_name),  # e.g. "Green"
                    "dss_complete": getattr(body, 'bio_complete', False)
                })

    return results


# ... [Keep _safe_get_atmosphere_type, _safe_get_enum, calculate_probability, estimate_biosigns from previous steps] ...
def _safe_get_atmosphere_type(body_atmosphere: Any) -> str:
    if body_atmosphere is None: return "None"
    if isinstance(body_atmosphere, dict): return body_atmosphere.get("raw", "None") or "None"
    if hasattr(body_atmosphere, "raw"):
        val = getattr(body_atmosphere, "raw", None)
        return val if val else "None"
    if isinstance(body_atmosphere, str): return body_atmosphere if body_atmosphere else "None"
    return "None"

def _safe_get_enum(value: Optional[str], enum_class: Any, default: Any) -> Any:
    if value is None: return default
    try:
        return enum_class(value)
    except ValueError as e:
        print(f"Error: Enum value not found {enum_class}({value}): {e}")
        return default


def calculate_probability(
        species_name: str,
        planet_type: PlanetType,
        atmosphere: str,
        mean_temp_k: float,
        volcanism: Optional[str],
        gravity: Optional[float] = None,
        star_class: Optional[StarClass] = None,
        star_luminosity: Optional[StarLuminosity] = None
) -> float:
    """
    Calculates a relative probability score (0.0 to 1.0).
    Returns 0.0 if hard constraints (Gravity, Atmosphere, Star) are violated.
    """
    score = 0.5

    # -----------------------------------------------------------------------
    # 1. HARD CONSTRAINTS (Return 0.0 if failed)
    # -----------------------------------------------------------------------

    # Gravity Constraints (< 0.27g)
    if gravity is not None and gravity > 0.27:
        if any(x in species_name for x in ["Aleoida", "Clypeus", "Anemone", "Electricae", "Recepta"]):
            return 0.0

    # Atmosphere Constraints (Specific species require specific atm)
    # If the estimator returned it, it's theoretically possible, but if we want strict probability:
    # (Optional: Uncomment if you want to penalize mismatched atm heavily)
    # if "Bacterium Nebulus" in species_name and atmosphere != Atmosphere.HELIUM: return 0.0

    # Star Constraints
    if "Amphora Plant" in species_name:
        if star_class != StarClass.A:
            return 0.0

    if "Electricae Pluma" in species_name:
        if star_class != StarClass.A or star_luminosity not in [StarLuminosity.V, StarLuminosity.VI]:
            return 0.0

    # -----------------------------------------------------------------------
    # 2. TEMPERATURE PRECISION (Narrow ranges = Higher Score)
    # -----------------------------------------------------------------------

    temp_match = False

    # Aleoida (Very Narrow: 5-10K windows)
    if "Aleoida Arcus" in species_name and 175 <= mean_temp_k <= 180:
        temp_match = True
    elif "Aleoida Coronamus" in species_name and 180 <= mean_temp_k <= 190:
        temp_match = True
    elif "Aleoida Gravis" in species_name and 190 <= mean_temp_k <= 195:
        temp_match = True
    elif "Aleoida" in species_name and 175 <= mean_temp_k <= 195:
        temp_match = True  # General match

    # Tussock (Specific windows)
    elif "Tussock Albata" in species_name and 175 <= mean_temp_k <= 180:
        temp_match = True
    elif "Tussock Caputus" in species_name and 180 <= mean_temp_k <= 190:
        temp_match = True
    elif "Tussock Ignis" in species_name and 160 <= mean_temp_k <= 170:
        temp_match = True
    elif "Tussock Pennata" in species_name and 145 <= mean_temp_k <= 155:
        temp_match = True
    elif "Tussock" in species_name and 145 <= mean_temp_k <= 195:
        temp_match = True

    # Stratum / Fungoida / Concha / Tubus (180-195K Sweet Spot)
    elif any(x in species_name for x in ["Stratum", "Fungoida", "Concha", "Tubus", "Osseus"]):
        if 180 <= mean_temp_k <= 195:
            temp_match = True
        elif 160 <= mean_temp_k <= 200:
            temp_match = True  # Broader match

    # Cactoida (Hot: 300-500K or CO2/Ammonia specific)
    elif "Cactoida" in species_name:
        if 300 <= mean_temp_k <= 500: temp_match = True

    # Brain Tree (200-500K)
    elif "Brain Tree" in species_name:
        if 200 <= mean_temp_k <= 500: temp_match = True

    # Fonticulua (Varies by Atm, but generally specific)
    elif "Fonticulua" in species_name:
        temp_match = True  # Hard to pinpoint without atm check, assume match if estimator passed it

    if temp_match:
        score += 0.3
    else:
        # If temp is outside ideal range but inside survival range
        score += 0.05

    # -----------------------------------------------------------------------
    # 3. ATMOSPHERE RARITY (Rare atm = Higher Confidence)
    # -----------------------------------------------------------------------
    if any(opt in atmosphere for opt in ("sulfur", "ammonia", "helium", "neon")):
        score += 0.15
    elif any(opt in atmosphere for opt in ("argon", "oxygen")):
        score += 0.10
    elif "carbon" in atmosphere :
        score += 0.05  # Common, less predictive power

    # -----------------------------------------------------------------------
    # 4. VOLCANISM DEPENDENCY (Critical for Fumerola/Sinuous)
    # -----------------------------------------------------------------------
    has_volcanism = volcanism not in STR_LIST_NONE

    if "Fumerola" in species_name or "Sinuous" in species_name:
        if has_volcanism:
            score += 0.25  # Critical match
        else:
            return 0.0  # Impossible without volcanism

    # -----------------------------------------------------------------------
    # 5. PLANET TYPE SPECIFICITY
    # -----------------------------------------------------------------------
    if "Electricae" in species_name and planet_type == PlanetType.ICY:
        score += 0.1
    if "Osseus Pumice" in species_name and planet_type == PlanetType.ROCKY_ICE:
        score += 0.1

    return min(score, 1.0)


def estimate_biosigns(
        planet_type: PlanetType, atmosphere: str, mean_temp_k: float,
        star_class: Optional[StarClass] = None, star_luminosity: Optional[StarLuminosity] = None,
        volcanism: Optional[str] = None, gravity: Optional[float] = None,
        in_nebula: bool = False, system_has_earth_like: bool = False,
        system_has_ammonia_world: bool = False, system_has_water_giant: bool = False,
        system_has_gas_giant_with_water_life: bool = False,
        system_has_gas_giant_with_ammonia_life: bool = False,
        distance_from_star_ls: Optional[float] = None,
) -> List[str]:
    possible_species: List[str] = []

    # Aleoida
    if "thin" in atmosphere and planet_type in PT_GROUP_HMC_ROCKY and gravity is not None and gravity <= 0.27:
        if "carbon dioxide" in atmosphere:
            if 175 <= mean_temp_k <= 180:
                possible_species.append("Aleoida Arcus")
            if 180 <= mean_temp_k <= 190:
                possible_species.append("Aleoida Coronamus")
            if 190 <= mean_temp_k <= 195:
                possible_species.append("Aleoida Gravis")
        if "ammonia" in atmosphere:
            possible_species.extend(["Aleoida Laminiae", "Aleoida Spica"])

    # Amphora Plant
    if (
            atmosphere in {None, "", "None", "none"} and StarClass.A == star_class and
            (
                    system_has_earth_like or
                    system_has_ammonia_world or
                    system_has_water_giant or
                    system_has_gas_giant_with_water_life or
                    system_has_gas_giant_with_ammonia_life
            )
    ):
        possible_species.append("Amphora Plant")

    # Anemone (Mapped to Clypeus genus)
    if star_class in [StarClass.A, StarClass.B, StarClass.O]:
        if star_class == StarClass.A:
            if star_luminosity == StarLuminosity.III:
                if planet_type == PlanetType.ROCKY: possible_species.append("Croceum Anemone")
                if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]: possible_species.append("Rubeum Bioluminescent Anemone")
        if star_class == StarClass.B:
            if star_luminosity in [StarLuminosity.I, StarLuminosity.II, StarLuminosity.III] and planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]:
                possible_species.extend("Roseum Bioluminescent Anemone")
            if star_luminosity in [StarLuminosity.I, StarLuminosity.II, StarLuminosity.III] and planet_type in [PlanetType.ROCKY]:
                possible_species.extend("Roseum Anemone")
            if star_luminosity in [StarLuminosity.IV, StarLuminosity.V] and planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]:
                possible_species.append("Blatteum Bioluminescent Anemone")
            if star_luminosity in [StarLuminosity.IV, StarLuminosity.V] and planet_type in [PlanetType.ROCKY]:
                possible_species.append("Luteolum Anemone")
            if star_luminosity == StarLuminosity.VI:
                if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]: possible_species.append("Rubeum Bioluminescent Anemone")
                if planet_type == PlanetType.ROCKY: possible_species.append("Croceum Anemone")
        if star_class == StarClass.O:
            if planet_type in [PlanetType.ROCKY_ICE, PlanetType.ICY]:
                possible_species.append("Puniceum Anemone")
            if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC, PlanetType.ROCKY]:
                possible_species.append("Prasinum Bioluminescent Anemone")

    # Bacterium
    if "thin" in atmosphere:
        if "helium" in atmosphere:
            possible_species.append("Bacterium Nebulus")
        if "neon" in atmosphere:
            if any(opt in volcanism for opt in ("nitrogen", "ammonia")):
                possible_species.append("Bacterium Omentum")
            elif any(opt in volcanism for opt in ("carbon", "methane")):
                possible_species.append("Bacterium Scopulum")
            elif "water" in volcanism:
                possible_species.append("Bacterium Verrata")
            else:
                possible_species.append("Bacterium Acies")
        if "methane" in atmosphere:
            possible_species.append("Bacterium Bullaris")
        if "argon" in atmosphere:
            possible_species.append("Bacterium Vesicula")
        if "nitrogen" in atmosphere:
            possible_species.append("Bacterium Informem")
        if "oxygen" in atmosphere:
            possible_species.append("Bacterium Volu")
        if "ammonia" in atmosphere:
            possible_species.append("Bacterium Alcyoneum")
        if "carbon" in atmosphere:
            possible_species.append("Bacterium Aurasus")
        if any(opt in atmosphere for opt in ("water", "sulfur")):
            possible_species.append("Bacterium Cerbrus")
        if any(opt in volcanism for opt in ("helium", "metallic", "silicate")):
            possible_species.append("Bacterium Tela")

    # Bark Mound
    if (atmosphere in STR_LIST_NONE
            and (in_nebula or (volcanism not in STR_LIST_NONE))):
        possible_species.append("Bark Mound")

    # Brain Tree
    if volcanism not in STR_LIST_NONE and atmosphere in STR_LIST_NONE:
        if 200 <= mean_temp_k <= 500:
            possible_species.append("Brain Tree Roseum")
        if system_has_earth_like or system_has_gas_giant_with_water_life:
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

    # Cactoida
    if "thin" in atmosphere and planet_type in PT_GROUP_HMC_ROCKY and gravity and gravity <= 0.27:
        if (
                ("carbon" in atmosphere and "rich" not in atmosphere)
                or ("rich" in atmosphere and 180 <= mean_temp_k <= 195)
        ):
            possible_species.extend(["Cactoida Cortexum", "Cactoida Pullulanta"])
        if "ammonia" in atmosphere:
            possible_species.extend(["Cactoida Lapis", "Cactoida Peperatis"])
        if "water" in atmosphere:
            possible_species.append("Cactoida Vermis")

    # Clypeus
    if (planet_type in PT_GROUP_HMC_ROCKY
            and ("thin" in atmosphere and any(opt in atmosphere for opt in ("water", "carbon")))
            and mean_temp_k > 190 and gravity and gravity <= 0.27):
        possible_species.extend(["Clypeus Lacrimam", "Clypeus Margaritus"])
        # TODO: #221 Determine distance from parent star. currently the distance is just the one from the system entry point
        if distance_from_star_ls and distance_from_star_ls > 2500:
            possible_species.append("Clypeus Speculumi")

    # Concha
    if planet_type in PT_GROUP_HMC_ROCKY and (gravity and gravity <= 0.27) and "thin" in atmosphere:
        if "ammonia" in atmosphere:
            possible_species.append("Concha Aureolas")
        if "nitrogen" in atmosphere:
            possible_species.append("Concha Biconcavis")
        if "carbon" in atmosphere:
            if mean_temp_k < 190:
                possible_species.append("Concha Labiata")
            if 180 <= mean_temp_k <= 195:
                possible_species.append("Concha Renibus")
        if "water" in atmosphere:
            possible_species.append("Concha Renibus")

    # Crystalline Shard
    if (atmosphere in STR_LIST_NONE
            and star_class in [StarClass.A,
                               StarClass.F,
                               StarClass.G,
                               StarClass.K,
                               StarClass.M,
                               StarClass.S]
            and (system_has_earth_like
                 or system_has_ammonia_world
                 or system_has_water_giant
                 or system_has_gas_giant_with_water_life
                 or system_has_gas_giant_with_ammonia_life)
            and (distance_from_star_ls is None or distance_from_star_ls > 12000)):
        # TODO: #221 Determine distance from parent star. currently the distance is just the one from the system entry point
        possible_species.append("Crystalline Shard")

    # Electricae
    if planet_type == PlanetType.ICY and ("thin" in atmosphere and any(opt in atmosphere for opt in ("helium", "neon", "argon"))) and gravity and gravity <= 0.27:
        if ((star_class == StarClass.A and star_luminosity in [StarLuminosity.V, StarLuminosity.VI, StarLuminosity.VII])
                or star_class in [StarClass.O, StarClass.B, StarClass.N, StarClass.BlackHole, *SC_WHITE_DWARFS]):
            possible_species.append("Electricae Pluma")
        if in_nebula:
            possible_species.append("Electricae Radialem")

    # Fonticulua
    if atmosphere and "thin" in atmosphere and planet_type in PT_GROUP_ICE and gravity and gravity <= 0.27:
        if "neon" in atmosphere:
            possible_species.append("Fonticulua Segmentatus")
        if "methane" in atmosphere:
            possible_species.append("Fonticulua Digitos")
        if "argon" in atmosphere:
            if "rich" in atmosphere:
                possible_species.append("Fonticulua Upupam")
            else:
                possible_species.append("Fonticulua Campestris")
        if "nitrogen" in atmosphere:
            possible_species.append("Fonticulua Lapida")
        if "oxygen" in atmosphere:
            possible_species.append("Fonticulua Fluctus")

    # Frutexa
    if "thin" in atmosphere:
        if "ammonia" in atmosphere:
            if planet_type == PlanetType.ROCKY:
                possible_species.extend(["Frutexa Flabellum", "Frutexa Flammasis"])
            if planet_type == PlanetType.HMC:
                possible_species.append("Frutexa Metallicum")
        if "carbon" in atmosphere and mean_temp_k < 195:
            if planet_type == PlanetType.ROCKY:
                possible_species.extend(["Frutexa Fera", "Frutexa Acus"])
            if planet_type == PlanetType.HMC:
                possible_species.append("Frutexa Metallicum")
        if "sulfur" in atmosphere:
            possible_species.append("Frutexa Collum")
        if "water" in atmosphere and planet_type == PlanetType.ROCKY:
            possible_species.append("Frutexa Sponsae")

    # Fumerola
    if volcanism not in STR_LIST_NONE and "thin" in atmosphere and gravity and gravity <= 0.27:
        if (planet_type in PT_GROUP_ICE
                and "water" in volcanism):
            possible_species.append("Fumerola Aquatis")
        if (planet_type in PT_GROUP_ICE
                and any(opt in volcanism for opt in ("methane", "carbon"))):
            possible_species.append("Fumerola Carbosis")
        if (planet_type in PT_GROUP_HMC_ROCKY
                and any(opt in volcanism for opt in ("metallic", "rocky", "silicate"))):
            possible_species.append("Fumerola Extremus")
        if (planet_type in PT_GROUP_ICE
                and any(opt in volcanism for opt in ("nitrogen", "ammonia"))):
            possible_species.append("Fumerola Nitris")

    # Fungoida
    if gravity and gravity <= 0.27 and "thin" in atmosphere:
        if any(opt in atmosphere for opt in ("methane", "ammonia")):
            possible_species.append("Fungoida Setisis")
        if "argon" in atmosphere:
            possible_species.append("Fungoida Bullarum")
        if ("water" in atmosphere
                or ("carbon" in atmosphere and 180 <= mean_temp_k <= 195)):
            possible_species.extend(["Fungoida Gelata", "Fungoida Stabitis"])

    # Osseus
    if "thin" in atmosphere and gravity and gravity <= 0.27:
        if (planet_type == PlanetType.ROCKY_ICE
                and any(opt in atmosphere for opt in ("methane", "argon", "nitrogen"))):
            possible_species.append("Osseus Pumice")
        if planet_type in PT_GROUP_HMC_ROCKY:
            if "carbon" in atmosphere:
                if 180 <= mean_temp_k <= 195:
                    possible_species.extend(["Osseus Cornibus", "Osseus Pellebantus"])
                if 180 >= mean_temp_k <= 190:
                    possible_species.append("Osseus Fractus")
            if "water" in atmosphere:
                possible_species.append("Osseus Discus")
            if "ammonia" in atmosphere:
                possible_species.append("Osseus Spiralis")

    # Recepta
    if "thin sulfur" in atmosphere and gravity and gravity < 0.27:
        if planet_type in PT_GROUP_ICE:
            possible_species.append("Recepta Conditivus")
        if planet_type in PT_GROUP_HMC_ROCKY:
            possible_species.append("Recepta Deltahedronix")
        if planet_type in [*PT_GROUP_HMC_ROCKY, *PT_GROUP_ICE]:
            possible_species.append("Recepta Umbrux")

    # Sinuous Tuber
    if volcanism not in STR_LIST_NONE and atmosphere in STR_LIST_NONE:
        if "silicate magma" in volcanism:
            possible_species.append("Sinuous Tuber Roseus")
        if planet_type == PlanetType.ROCKY:
            possible_species.extend(["Sinuous Tuber Albidum", "Sinuous Tuber Caeruleum", "Sinuous Tuber Lindigoticum"])
        if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]:
            possible_species.extend(["Sinuous Tuber Blatteum", "Sinuous Tuber Prasinum", "Sinuous Tuber Violaceum", "Sinuous Tuber Viride"])

    # Stratum
    if "thin" in atmosphere:
        if (planet_type == PlanetType.HMC
                and mean_temp_k > 165):
            possible_species.append("Stratum Tectonicas")
        if planet_type == PlanetType.ROCKY:
            if "ammonia" in atmosphere and mean_temp_k > 165:
                possible_species.extend(["Stratum Paleas", "Stratum Laminamus"])
            if "water" in atmosphere:
                possible_species.append("Stratum Paleas")
            if "carbon" in atmosphere:
                if mean_temp_k > 165:
                    possible_species.append("Stratum Paleas")
                if mean_temp_k > 190:
                    possible_species.extend(["Stratum Cucumisis", "Stratum Frigus"])
                if 165 <= mean_temp_k <= 190:
                    possible_species.extend(["Stratum Limaxus", "Stratum Excutitus"])
            if "sulfur" in atmosphere:
                if mean_temp_k > 165:
                    possible_species.append("Stratum Araneamus")
                if mean_temp_k > 190:
                    possible_species.extend(["Stratum Cucumisis", "Stratum Frigus"])
                if 165 <= mean_temp_k <= 190:
                    possible_species.extend(["Stratum Limaxus", "Stratum Excutitus"])

    # Tubus
    if "thin" in atmosphere and gravity and gravity <= 0.15:
        if planet_type == PlanetType.HMC and any(opt in atmosphere for opt in ("ammonia", "carbon")):
            possible_species.append("Tubus Sororibus")
        if planet_type == PlanetType.ROCKY:
            if "ammonia" in atmosphere:
                possible_species.append("Tubus Rosarium")
            if "carbon" in atmosphere:
                possible_species.append("Tubus Cavas")
            if "carbon" in atmosphere and 160 <= mean_temp_k <= 190:
                possible_species.extend(["Tubus Compagibus", "Tubus Conifer"])

    # Tussock
    if planet_type == PlanetType.ROCKY and "thin" in atmosphere and gravity and gravity <= 0.27:
        if "carbon" in atmosphere:
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
        if any(opt in atmosphere for opt in ("methane", "argon")):
            possible_species.append("Tussock Capillum")
        if "ammonia" in atmosphere:
            possible_species.extend(["Tussock Catena", "Tussock Cultro", "Tussock Divisa"])
        if "sulfur" in atmosphere:
            possible_species.append("Tussock Stigmasis")
        if "water" in atmosphere:
            possible_species.append("Tussock Virgam")

    return possible_species