import json
from calendar import error
from typing import List

import requests

from EDXD.data_handler.helper.json_helper import DotDict
from EDXD.data_handler.model import Model
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


    def update_system_data(self, system_model: Model):
        systemaddress: int = self.system_data.id64
        system_model.reset_system(self.system_data.name, systemaddress)
        system_model.update_body_count(
            systemaddress=systemaddress,
            total_bodies=self.system_data.bodyCount
        )
        fetched_body_ids: List[str] = []
        print(f"update_system_data[{systemaddress}] {self.system_data.name}")
        bodies: DotDict = self.system_data.bodies
        for body in bodies:
            try:
                if body is not None and (body.name is None or not body.name.endswith("Ring")) and body.type != "Barycentre":
                    body_id = "body_" + str(body.bodyId)

                    fetched_body_ids.append(body_id)
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

                    rings = {}
                    if hasattr(body, "rings"):
                        #ToDo: #255 - forge ring data
                        pass

                    atmosphere = {}
                    if hasattr(body, "atmosphereType"):
                        #ToDo: #256 - forge atmosphere data
                        pass

                    luminosity = None
                    raw_luminosity = None
                    if hasattr(body, "luminosity"):
                        raw_luminosity = body.luminosity
                        luminosity = dh.get_clean_luminosity(raw_luminosity)

                    parents = None
                    if hasattr(body, "parents"):
                        #ToDo: #257 - forge parent data
                        pass

                    volcanism = None
                    if hasattr(body, "volcanismType"):
                        volcanism = body.volcanismType.lower()

                    present_life = ""
                    if hasattr(body, "subType") and " with " in body.subType:
                        present_life = body.subType.split(" with ")[1]

                    #ToDo: 254 - forge scandata for body appraisal
                    scandata = None


                    if body.type == "Star":
                        if body.spectralClass:
                            body_type = "".join(char for char in body.spectralClass if char.isalpha())
                        else:
                            body_type = body.subType.split("(")[1].split(")")[0]
                            print(f"update_system_data[{systemaddress}] {self.system_data.name}: {body.name}[{body_id}] TYPE - [{body.subType}] -> [{body_type}]")
                    else:
                        body_type = body.subType

                    parent_distance = 0
                    if hasattr(body, "semiMajorAxis"):
                        parent_distance = body.semiMajorAxis

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
                        bio_found=None,
                        geo_found=None,
                        has_rings=hasattr(body, "rings"),
                        rings=rings,
                        total_bodies=self.system_data.bodyCount,
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
            total_bodies=self.system_data.bodyCount
        )
