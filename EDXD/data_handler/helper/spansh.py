import json
from typing import List, Dict

import requests

from EDXD.data_handler.helper.json_helper import DotDict
from EDXD.data_handler.model import Model, Atmosphere
import EDXD.data_handler.helper.data_helper as dh
from EDXD.globals import BODY_NO_DATA

SPANSH_GET_DUMP: str = "https://spansh.co.uk/api/dump/"

class SpanshHelper:
    def __init__(self):
        self.system_data: DotDict = None

    def get_system_data(self, system_id: int):
        # Check if we need to fetch new data
        if self.system_data is None or (hasattr(self.system_data, "id64") and int(self.system_data.id64) != system_id):
            # 1. Make the request
            url = SPANSH_GET_DUMP + str(system_id)
            response = requests.get(url)
            response.raise_for_status()  # Raise error if request failed

            # 2. Parse JSON into a standard Python dict
            data_dict = response.json()

            # 3. Convert the ENTIRE nested structure to DotDict
            self.system_data = DotDict(data_dict.get("system"))

    def get_parent_star_ids(self, current_body: DotDict) -> List[Dict[str, int]]:
        parent_stars: List[Dict[str, int]] = current_body.parents

        try:
            # does the planet already have Stars listed as parents?
            for body_parent in parent_stars:
                if list(body_parent.keys())[0] == "Star":
                    return parent_stars
        except  Exception as e:
            print(f"ERROR: get_parent_star_ids[1] {current_body.bodyId}/{current_body.name}/{current_body.type}/{current_body.parents}: {e}")

        try:
            for body_parent in parent_stars:
                if list(body_parent.keys())[0] == "Planet":
                    parent_id = list(body_parent.values())[0]
                    for body in self.system_data.bodies:
                        if body.bodyId == parent_id:
                            parent_results = self.get_parent_star_ids(body)
                            for item in parent_results:
                                parent_stars.append(item)
        except  Exception as e:
            print(f"ERROR: get_parent_star_ids[2] {current_body.bodyId}/{current_body.name}/{current_body.type}/{current_body.parents}: {e}")

        try:
            for body_parent in parent_stars:
                if list(body_parent.keys())[0] == "Null":
                    parent_id = list(body_parent.values())[0]
                    for body in self.system_data.bodies:
                        if body.type == "Star":
                            for star_parent in body.parents:
                                if list(star_parent.keys())[0] == "Null" and list(star_parent.values())[0] == parent_id:
                                    parent_stars.append({str("Star"): int(body.bodyId)})
        except  Exception as e:
            print(f"ERROR: get_parent_star_ids[3] {current_body.bodyId}/{current_body.name}/{current_body.type}/{current_body.parents}: {e}")

        return parent_stars

    def update_system_data(self, system_model: Model):
        systemaddress: int = self.system_data.id64
        system_model.reset_system(self.system_data.name, systemaddress)
        body_count = 0
        if hasattr(self.system_data, "bodyCount"):
            body_count = self.system_data.bodyCount
        else:
            for item in  self.system_data.bodies:
                if item.type and item.type in {"Star", "Planet"}:
                    body_count += 1
        system_model.update_body_count(
            systemaddress=systemaddress,
            total_bodies=body_count
        )
        fetched_body_ids: List[str] = []
        print(f"DEBUG: update_system_data[{systemaddress}] {self.system_data.name}")
        bodies: DotDict = self.system_data.bodies
        for body in bodies:
            try:
                if body is not None and (body.name is None or not body.name.endswith("Ring")) and body.type != "Barycentre":
                    body_id = "body_" + str(body.bodyId)
                    fetched_body_ids.append(body_id)
                    if body_id in  system_model.bodies.keys():
                        if (system_model.bodies[body_id].body_name is not None and system_model.bodies[body_id].body_name != BODY_NO_DATA and
                                system_model.bodies[body_id].body_type is not None and system_model.bodies[body_id].body_type != BODY_NO_DATA):
                            continue

                    landable = False
                    if hasattr(body, "isLandable"):
                        landable = body.isLandable

                    g_force     : float = None
                    earth_mass  : float = None
                    stellar_mass: float = None
                    radius      : float = None

                    if body.type == "Star":
                        stellar_mass = body.solarMasses
                        if stellar_mass:
                            stellar_mass = float(stellar_mass)
                        radius = body.solarRadius
                        g_force = dh.get_gravity_from_mass_and_radius(solar_masses=stellar_mass, earth_masses=earth_mass, radius=float(radius))
                    if body.type == "Planet":
                        radius = body.radius
                        g_force = body.gravity
                    if radius is not None:
                        radius = float(radius)

                    pressure = None
                    if hasattr(body, "surfacePressure"):
                        pressure = dh.pressure_as_pascals_from_atm(body.surfacePressure)

                    materials = {}
                    if hasattr(body, "materials"):
                        materials = {k.lower(): v for k, v in body.materials.items()}

                    atmosphere = None
                    atmos_type  = None
                    atmos_type_raw  = None
                    if hasattr(body, "atmosphereComposition") and hasattr(body, "atmosphereType"):
                        atmos_composition = body.atmosphereComposition
                        if body.atmosphereType is not None:
                            atmos_type = body.atmosphereType.replace(" ", "")
                            atmos_type_raw = body.atmosphereType.lower() + " atmosphere"
                        atmosphere = Atmosphere(type=atmos_type, composition=atmos_composition, raw=atmos_type_raw)

                    luminosity = None
                    raw_luminosity = None
                    if hasattr(body, "luminosity"):
                        raw_luminosity = body.luminosity
                        luminosity = dh.get_clean_luminosity(raw_luminosity)

                    parents = None
                    if hasattr(body, "parents"):
                        parents = self.get_parent_star_ids(body)
                        parents = dh.unique_dict_list(parents)

                    volcanism = None
                    if hasattr(body, "volcanismType"):
                        volcanism = body.volcanismType.lower()

                    present_life = ""
                    if hasattr(body, "subType") and " with " in body.subType:
                        present_life = body.subType.split(" with ")[1]

                    if body.type == "Star":
                        if body.spectralClass:
                            body_type = "".join(char for char in body.spectralClass if char.isalpha())
                        else:
                            if "(" in body.subType:
                                body_type = body.subType.split("(")[1].split(")")[0]
                            else:
                                if body.subType ==  "Neutron Star":
                                    body_type = "N"
                                else:
                                    body_type = body.subType
                                    print(f"body.subType used as body type: [{body_type}]")
                            print(f"update_system_data[{systemaddress}] {self.system_data.name}: {body.name}[{body_id}] TYPE - [{body.subType}] -> [{body_type}]")
                    else:
                        body_type = body.subType

                    part = 0
                    for body_type_part in body_type.split(" "):
                        if part == 0:
                            body_type = body_type_part
                        elif body_type_part in {"I", "II", "III", "IV", "V", "VI", "VII", "VIII"}:
                            body_type += " " + body_type_part
                        else:
                            body_type += " " + body_type_part.lower()

                        part += 1

                    parent_distance = 0
                    if hasattr(body, "semiMajorAxis"):
                        parent_distance = body.semiMajorAxis

                    # ToDo: #255 - forge ring data
                    rings = {}
                    if hasattr(body, "rings"):
                        pass

                    #ToDo: #260: get present geo signals (count only)
                    geo_signal_count = None

                    #ToDo: #261: get present bio signals (count only)
                    bio_signal_count = None

                    #ToDo: 254 - forge scandata for body appraisal
                    scandata = None

                    system_model.update_body(
                        systemaddress=systemaddress,
                        body_id=body_id,
                        body_name=body.name,
                        body_type=body_type,
                        is_star=body.type == "Star",
                        scoopable=body.type == "Star" and body.subType[0] in ["K", "G", "B", "F", "O", "A", "M"],
                        distance=body.distanceToArrival,
                        landable=landable,
                        g_force=g_force,
                        biosignals=body.get("$SAA_SignalType_Biological;"),
                        geosignals=body.get("$SAA_SignalType_Geological;"),
                        materials=materials,
                        scandata=scandata,
                        bio_found=bio_signal_count,
                        geo_found=geo_signal_count,
                        has_rings=hasattr(body, "rings"),
                        rings=rings,
                        total_bodies=body_count,
                        radius=radius,
                        mapped=None,
                        geo_complete=None,
                        geo_scanned=None,
                        bio_complete=None,
                        bio_scanned=None,
                        first_discovered=None,
                        first_mapped=None,
                        first_footfalled=None,
                        atmosphere=atmosphere,
                        mean_temp=body.surfaceTemperature,
                        luminosity=luminosity,
                        raw_luminosity=raw_luminosity,
                        volcanism=volcanism,
                        present_life=present_life,
                        parents=parents,
                        parent_distance=parent_distance,
                        pressure=pressure
                    )
            except Exception as e:
                print(f"ERROR: [{systemaddress}] {self.system_data.name} - {body.type} - {e}")

        pop_items: List[str] = []
        for body in system_model.bodies:
            if body not in fetched_body_ids:
                pop_items.append(body)

        for poppy in pop_items:
            system_model.bodies.pop(poppy)

        system_model.update_body_count(
            systemaddress=systemaddress,
            total_bodies=body_count
        )
