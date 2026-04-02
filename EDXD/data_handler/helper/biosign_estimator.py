from typing import List, Optional, Dict, Any
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
        pressure_atm = getattr(body, 'pressure', 0.0)

        # 3. Check DSS & Codex Data
        bio_found_data = getattr(body, 'bio_found', {})

        scanned_genus_localised = set()
        scanned_genus_species_localised = set()
        for genus in bio_found_data.items():
            scanned_genus_localised.add(genus[1].localised)
            if genus[1].species_localised is not None:
                scanned_genus_species_localised.add(genus[1].species_localised)
            elif genus[1].variant_localised is not None:
                scanned_genus_species_localised.add(str(genus[1].variant_localised).split(" - ")[0])

        # New: Track Confirmed Species
        confirmed_species_names = set()
        confirmed_variants = {}  # Map species_name -> color

        if scanned_genus_localised:
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

        if potential_species:
            # CODEX PHASE: We know exactly what is here.
            # 1. Keep ONLY the confirmed species.
            # 2. Discard all other candidates of the same genus.
            for sp in potential_species:
                if any(sp.startswith(p) for p in scanned_genus_species_localised):
                    final_species.append(sp)
                # Optional: If you want to keep "theoretical" siblings until 100% complete,
                # you can skip the 'else' block. But usually, 1 species found = others impossible.
        if scanned_genus_localised:
            # DSS PHASE (Genus known, species unknown): Filter by Genus Prefix (as before)
            allowed_prefixes = set()
            for item in scanned_genus_localised:
                is_confirmed = False
                for confirmed in confirmed_species_names:
                    if item in confirmed:
                        is_confirmed = True
                        break
                if not is_confirmed:
                    allowed_prefixes.add(item)
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
                prob = 0.0
                if species_name in confirmed_species_names or any(species_name.startswith(p) for p in scanned_genus_localised):
                    # check if found species is already unique in list
                    current_genus = species_name.split(" ")[0]
                    genus_occurrence = 0
                    for fs in final_species:
                        if fs.startswith(current_genus):
                            genus_occurrence += 1
                    if genus_occurrence == 1:
                        prob = 1.0
                    else:
                        # Inside the loop where you calculate prob:
                        prob = calculate_probability(
                            species_name=species_name,
                            planet_type=pt_enum,
                            #atmosphere=atm_raw,
                            pressure_atm=pressure_atm,
                            mean_temp_k=mean_temp,
                            #volcanism=volc_raw,
                            gravity=gravity,  # Pass these new args
                            #star_class=star_class_enum,
                            #star_luminosity=star_luminosity_enum
                        )

                results[body_id].append({
                    "body_id": body_id,
                    "body_name": body_name,
                    "name": species_name,
                    "base_value": get_genus_value(species_name),
                    "scan_range": get_scan_range_for_species(species_name),
                    "probability": round(prob, 2),
                    "confirmed_by_dss": scanned_genus_localised,  # True if only genus known
                    "confirmed_by_codex": species_name in scanned_genus_localised,  # True if exact species known
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
        pressure_atm: float,
        mean_temp_k: float,
        gravity: Optional[float] = None,
) -> float:
    """
    Calculates a relative probability score (0.0 to 1.0).
    Returns 0.0 if hard constraints (Gravity, Atmosphere, Star) are violated.
    """
    score = 0.5

    if "Aleoida" in species_name:
        score += score_aleoida_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Amphora" in species_name:
        score += score_amphora_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Anemone" in species_name:
        score += score_anemone_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Bacteria" in species_name:
        score += score_bacteria_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Bark" in species_name:
        score += score_bark_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Brain" in species_name:
        score += score_brain_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Cactoida" in species_name:
        score += score_cactoida_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Clypeus" in species_name:
        score += score_clypeus_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Concha" in species_name:
        score += score_concha_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Crystalline" in species_name:
        score += score_crystal_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Electricae" in species_name:
        score += score_electricae_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Fonticulua" in species_name:
        score += score_fonticulua_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

    if "Frutexa" in species_name:
        score += score_frutexa_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type)

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
    if "thin" in atmosphere and planet_type in PT_GROUP_HMC_ROCKY and gravity is not None and gravity <= 0.28:
        if "carbon dioxide" in atmosphere:
            if 175 <= mean_temp_k <= 180:
                possible_species.append("Aleoida Arcus")
            if 179 <= mean_temp_k <= 190:
                possible_species.append("Aleoida Coronamus")
            if 190 <= mean_temp_k <= 197:
                possible_species.append("Aleoida Gravis")
        if "ammonia" in atmosphere:
            if 152 <= mean_temp_k <= 177:
                possible_species.append("Aleoida Laminiae")
            if 170 <= mean_temp_k <= 177:
                possible_species.append("Aleoida Spica")

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
    if "thin" in atmosphere and planet_type in PT_GROUP_HMC_ROCKY and gravity and gravity <= 0.28:
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
    if planet_type in PT_GROUP_HMC_ROCKY and (gravity and gravity <= 0.28) and "thin" in atmosphere:
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
    if planet_type == PlanetType.ICY and ("thin" in atmosphere and any(opt in atmosphere for opt in ("helium", "neon", "argon"))) and gravity and gravity <= 0.28:
        if ((star_class == StarClass.A and star_luminosity in [StarLuminosity.V, StarLuminosity.VI, StarLuminosity.VII])
                or star_class in [StarClass.O, StarClass.B, StarClass.N, StarClass.BlackHole, *SC_WHITE_DWARFS]):
            possible_species.append("Electricae Pluma")
        if in_nebula:
            possible_species.append("Electricae Radialem")

    # Fonticulua
    if atmosphere and "thin" in atmosphere and planet_type in PT_GROUP_ICE and gravity and gravity <= 0.28:
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
    if volcanism not in STR_LIST_NONE and "thin" in atmosphere and gravity and gravity <= 0.28:
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
    if gravity and gravity <= 0.28 and "thin" in atmosphere:
        if any(opt in atmosphere for opt in ("methane", "ammonia")):
            possible_species.append("Fungoida Setisis")
        if "argon" in atmosphere:
            possible_species.append("Fungoida Bullarum")
        if ("water" in atmosphere
                or ("carbon" in atmosphere and 180 <= mean_temp_k <= 195)):
            possible_species.extend(["Fungoida Gelata", "Fungoida Stabitis"])

    # Osseus
    if "thin" in atmosphere and gravity and gravity <= 0.28:
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
    if "thin sulfur" in atmosphere and gravity and gravity < 0.28:
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
    if "thin" in atmosphere and gravity and gravity <= 0.16:
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
    if planet_type in [PlanetType.ROCKY, PlanetType.HMC] and "thin" in atmosphere and gravity and gravity <= 0.28:
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

# Calculate probabilities
def score_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType, modes: dict) -> float:
    score = 0.0
    name_lower = species_name.lower()

    # Identify the target mode for this species
    target = None
    for key, val in modes.items():
        if key in name_lower:
            target = val
            break

    # Safety fallback if species name is unrecognized
    if target is None:
        return 0.0

    target_temp, tolerance_temp, target_press, tolerance_pressure, target_grav, tolerance_gravity, target_planet_type = target

    # Check planet type(s)
    if planet_type in target_planet_type:
        score += 0.075
    else:
        score += 0.025

    # Check Temperature (Tolerance: ±{tolerance_temp} K)
    if target_temp is not None:
        if abs(mean_temp_k - target_temp) <= tolerance_temp:
            score += 0.1
        else:
            score += 0.05

    # Check Pressure (Tolerance: ±{tolerance_pressure} atm)
    if target_press is not None:
        if abs(pressure_atm - target_press) <= tolerance_pressure:
            score += 0.1
        else:
            score += 0.05

    # Check Gravity (Tolerance: ±{tolerance_gravity} g)
    if target_grav is not None:
        if abs(gravity - target_grav) <= tolerance_gravity:
            score += 0.1
        else:
            score += 0.05

    return score

def score_aleoida_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "arcus"     : (177.0, 5.0, 0.024, 0.005,  0.12, 0.05, [PlanetType.HMC, PlanetType.ICY, PlanetType.ROCKY]),
        "coronamus" : (181.0, 5.0, 0.035, 0.005,  0.17, 0.05, [PlanetType.HMC, PlanetType.ROCKY, PlanetType.ICY]),
        "gravis"    : (190.1, 5.0, 0.074, 0.005,  0.21, 0.05, [PlanetType.HMC, PlanetType.ROCKY, PlanetType.ICY, PlanetType.ROCKY_ICE]),
        "laminiae"  : (171.0, 5.0, 0.001, 0.0005, 0.14, 0.05, [PlanetType.HMC, PlanetType.ROCKY]),
        "spica"     : (173.0, 5.0, 0.001, 0.0005, 0.16, 0.05, [PlanetType.HMC, PlanetType.ROCKY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_amphora_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "plant"     : (1090.0, 70.0, None, None,  1.0, 0.9, [PlanetType.HMC, PlanetType.METAL_RICH, PlanetType.ROCKY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_anemone_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "blatteum bioluminescent"   : (1000.0, 500.0, 0.0035,  0.0035,  1.42,   0.66,   [PlanetType.HMC, PlanetType.METAL_RICH, PlanetType.ROCKY]),
        "croceum"                   : (390.0,  50.0,  0.0035,  0.0035,  0.09,   0.05,   [PlanetType.HMC, PlanetType.ROCKY]),
        "luteolum"                  : (349.0,  75.0,  0.0035,  0.0035,  0.1,    0.06,   [PlanetType.HMC, PlanetType.ROCKY]),
        "prasinum bioluminescent"   : (1275.0, 475.0, 0.0035,  0.0035,  0.5665, 0.5295, [PlanetType.HMC, PlanetType.METAL_RICH, PlanetType.ROCKY]),
        "puniceum"                  : (550.0,  150.0, 0.00075, 0.00075, 2.25,   0.35,   [PlanetType.ICY]),
        "roseum"                    : (410.0,  30.0,  0.003,   0.003,   0.095,  0.051,  [PlanetType.HMC, PlanetType.ROCKY]),
        "roseum bioluminescent"     : (970.0,  480.0, 0.0035,  0.0035,  1.305,  0.495,  [PlanetType.HMC, PlanetType.METAL_RICH, PlanetType.ROCKY]),
        "rubeum bioluminescent"     : (895.0,  245.0, 0.0035,  0.0035,  1.17,   0.38,   [PlanetType.HMC, PlanetType.METAL_RICH, PlanetType.ROCKY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_bacteria_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity, PlanetType)
    modes = {
        "acies"     : (22.0,    20.0,   0.015,  0.005,  0.4,    0.1,    [PlanetType.ICY]),
        "alcyoneum" : (168.0,   25.0,   0.001,  0.001,  0.15,   0.05,   [PlanetType.HMC, PlanetType.ROCKY, PlanetType.ICY]),
        "aurasus"   : (177.0,   25.0,   0.1,    0.05,   0.2,    0.01,   [PlanetType.HMC, PlanetType.ROCKY, PlanetType.ICY]),
        "bullaris"  : (95.0,    10.0,   0.045,  0.005,  0.05,   0.005,  [PlanetType.ICY]),
        "cerbrus"   : (180.0,   30.0,   0.05,   0.005,  0.3,    0.05,   [PlanetType.HMC, PlanetType.ROCKY, PlanetType.ICY, PlanetType.ROCKY_ICE]),
        "informem"  : (75.0,    20.0,   0.01,   0.005,  0.27,   0.05,   [PlanetType.HMC, PlanetType.ICY]),
        "nebulus"   : (20.0,    15.0,   0.08,   0.03,   0.5,    0.1,    [PlanetType.ICY]),
        "omentum"   : (30.0,    20.0,   0.005,  0.002,  0.4,    0.1,    [PlanetType.ICY]),
        "scopulum"  : (30.0,    20.0,   0.005,  0.002,  0.4,    0.1,    [PlanetType.ICY]),
        "tela"      : (350.0,   50.0,   0.005,  0.002,  0.5,    0.1,    [PlanetType.HMC, PlanetType.ROCKY, PlanetType.ICY]),
        "verrata"   : (40.0,    20.0,   0.005,  0.002,  0.5,    0.1,    [PlanetType.ICY]),
        "vesicula"  : (50.0,    20.0,   0.005,  0.002,  0.2,    0.05,   [PlanetType.HMC, PlanetType.ICY]),
        "volu"      : (170.0,   25.0,   0.05,   0.005,  0.4,    0.1,    [PlanetType.HMC, PlanetType.ICY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_bark_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "mounds"     : (250.0, 45.0, 69.0, 69.0,  0.168, 0.142, [PlanetType.HMC, PlanetType.ICY, PlanetType.ROCKY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_brain_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "aureum"        : (571.0, 269.0, 0.00185, 0.00185,  0.198,  0.162,  [PlanetType.HMC, PlanetType.ROCKY]),
        "gypseeum"      : (226.0, 26.0,  0.0035,  0.0035,   0.1,    0.06,   [PlanetType.ROCKY]),
        "lindigoticum"  : (475.0, 25.0,  0.0004,  0.0004,   0.152,  0.108,  [PlanetType.HMC, PlanetType.ROCKY]),
        "lividum"       : (503.0, 272.0, 0.0004,  0.0004,   0.084,  0.055,  [PlanetType.HMC, PlanetType.ROCKY]),
        "ostrinum"      : (685.0, 222.0, 0.0004,  0.0004,   0.7675, 0.7325, [PlanetType.HMC, PlanetType.ROCKY, PlanetType.ICY]),
        "puniceum"      : (748.0, 292.0, 0.0004,  0.0004,   0.82,   0.78,   [PlanetType.HMC, PlanetType.ROCKY]),
        "roseum"        : (392.5, 277.5, 0.0004,  0.0004,   0.201,  0.174,  [PlanetType.HMC, PlanetType.ROCKY, PlanetType.ICY]),
        "viride"        : (113.0, 13.0,  0.0004,  0.0004,   0.079,  0.044,  [PlanetType.ROCKY_ICE, PlanetType.ICY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_cactoida_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "cortexum"      : (188.0, 9.0,   0.06,   0.05,   0.2,  0.05, [PlanetType.HMC, PlanetType.ROCKY, PlanetType.ICY]),
        "lapis"         : (170.0, 15.0,  0.001,  0.001,  0.15, 0.05, [PlanetType.HMC, PlanetType.ROCKY]),
        "peperatis"     : (170.0, 10.0,  0.0015, 0.007,  0.27, 0.1,  [PlanetType.HMC, PlanetType.ROCKY]),
        "pullulanta"    : (188.0, 9.0,   0.06,   0.04,   0.15, 0.12, [PlanetType.HMC, PlanetType.ROCKY]),
        "vermis"        : (250.0, 200.0, 0.05,   0.05,   0.15, 0.12, [PlanetType.HMC, PlanetType.ROCKY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_clypeus_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "lacrimam"     : (320.0, 130.0, 0.085, 0.015,  0.07,  0.031, [PlanetType.HMC, PlanetType.ICY, PlanetType.ROCKY]),
        "margaritus"   : (310.0, 120.0, 0.085, 0.015,  0.145, 0.105, [PlanetType.HMC, PlanetType.ICY]),
        "speculumi"    : (321.0, 131.0, 0.085, 0.015,  0.12,  0.085, [PlanetType.HMC, PlanetType.ROCKY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_concha_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "aureolas"      : (165.0, 20.0, 0.005, 0.007,  0.6,   0.6,  [PlanetType.HMC, PlanetType.ROCKY]),
        "biconcavis"    : (46.0,  7.0,  0.005, 0.005,  0.15,  0.13, [PlanetType.HMC, PlanetType.ROCKY]),
        "labiata"       : (175.0, 26.0, 0.007, 0.005,  0.15,  0.13, [PlanetType.ROCKY]),
        "renibus"       : (188.0, 20.0, 0.07,  0.02,   0.045, 0.02, [PlanetType.HMC, PlanetType.ROCKY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_crystal_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "shards"     : (102.0, 22.0, 0.004, 0.004,  0.1055, 0.0805, [PlanetType.HMC, PlanetType.ICY, PlanetType.ROCKY]),
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_electricae_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "pluma"     : (250.0, 45.0, 0.10,    0.10,    0.168,  0.142,  [PlanetType.ICY]),
        "radialem"  : (44.5,  15.5, 0.00549, 0.00451, 0.1495, 0.1005, [PlanetType.ICY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_fonticulua_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "campestris"    : (97.0,  47.0, 0.01549,  0.01451,  0.155,  0.105,  [PlanetType.ICY]),
        "digitos"       : (97.0,  8.0,  0.067,    0.028,    0.0365, 0.0085, [PlanetType.ICY]),
        "fluctus"       : (150.0, 5.0,  0.035,    0.015,    0.255,  0.015,  [PlanetType.ICY]),
        "lapida"        : (67.5,  12.5, 0.009495, 0.008505, 0.255,  0.025,  [PlanetType.ICY]),
        "segmentatus"   : (65.0,  5.0,  0.003,    0.001,    0.27,   0.01,   [PlanetType.ICY]),
        "upupam"        : (81.0,  11.0, 0.055,    0.035,    0.148,  0.128,  [PlanetType.ICY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

def score_frutexa_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "acus"       : (175.0, 15.0, 0.0255,  0.0245,  0.09,   0.05,   [PlanetType.HMC, PlanetType.ICY, PlanetType.ROCKY]),
        "collum"     : (135.0, 5.0,  0.00199, 0.00101, 0.255,  0.025,  [PlanetType.HMC, PlanetType.ICY, PlanetType.ROCKY]),
        "fera"       : (172.0, 18.0, 0.0485,  0.0465,  0.1275, 0.0925, [PlanetType.HMC, PlanetType.ICY, PlanetType.ROCKY]),
        "flabellum"  : (165.0, 15.0, 0.00274, 0.00176, 0.15,   0.05,   [PlanetType.HMC, PlanetType.ICY, PlanetType.ROCKY]),
        "flammasis"  : (166.5, 8.5,  0.00174, 0.00076, 0.16,   0.06,   [PlanetType.HMC, PlanetType.ICY, PlanetType.ROCKY]),
        "metallicum" : (170.0, 25.0, 0.00499, 0.00401, 0.205,  0.065,  [PlanetType.HMC, PlanetType.ICY]),
        "sponsae"    : (425.0, 25.0, 0.084,   0.014,   0.05,   0.005,  [PlanetType.HMC, PlanetType.ROCKY])
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)





def score_XXX_variant(species_name: str, mean_temp_k: float, pressure_atm: float, gravity: float, planet_type: PlanetType) -> float:
    # Exact Mode values from Canonn Research Group tables
    # Format: (Target_Temp_K, tolerance_temp Target_Pressure_atm, tolerance_pressure, Target_Gravity_g, tolerance_gravity)
    modes = {
        "XXX"     : (250.0, 45.0, 0.10, 0.10,  0.168, 0.142, [PlanetType.HMC, PlanetType.ICY, PlanetType.ROCKY]),
    }

    return score_variant(species_name, mean_temp_k, pressure_atm, gravity, planet_type, modes)

