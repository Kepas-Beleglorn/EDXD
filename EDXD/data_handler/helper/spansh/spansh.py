from time import sleep
from datetime import datetime, timezone
from typing import List, Dict, Any
import json

import requests
from pathlib import Path

from EDXD.data_handler.helper.data_helper import time_delta

from EDXD.data_handler.helper.spansh import spansh2edjournal
from EDXD.data_handler.helper.dotted_dictionary import create_dot_dict_from_string
from EDXD.data_handler.model import Model, Atmosphere, Ring
import EDXD.data_handler.helper.data_helper as dh
from EDXD.globals import BODY_NO_DATA, SLEF_PATH
from EDXD.data_handler.helper.spansh.ship_modules import ShipFSDModules

SPANSH_BASE_URL:str = "https://spansh.co.uk/"
SPANSH_GET_DUMP: str = SPANSH_BASE_URL + "api/dump/"
SPANSH_PLOTTED_ROUTE: str = SPANSH_BASE_URL + "api/results/"

SPANSH_ROAD_TO_RICHES_API: str = SPANSH_BASE_URL + "api/riches/route"
#SPANSH_ROAD_TO_RICHES_REF: str = SPANSH_BASE_URL + "riches"

SPANSH_GALAXY_PLOTTER_API: str = SPANSH_BASE_URL + "api/generic/route"
#SPANSH_GALAXY_PLOTTER_REF: str = SPANSH_BASE_URL + "exact-plotter"

SPANSH_NEUTRON_ROUTER_API: str = SPANSH_BASE_URL + "api/route"
#SPANSH_NEUTRON_ROUTER_REF: str = SPANSH_BASE_URL + "plotter"

SPANSH_EXO_MASTERY_API: str = SPANSH_BASE_URL + "api/exobiology/route"

FSD_INJECTION_MULTIPLIER: int = 2

# current version
try:
    from EDXD._version import VERSION as __version__
except Exception:
    __version__ = "0.0.0.0"

class SpanshHelper:
    def __init__(self):
        self.system_data: DotDict  | None = None
        self.url = None

    def get_system_data(self, system_id: int):
        # Check if we need to fetch new data
        if self.system_data is None or (hasattr(self.system_data, "id64") and int(self.system_data.id64) != system_id):
            # 1. Make the request
            self.url = SPANSH_GET_DUMP + str(system_id)
            response = requests.get(self.url)
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
        bodies: DotDict = self.system_data.bodies
        for body in bodies:
            try:
                if body is not None and (body.name is None or not body.name.endswith("Ring")) and body.type != "Barycentre":
                    body_id = "body_" + str(body.bodyId)
                    fetched_body_ids.append(body_id)
                    if body_id in system_model.bodies.keys():
                        if (system_model.bodies[body_id].body_name is not None and system_model.bodies[body_id].body_name != BODY_NO_DATA and
                                system_model.bodies[body_id].body_type is not None and system_model.bodies[body_id].body_type != BODY_NO_DATA):
                            continue

                    landable = False
                    if hasattr(body, "isLandable"):
                        landable = body.isLandable

                    g_force     : float = 0
                    earth_mass  : float = 0
                    stellar_mass: float = 0
                    radius      : float = 0

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

                    rings_found:    Dict[str, Ring]         = {}
                    if hasattr(body, "rings"):
                        for spansh_ring in body.rings:
                            ring_name = spansh_ring.name
                            ring_class = spansh2edjournal.get_journal_ring_class(spansh_ring.type)
                            ring = Ring(body_id=ring_name, body_name=ring_name, ring_class=ring_class, signals={})
                            rings_found[ring_name] = ring

                    geo_signal_count = None
                    if hasattr(body, "signals"):
                        if hasattr(body.signals, "signals"):
                            if hasattr(body.signals.signals, "$SAA_SignalType_Geological;"):
                                geo_signal_count = int(body.signals.signals["$SAA_SignalType_Geological;"])

                    bio_signal_count = None
                    if hasattr(body, "signals"):
                        if hasattr(body.signals, "signals"):
                            if hasattr(body.signals.signals, "$SAA_SignalType_Biological;"):
                                bio_signal_count = int(body.signals.signals["$SAA_SignalType_Biological;"])

                    scandata = {}
                    scandata["event"] = "Scan"
                    scandata["ScanType"] = "Detailed"
                    if body.type == "Star":
                        scandata["StarType"] = body_type
                    if body.type == "Planet":
                        scandata["PlanetClass"] = body_type
                        scandata["TerraformState"] = body.terraformingState
                    if hasattr(body, "earthMasses"):
                        scandata["MassEM"] = body.earthMasses

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
                        biosignals=bio_signal_count,
                        geosignals=geo_signal_count,
                        materials=materials,
                        scandata=scandata,
                        bio_found=None,
                        geo_found=None,
                        has_rings=hasattr(body, "rings"),
                        rings=rings_found,
                        total_bodies=body_count,
                        radius=radius,
                        mapped=None,
                        geo_complete=None,
                        geo_scanned=None,
                        bio_complete=None,
                        bio_scanned=None,
                        first_discovered=1,
                        first_mapped=0,
                        first_footfalled=0,
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
                print(f"WARNING (update_system_data; after 'system_model.update_body'): [{systemaddress}] {self.system_data.name} - Body: {body.bodyId} | {body.name} | {body.type} - {e}\nGET: {self.url}\nplease consider using EDMC to help keeping spansh, EDSM and other databases up to date.\nsystem@spansh: https://spansh.co.uk/system/{systemaddress}#system-main")

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

    @staticmethod
    def extract_loadout_to_slef(journal_event: dict[str, Any]) -> None:
        """
        Extracts a 'Loadout' event from an Elite Dangerous journal and converts it to SLEF format.

        Args:
            journal_event: The parsed JSON dictionary of the 'Loadout' event.
            output_path: The file path where the resulting SLEF JSON will be saved.
        """
        slef_structure = {
            "header": {
                "appName": "EDXD",
                "appVersion": __version__
            },
            "data": journal_event
        }

        with open(SLEF_PATH, "w", encoding="utf-8") as f:
            json.dump([slef_structure], f, indent=4)


class SpanshRoutePlotter:
    def __init__(self):
        self.route_planners = [
            ("Galaxy Plotter", "exact-plotter"),
            ("Road to Riches", "riches"),
            ("Neutron Plotter", "plotter")
        ]
        self.sm: ShipFSDModules = ShipFSDModules()

    @staticmethod
    def get_route(job_id: str) -> DotDict | None:
        plotted_route: DotDict | None = None
        return plotted_route

    def galaxy_plotter(self,
                       ship_loadout: DotDict,
                       source_system_name: str,
                       destination_system_name: str,
                       cargo: int,
                       reserve_fuel: int = 0,
                       already_supercharged: bool = False,
                       use_supercharge: bool = True,
                       fsd_inject_always: bool = False,
                       fsd_inject_when_required: bool = False,
                       exclude_secondary: bool = False,
                       refuel_every_scoopable: bool = False,
                       algorithm: str =  "optimistic"
                       ) -> str | None:
        spansh_job_id = None

        path = Path(SLEF_PATH)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {SLEF_PATH}")

        with open(path, 'r', encoding='utf-8') as f:
            ship_loadout_json = json.load(f)

        url = SPANSH_GALAXY_PLOTTER_API
        payload = {
            "source": source_system_name,
            "destination": destination_system_name,
            "is_supercharged": 1 if already_supercharged else 0,
            "use_supercharge": 1 if use_supercharge else 0,
            "use_injections": 1 if fsd_inject_always else 0,
            "use_injections_when_required": 1 if fsd_inject_when_required else 0,
            "exclude_secondary": 1 if exclude_secondary else 0,
            "refuel_every_scoopable": 1 if refuel_every_scoopable else 0,
            "fuel_power": self.sm.get_fuel_power(ship_loadout),
            "fuel_multiplier": self.sm.get_fuel_multiplier(ship_loadout),
            "optimal_mass": self.sm.get_optimal_mass(ship_loadout),
            "base_mass": ship_loadout.data.UnladenMass,
            "tank_size": ship_loadout.data.FuelCapacity.Main,
            "internal_tank_size": ship_loadout.data.FuelCapacity.Reserve,
            "reserve_size": reserve_fuel,
            "max_fuel_per_jump": self.sm.get_max_fuel_per_jump(ship_loadout),
            "range_boost": self.sm.get_jump_boost(ship_loadout),
            "max_time": 120,
            "cargo": cargo,
            "algorithm": algorithm,
            "supercharge_multiplier": self.sm.get_super_charge_multiplier(ship_loadout),
            "injection_multiplier": FSD_INJECTION_MULTIPLIER,
            # REPLACE THE STRING BELOW WITH YOUR ACTUAL MASSIVE URL-ENCODED SHIP_BUILD STRING
            # Or, if you have the Python dict/object from your SLEF function, use: json.dumps(slef_object)
            "ship_build": ship_loadout_json
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "EDXD (Python)",
            "X-Requested-With": "XMLHttpRequest"
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code < 200 or response.status_code >= 300:
            # Read the body for the error message
            error_body = response.text
            print(f"ERROR: Spansh API returned status {response.status_code}: {error_body}")
            return spansh_job_id

        response_dict: DotDict = create_dot_dict_from_string(response.text)
        spansh_job_id = response_dict.job
        return spansh_job_id

    @staticmethod
    def get_itinerary(job_id: str | None) -> DotDict | None:
        spansh_itinerary: DotDict | None = None

        url = SPANSH_PLOTTED_ROUTE

        while True:
            response = requests.request("GET", url + str(job_id))
            response_dict: DotDict = create_dot_dict_from_string(response.text)
            iso_date =datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            if response.status_code < 200 or response.status_code >= 300:
                error_body = response.text
                print(f"ERROR: Spansh API returned status {response.status_code}: {error_body}")
                break

            if response_dict.state == "completed" and response_dict.status == "ok":
                spansh_itinerary = DotDict(response_dict.result)
                break

            print(f"Job ID: {job_id} - state: {response_dict.state} - status: {response_dict.status} - created at: {response_dict.created_at} - current time: {iso_date} - duration: {time_delta(response_dict.created_at, iso_date)}")
            sleep(1)

        print(f"Job ID: {job_id} - state: {response_dict.state} - status: {response_dict.status} - created at: {response_dict.created_at} - updated at: {response_dict.updated_at} - duration: {time_delta(response_dict.created_at, response_dict.updated_at)}")
        return spansh_itinerary

########################################################################################################################################################################################################
#======================================================================================================================================================================================================#
########################################################################################################################################################################################################
from EDXD.data_handler.helper.dotted_dictionary import DotDict, load_json_as_dotdict
spansh = SpanshRoutePlotter()
ship_loadout = load_json_as_dotdict(SLEF_PATH)

algos = ("optimistic", "fuel", "fuel_jumps", "guided", "pessimistic")

try:
    for algo in algos:
        job_id: str | None= spansh.galaxy_plotter(ship_loadout, source_system_name="Sol", destination_system_name="Colonia", cargo=1, algorithm=algo)
        print(f"{algo}: {job_id}")
        itinerary: DotDict | None = spansh.get_itinerary(job_id)
        print(f"{algo} - jumps:  {len(itinerary.jumps) - 1}")
except Exception as e:
    print(e)