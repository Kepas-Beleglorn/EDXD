from typing import List, Optional, Dict, Any, Set
from EDXD.data_handler.helper.system_params import (
    StarClass, StarLuminosity, Atmosphere, PlanetType, Volcanism,
    ATM_GROUP_CARBON, ATM_GROUP_WATER, ATM_GROUP_METHANE, ATM_GROUP_NEON,
    ATM_GROUP_ARGON, ATM_GROUP_RARE_GAS, ATM_GROUP_ALL_BACTERIA,
    PT_GROUP_LANDABLE_ROCKY, PT_GROUP_HMC_ROCKY, PT_GROUP_ICE,
    VOLC_GROUP_GAS_ICE, VOLC_GROUP_CARBON_ICE, VOLC_GROUP_HOT_ROCK, VOLC_GROUP_INERT
)
from EDXD.data_handler.helper.bio_helper import (
    get_genus_value,
    get_scan_range_for_species,
    SPECIES_TO_CODEX  # We need this reverse map
)


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
        "$Codex_Ent_Tubus_Genus_Name;": "Tubas",  # Note: Species are "Tubas ..."
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

        is_star = False
        if not b.parents:
            is_star = True
        elif len(b.parents) > 0 and isinstance(b.parents[0], dict) and "Null" in b.parents[0]:
            is_star = True

        if is_star and star_class_enum is None:
            s_type = b.body_type
            star_class_enum = _safe_get_enum(s_type, StarClass, None)
            if star_class_enum is None and "_" in s_type:
                star_class_enum = _safe_get_enum(s_type.split("_")[0], StarClass, None)
            lum_raw = getattr(b, 'luminosity', None) or getattr(b, 'raw_luminosity', None)
            if lum_raw:
                star_luminosity_enum = _safe_get_enum(lum_raw, StarLuminosity, None)

    in_nebula = False

    for body_id, body in model_bodies.items():
        if not getattr(body, 'landable', False):
            continue

        if not getattr(body, 'biosignals', None):
            continue

        # 2. Map Body Data
        atm_raw = _safe_get_atmosphere_type(body.atmosphere)
        atm_enum = _safe_get_enum(atm_raw, Atmosphere, Atmosphere.NONE)
        pt_raw = body.body_type if isinstance(body.body_type, str) else str(body.body_type)
        pt_enum = _safe_get_enum(pt_raw, PlanetType, PlanetType.ROCKY)
        volc_raw = getattr(body, 'volcanism', None) or "None"
        volc_enum = _safe_get_enum(volc_raw, Volcanism, Volcanism.NONE)

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
                planet_type=pt_enum, atmosphere=atm_enum, mean_temp_k=mean_temp,
                star_class=star_class_enum, star_luminosity=star_luminosity_enum,
                volcanism=volc_enum, gravity=gravity, in_nebula=in_nebula,
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
                # If confirmed, probability is 100%. Otherwise calculate.
                if species_name in confirmed_species_names:
                    prob = 1.0
                    is_confirmed = True
                else:
                    prob = calculate_probability(species_name, pt_enum, atm_enum, mean_temp, volc_enum)
                    is_confirmed = False

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
    if isinstance(body_atmosphere, dict): return body_atmosphere.get("type", "None") or "None"
    if hasattr(body_atmosphere, "type"):
        val = getattr(body_atmosphere, "type", None)
        return val if val else "None"
    if isinstance(body_atmosphere, str): return body_atmosphere if body_atmosphere else "None"
    return "None"


def _safe_get_enum(value: Optional[str], enum_class: Any, default: Any) -> Any:
    if value is None: return default
    try:
        return enum_class(value)
    except ValueError:
        return default


def calculate_probability(species_name: str, planet_type: PlanetType, atmosphere: Atmosphere,
                          mean_temp_k: float, volcanism: Optional[Volcanism]) -> float:
    score = 0.5
    if "Aleoida" in species_name:
        if 175 <= mean_temp_k <= 195: score += 0.3
    elif "Tussock" in species_name:
        if 145 <= mean_temp_k <= 195: score += 0.3
    elif "Stratum" in species_name:
        if 165 <= mean_temp_k <= 190: score += 0.2
    else:
        score += 0.1
    if atmosphere in [Atmosphere.SULPHUR_DIOXIDE, Atmosphere.AMMONIA, Atmosphere.HELIUM]:
        score += 0.15
    if volcanism and volcanism != Volcanism.NONE:
        if "Fumerola" in species_name or "Sinuous" in species_name:
            score += 0.25
    return min(score, 1.0)


def estimate_biosigns(
        planet_type: PlanetType, atmosphere: Atmosphere, mean_temp_k: float,
        star_class: Optional[StarClass] = None, star_luminosity: Optional[StarLuminosity] = None,
        volcanism: Optional[Volcanism] = None, gravity: Optional[float] = None,
        in_nebula: bool = False, system_has_earth_like: bool = False,
        system_has_ammonia_world: bool = False, system_has_water_giant: bool = False,
        system_has_gas_giant_with_water_life: bool = False,
        system_has_gas_giant_with_ammonia_life: bool = False,
        distance_from_star_ls: Optional[float] = None,
) -> List[str]:
    possible_species: List[str] = []

    # Aleoida
    if planet_type in PT_GROUP_HMC_ROCKY and gravity is not None and gravity <= 0.27:
        if atmosphere in ATM_GROUP_CARBON:
            if 175 <= mean_temp_k <= 180: possible_species.append("Aleoida Arcus")
            if 180 <= mean_temp_k <= 190: possible_species.append("Aleoida Coronamus")
            if 190 <= mean_temp_k <= 195: possible_species.append("Aleoida Gravis")
        if atmosphere == Atmosphere.AMMONIA:
            possible_species.extend(["Aleoida Laminiae", "Aleoida Spica"])

    # Amphora Plant
    if (atmosphere == Atmosphere.NONE and star_class == StarClass.A and
            (system_has_earth_like or system_has_ammonia_world or system_has_water_giant or
             system_has_gas_giant_with_water_life or system_has_gas_giant_with_ammonia_life)):
        possible_species.append("Amphora Plant")

    # Anemone (Mapped to Clypeus genus)
    if star_class in [StarClass.A, StarClass.B, StarClass.O]:
        if star_class == StarClass.A:
            if star_luminosity == StarLuminosity.III:
                if planet_type == PlanetType.ROCKY: possible_species.append("Croceum Anemone")
                if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]: possible_species.append("Rubeum Bioluminescent Anemone")
        if star_class == StarClass.B:
            if star_luminosity in [StarLuminosity.I, StarLuminosity.II, StarLuminosity.III] and planet_type in [PlanetType.METAL_RICH, PlanetType.HMC, PlanetType.ROCKY]:
                possible_species.extend(["Roseum Bioluminescent Anemone", "Roseum Anemone"])
            if star_luminosity in [StarLuminosity.IV, StarLuminosity.V] and planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]:
                possible_species.append("Blatteum Bioluminescent Anemone")
            if star_luminosity == StarLuminosity.VI:
                if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]: possible_species.append("Rubeum Bioluminescent Anemone")
                if planet_type == PlanetType.ROCKY: possible_species.append("Croceum Anemone")
        if star_class == StarClass.O:
            if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC, PlanetType.ROCKY, PlanetType.ROCKY_ICE, PlanetType.ICY]:
                possible_species.append("Puniceum Anemone")
            if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC, PlanetType.ROCKY]:
                possible_species.append("Prasinum Bioluminescent Anemone")

    # Bacterium
    if atmosphere in ATM_GROUP_ALL_BACTERIA:
        if atmosphere == Atmosphere.HELIUM: possible_species.append("Bacterium Nebulus")
        if atmosphere in ATM_GROUP_NEON:
            if volcanism and volcanism.value.startswith(("nitrogen", "ammonia")):
                possible_species.append("Bacterium Omentum")
            elif volcanism and volcanism.value.startswith(("carbon", "methane")):
                possible_species.append("Bacterium Scopulum")
            elif volcanism and volcanism.value.startswith("water"):
                possible_species.append("Bacterium Verrata")
            else:
                possible_species.append("Bacterium Acies")
        if atmosphere in ATM_GROUP_METHANE: possible_species.append("Bacterium Bullaris")
        if atmosphere in ATM_GROUP_ARGON: possible_species.append("Bacterium Vesicula")
        if atmosphere == Atmosphere.NITROGEN: possible_species.append("Bacterium Informem")
        if atmosphere == Atmosphere.OXYGEN: possible_species.append("Bacterium Volu")
        if atmosphere == Atmosphere.AMMONIA: possible_species.append("Bacterium Alcyoneum")
        if atmosphere in ATM_GROUP_CARBON: possible_species.append("Bacterium Aurasus")
        if atmosphere in [Atmosphere.WATER, Atmosphere.SULPHUR_DIOXIDE]: possible_species.append("Bacterium Cerbrus")
        if volcanism and volcanism.value in ["None", "Helium", "Iron", "Silicate"]: possible_species.append("Bacterium Tela")

    # Bark Mound
    if atmosphere == Atmosphere.NONE and in_nebula: possible_species.append("Bark Mound")

    # Brain Tree
    if (planet_type in PT_GROUP_LANDABLE_ROCKY and (200 <= mean_temp_k <= 500 or atmosphere in [Atmosphere.AMMONIA, Atmosphere.WATER, Atmosphere.WATER_RICH] or atmosphere in ATM_GROUP_WATER)):
        if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC] and 300 <= mean_temp_k <= 500: possible_species.append("Brain Tree Aureum")
        if planet_type == PlanetType.ROCKY and 200 <= mean_temp_k <= 300: possible_species.append("Brain Tree Gypseeum")
        if planet_type in [PlanetType.HMC, PlanetType.ROCKY] and 300 <= mean_temp_k <= 500: possible_species.append("Brain Tree Lindigoticum")
        if planet_type == PlanetType.ROCKY and 300 <= mean_temp_k <= 500: possible_species.append("Brain Tree Lividum")
        if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]: possible_species.extend(["Brain Tree Ostrinum", "Brain Tree Puniceum"])
        if planet_type == PlanetType.ROCKY_ICE and 100 <= mean_temp_k <= 270: possible_species.append("Brain Tree Viride")
        if (system_has_earth_like or system_has_gas_giant_with_water_life) or atmosphere in [Atmosphere.AMMONIA, Atmosphere.WATER, Atmosphere.WATER_RICH] or atmosphere in ATM_GROUP_WATER:
            possible_species.append("Brain Tree Roseum")

    # Cactoida
    if planet_type in PT_GROUP_HMC_ROCKY:
        if atmosphere in ATM_GROUP_CARBON: possible_species.extend(["Cactoida Cortexum", "Cactoida Pullulanta"])
        if atmosphere == Atmosphere.AMMONIA: possible_species.extend(["Cactoida Lapis", "Cactoida Peperatis"])
        if atmosphere in ATM_GROUP_WATER: possible_species.append("Cactoida Vermis")

    # Clypeus
    if (planet_type in PT_GROUP_HMC_ROCKY and (atmosphere in [Atmosphere.WATER, Atmosphere.WATER_RICH] or atmosphere in ATM_GROUP_CARBON) and mean_temp_k > 190 and (
            gravity is None or gravity <= 0.27)):
        possible_species.extend(["Clypeus Lacrimam", "Clypeus Margaritus"])
        if distance_from_star_ls and distance_from_star_ls > 2500: possible_species.append("Clypeus Speculumi")

    # Concha
    if planet_type in PT_GROUP_HMC_ROCKY:
        if atmosphere == Atmosphere.AMMONIA: possible_species.append("Concha Aureolas")
        if atmosphere == Atmosphere.NITROGEN: possible_species.append("Concha Biconcavis")
        if atmosphere in ATM_GROUP_CARBON and mean_temp_k < 190: possible_species.append("Concha Labiata")
        if (atmosphere in [Atmosphere.WATER, Atmosphere.WATER_RICH] or atmosphere in ATM_GROUP_CARBON) and 180 <= mean_temp_k <= 195: possible_species.append("Concha Renibus")

    # Crystalline Shard
    if (atmosphere == Atmosphere.NONE and star_class in [StarClass.A, StarClass.F, StarClass.G, StarClass.K, StarClass.M, StarClass.S] and
            (system_has_earth_like or system_has_ammonia_world or system_has_water_giant or system_has_gas_giant_with_water_life or system_has_gas_giant_with_ammonia_life) and
            (distance_from_star_ls is None or distance_from_star_ls > 12000)):
        possible_species.append("Crystalline Shard")

    # Electricae
    if planet_type == PlanetType.ICY and atmosphere in ATM_GROUP_RARE_GAS and (gravity is None or gravity <= 0.27):
        if star_class == StarClass.A and star_luminosity in [StarLuminosity.V, StarLuminosity.VI]: possible_species.append("Electricae Pluma")
        if in_nebula: possible_species.append("Electricae Radialem")

    # Fonticulua
    if atmosphere == Atmosphere.ARGON: possible_species.append("Fonticulua Campestris")
    if atmosphere == Atmosphere.METHANE: possible_species.append("Fonticulua Digitos")
    if atmosphere == Atmosphere.OXYGEN: possible_species.append("Fonticulua Fluctus")
    if atmosphere == Atmosphere.NITROGEN: possible_species.append("Fonticulua Lapida")
    if atmosphere in ATM_GROUP_NEON: possible_species.append("Fonticulua Segmentatus")
    if atmosphere == Atmosphere.ARGON_RICH: possible_species.append("Fonticulua Upupam")

    # Frutexa
    if planet_type == PlanetType.ROCKY:
        if atmosphere in ATM_GROUP_CARBON and mean_temp_k < 195: possible_species.extend(["Frutexa Fera", "Frutexa Acus"])
        if atmosphere == Atmosphere.AMMONIA: possible_species.extend(["Frutexa Flabellum", "Frutexa Flammasis"])
        if (atmosphere == Atmosphere.AMMONIA or atmosphere in ATM_GROUP_CARBON) and mean_temp_k < 195: possible_species.append("Frutexa Metallicum")
        if atmosphere in ATM_GROUP_WATER: possible_species.append("Frutexa Sponsae")

    # Fumerola
    if volcanism and volcanism != Volcanism.NONE:
        if planet_type in PT_GROUP_ICE and "water" in volcanism.value: possible_species.append("Fumerola Aquatis")
        if planet_type in PT_GROUP_ICE and ("methane" in volcanism.value or "carbon dioxide" in volcanism.value): possible_species.append("Fumerola Carbosis")
        if planet_type in PT_GROUP_HMC_ROCKY and volcanism in VOLC_GROUP_HOT_ROCK: possible_species.append("Fumerola Extremus")
        if planet_type in PT_GROUP_ICE and ("nitrogen" in volcanism.value or "ammonia" in volcanism.value): possible_species.append("Fumerola Nitris")

    # Fungoida
    if planet_type in PT_GROUP_HMC_ROCKY:
        if atmosphere in ATM_GROUP_ARGON: possible_species.append("Fungoida Bullarum")
        if (atmosphere in ATM_GROUP_CARBON or atmosphere in ATM_GROUP_WATER) and 180 <= mean_temp_k <= 195: possible_species.append("Fungoida Gelata")
        if atmosphere in ATM_GROUP_METHANE or atmosphere == Atmosphere.AMMONIA: possible_species.append("Fungoida Setisis")
        if (atmosphere in ATM_GROUP_CARBON or atmosphere in ATM_GROUP_WATER) and 180 <= mean_temp_k <= 195: possible_species.append("Fungoida Stabitis")

    # Osseus
    if planet_type in PT_GROUP_HMC_ROCKY:
        if atmosphere in ATM_GROUP_CARBON and 180 <= mean_temp_k <= 195: possible_species.extend(["Osseus Cornibus", "Osseus Fractus", "Osseus Pellebantus"])
        if atmosphere in ATM_GROUP_WATER: possible_species.append("Osseus Discus")
        if atmosphere == Atmosphere.AMMONIA: possible_species.append("Osseus Spiralis")
        if planet_type == PlanetType.ROCKY_ICE and (atmosphere in ATM_GROUP_METHANE or atmosphere in ATM_GROUP_ARGON or atmosphere == Atmosphere.NITROGEN):
            possible_species.append("Osseus Pumice")

    # Recepta
    if atmosphere == Atmosphere.SULPHUR_DIOXIDE and (gravity is None or gravity < 0.27):
        if planet_type in PT_GROUP_ICE: possible_species.append("Recepta Conditivus")
        if planet_type in PT_GROUP_HMC_ROCKY: possible_species.extend(["Recepta Deltahedronix", "Recepta Umbrux"])

    # Sinuous Tuber
    if volcanism and volcanism != Volcanism.NONE and atmosphere == Atmosphere.NONE:
        if planet_type == PlanetType.ROCKY: possible_species.extend(["Sinuous Tuber Albidum", "Sinuous Tuber Caeruleum", "Sinuous Tuber Lindigoticum"])
        if planet_type in [PlanetType.METAL_RICH, PlanetType.HMC]: possible_species.extend(["Sinuous Tuber Blatteum", "Sinuous Tuber Prasinum", "Sinuous Tuber Violaceum", "Sinuous Tuber Viride"])
        if "silicate vapour" in volcanism.value: possible_species.append("Sinuous Tuber Roseus")

    # Stratum
    if planet_type == PlanetType.ROCKY:
        if (atmosphere == Atmosphere.SULPHUR_DIOXIDE or atmosphere in ATM_GROUP_CARBON) and mean_temp_k > 165:
            possible_species.extend(["Stratum Araneamus", "Stratum Cucumisis", "Stratum Excutitus", "Stratum Frigus"])
        if atmosphere == Atmosphere.AMMONIA and mean_temp_k > 165: possible_species.append("Stratum Laminamus")
        if (atmosphere == Atmosphere.SULPHUR_DIOXIDE or atmosphere in ATM_GROUP_CARBON) and 165 <= mean_temp_k <= 190: possible_species.append("Stratum Limaxus")
        if (atmosphere == Atmosphere.AMMONIA or atmosphere in ATM_GROUP_WATER) and mean_temp_k > 165: possible_species.append("Stratum Paleas")
    if planet_type == PlanetType.HMC and mean_temp_k > 165: possible_species.append("Stratum Tectonicas")

    # Tubus
    if planet_type in PT_GROUP_HMC_ROCKY:
        if atmosphere in ATM_GROUP_CARBON and 160 <= mean_temp_k <= 190: possible_species.extend(["Tubus Cavas", "Tubus Compagibus", "Tubus Conifer"])
        if atmosphere == Atmosphere.AMMONIA and mean_temp_k > 160: possible_species.append("Tubus Rosarium")
        if planet_type == PlanetType.HMC and (atmosphere == Atmosphere.AMMONIA or atmosphere in ATM_GROUP_CARBON) and 160 <= mean_temp_k <= 190: possible_species.append("Tubus Sororibus")

    # Tussock
    if planet_type == PlanetType.ROCKY:
        if atmosphere in ATM_GROUP_CARBON:
            if 175 <= mean_temp_k <= 180: possible_species.append("Tussock Albata")
            if 180 <= mean_temp_k <= 190: possible_species.append("Tussock Caputus")
            if 160 <= mean_temp_k <= 170: possible_species.append("Tussock Ignis")
            if 145 <= mean_temp_k <= 155: possible_species.append("Tussock Pennata")
            if mean_temp_k < 195: possible_species.extend(["Tussock Pennatis", "Tussock Propagito"])
            if 170 <= mean_temp_k <= 175: possible_species.append("Tussock Serrati")
            if 190 <= mean_temp_k <= 195: possible_species.append("Tussock Triticum")
            if 155 <= mean_temp_k <= 160: possible_species.append("Tussock Ventusa")
        if atmosphere in ATM_GROUP_METHANE or atmosphere in ATM_GROUP_ARGON: possible_species.append("Tussock Capillum")
        if atmosphere == Atmosphere.AMMONIA: possible_species.extend(["Tussock Catena", "Tussock Cultro", "Tussock Divisa"])
        if atmosphere == Atmosphere.SULPHUR_DIOXIDE: possible_species.append("Tussock Stigmasis")
        if atmosphere in ATM_GROUP_WATER: possible_species.append("Tussock Virgam")

    return possible_species