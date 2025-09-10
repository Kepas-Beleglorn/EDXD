import json, threading, queue, re
import inspect
import EDXD.data_handler.helper.bio_helper as bio_helper
import EDXD.data_handler.helper.data_helper as dh

from typing import Dict

from EDXD.data_handler.planetary_surface_positioning_system import PSPSCoordinates
from EDXD.data_handler.model import Model, Genus, CodexEntry, Ring
from EDXD.data_handler.helper.pausable_thread import PausableThread
from EDXD.globals import logging, BODY_ID_PREFIX, log_context, JOURNAL_TIMESTAMP_FILE

bip = BODY_ID_PREFIX

# ---------------------------------------------------------------------------
# controller thread – turns Journal lines into Model updates
# ---------------------------------------------------------------------------
class JournalController(PausableThread, threading.Thread):
    def __init__(self, q: "queue.Queue[str]", model: Model):
        super().__init__()
        self.q = q
        self.m = model

    def _process_data(self):
        try:
            evt = json.loads(self.q.get())
        except Exception as e:
            log_context(level=logging.ERROR, frame=inspect.currentframe(), e=e)
            return

        self.process_event(evt=evt, update_gui=True)

    def process_event(self, evt, update_gui: bool, set_timestamp: bool = True):
        etype = evt.get("event")
        total_bodies = None

        #113:   after app-start, load only current SYSTEM.json
        #       store last read journal line (timestamp) and process only newer lines
        if set_timestamp:
            current_timestamp_str = evt.get("timestamp")
            last_read_timestamp_str = dh.read_last_timestamp(JOURNAL_TIMESTAMP_FILE, current_timestamp_str)

            last_read_timestamp_date = dh.parse_utc_isoformat(last_read_timestamp_str)
            current_timestamp_date = dh.parse_utc_isoformat(current_timestamp_str)

            if last_read_timestamp_date >= current_timestamp_date:
                if evt.get("SystemAddress") is not None:
                    self.m.total_bodies = None
                    self.m.reset_system(evt.get("StarSystem"), evt.get("SystemAddress"))
                return

            if last_read_timestamp_date < current_timestamp_date:
                dh.update_last_timestamp(JOURNAL_TIMESTAMP_FILE, current_timestamp_str)

        # ───── jump to a new system ───────────────────────────────
        if etype != "FSDJump":
            self.m.just_jumped = False
        if etype == "FSDJump":
            self.m.just_jumped = True
            self.m.total_bodies = None
            self.m.target_body = None
            self.m.sel_target = None
            self.m.reset_system(evt.get("StarSystem"), evt.get("SystemAddress"))

        #elif etype in ("FSSDiscoveryScan", "FSSAllBodiesFound"):
        if evt.get("BodyCount") is not None:
            self.m.total_bodies = evt.get("BodyCount")
            total_bodies = self.m.total_bodies

        if evt.get("FSSAllBodiesFound") is not None:
            self.m.total_bodies = evt.get("Count")
            total_bodies = self.m.total_bodies
        # initialize all parameters for update_body
        systemaddress   = evt.get("SystemAddress")
        body_id         = None
        body_name       = None
        body_type       = None
        radius          = None
        scoopable       = None
        distance        = None
        landable        = None
        biosignals      = None
        geosignals      = None
        materials       = {}
        scandata        = evt

        bio_found:      Dict[str, Genus]        = {}
        geo_found:      Dict[str, CodexEntry]   = {}
        rings_found:    Dict[str, Ring]         = {}

        self.m.read_data_from_cache(systemaddress)

        # FSS - body scan in system
        if etype == "Scan":
            if self.m.system_name is None:  # first scan in a fresh session
                self.m.reset_system(evt.get("StarSystem"), evt.get("SystemAddress"))
            body_name = evt.get("BodyName")
            # todo: process ring data properly
            if body_name.endswith("Ring"):
                pass # skip for now
            else:
                distance = evt.get("DistanceFromArrivalLS")
                bodyid_int = evt.get("BodyID")
                landable = evt.get("Landable")
                body_id = bip + str(bodyid_int)
                body_type = evt.get("PlanetClass") or evt.get("StarType")
                radius = evt.get("Radius")
                if body_type is None and "Belt Cluster" in body_name:
                    body_type = "Belt Cluster"
                scoopable = body_type in ["K", "G", "B", "F", "O", "A", "M"]
                materials = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}

        # FSS - scanning of bodies
        if etype == "FSSBodySignals":
            body_name = evt.get("BodyName")
            # todo: process rings properly
            if body_name.endswith("Ring"):
                pass  # skip for now
            else:
                bodyid_int = evt.get("BodyID")
                body_id = bip + str(bodyid_int)
                for signal in evt.get("Signals", []):
                    if signal.get("Type") == "$SAA_SignalType_Biological;":
                        biosignals = signal.get("Count")

                    if signal.get("Type") == "$SAA_SignalType_Geological;":
                        geosignals = signal.get("Count")

        # DSS - mapping of bodies
        if etype == "SAASignalsFound":
            body_name = evt.get("BodyName")
            # todo: process rings properly
            if body_name.endswith("Ring"):
                pass  # skip for now
            else:
                bodyid_int = evt.get("BodyID")
                body_id = bip + str(bodyid_int)
                for signal in evt.get("Signals", []):
                    if signal.get("Type") == "$SAA_SignalType_Biological;":
                        biosignals = signal.get("Count")
                        bio_dict = self.m.bodies[body_id].bio_found if body_id in self.m.bodies else {}
                        bio_found = {k: Genus(**v) if isinstance(v, dict) else v for k, v in bio_dict.items()}

                        for genus in evt.get("Genuses", []):
                            genus_id = genus.get("Genus")
                            genus_localised = genus.get("Genus_Localised")
                            genus_found_dict = {}
                            if body_id in self.m.bodies and genus_id in self.m.bodies[body_id].bio_found:
                                genus_found_dict = self.m.bodies[body_id].bio_found[genus_id]

                            if genus_found_dict == {}:
                                genus_found = Genus(genusid=genus_id, localised=genus_localised, scanned_count=0)
                            else:
                                genus_found = Genus(
                                    genusid=genus_found_dict.genusid,
                                    localised=genus_found_dict.localised or genus_found_dict.localised,
                                    variant_localised=genus_found_dict.variant_localised,
                                    species_localised=genus_found_dict.species_localised,
                                    min_distance=genus_found_dict.min_distance or bio_helper.bioGetRange(genus_id),
                                    scanned_count=genus_found_dict.scanned_count or 0
                                )

                            bio_found[genus_id] = genus_found

                    if signal.get("Type") == "$SAA_SignalType_Geological;":
                        geosignals = signal.get("Count")

        # ── SRV geology scan (CodexEntry, but not if IsNewDiscovery=falsgenuse) ───
        if etype == "CodexEntry":  # and evt.get("Category") == "$Codex_Category_Geology;":
            bodyid_int = evt.get("BodyID")
            body_id = bip + str(bodyid_int)
            subcategory = evt.get("SubCategory")
            if subcategory == "$Codex_SubCategory_Geology_and_Anomalies;":
                if evt.get("NearestDestination") != "$Fixed_Event_Life_Cloud;":
                    geo_id = evt.get("Name")
                    geo_localised = evt.get("Name_Localised")
                    geo_is_new = evt.get("IsNewEntry") or evt.get("IsNewEntry") == "true"
                    geo_dict = self.m.bodies[body_id].geo_found if body_id in self.m.bodies else {}
                    geo_found = {k: CodexEntry(**v) if isinstance(v, dict) else v for k, v in geo_dict.items()}
                    geo_codex_dict = {}
                    if body_id in self.m.bodies and geo_id in self.m.bodies[body_id].geo_found:
                        geo_codex_dict = self.m.bodies[body_id].geo_found[geo_id]

                    if geo_codex_dict == {}:
                        geo_codex_found = CodexEntry(codexid=geo_id, localised=geo_localised, is_new=geo_is_new, body_id=body_id)
                    else:
                        if isinstance(geo_codex_dict, CodexEntry):
                            geo_codex_found = geo_codex_dict
                            geo_codex_found.is_new = geo_is_new or geo_codex_found.is_new
                        else:
                            geo_codex_found = CodexEntry(
                                codexid = geo_codex_dict.get("codexid"),
                                localised = geo_codex_dict.get("localised"),
                                is_new = geo_codex_dict.get("is_new"),
                                body_id=body_id
                            )
                    geo_found[geo_id] = geo_codex_found

            if subcategory == "$Codex_SubCategory_Organic_Structures;":
                body_int = evt.get("BodyID")
                body_id = bip + str(body_int)
                genus_id = evt.get("Name")
                # generalize genus ID
                genus_id = re.sub(r'_\d+_[A-Za-z](?=_Name;)', '_Genus', genus_id)
                genus_localised = evt.get("Genus_Localised")
                variant_localised = evt.get("Name_Localised")
                bio_dict = self.m.bodies[body_id].bio_found if body_id in self.m.bodies else {}
                bio_found = {k: Genus(**v) if isinstance(v, dict) else v for k, v in bio_dict.items()}

                genus_found_dict = {}
                if body_id in self.m.bodies and genus_id in self.m.bodies[body_id].bio_found:
                    genus_found_dict = self.m.bodies[body_id].bio_found[genus_id]

                if genus_found_dict == {}:
                    genus_found = Genus(genusid=genus_id, localised=genus_localised, variant_localised=variant_localised, scanned_count=0)
                else:
                    genus_found = Genus(
                        genusid=genus_found_dict.genusid,
                        localised=genus_found_dict.localised or genus_found_dict.localised,
                        species_localised=genus_found_dict.species_localised,
                        variant_localised=genus_found_dict.variant_localised or variant_localised,
                        min_distance=genus_found_dict.min_distance or bio_helper.bioGetRange(genus_id),
                        scanned_count=genus_found_dict.scanned_count
                    )

                bio_found[genus_id] = genus_found

        if etype == "ScanOrganic":
            scantype = evt.get("ScanType")
            body_int = evt.get("Body")
            body_id = bip + str(body_int)
            genus_id = evt.get("Genus")
            # generalize genus ID
            genus_id = re.sub(r'_\d+_[A-Za-z](?=_Name;)', '_Genus', genus_id)
            genus_localised = evt.get("Genus_Localised")
            species_localised = evt.get("Species_Localised")
            variant_localised = evt.get("Variant_Localised")
            bio_dict = self.m.bodies[body_id].bio_found if body_id in self.m.bodies else {}
            def genus_from_dict(data):
                # Replace these field names with your actual property names
                if "pos_first" in data and isinstance(data["pos_first"], dict):
                    data["pos_first"] = PSPSCoordinates.from_dict(data["pos_first"])
                if "pos_second" in data and isinstance(data["pos_second"], dict):
                    data["pos_second"] = PSPSCoordinates.from_dict(data["pos_second"])
                return Genus(**data)
            bio_found = {k: Genus(**v) if isinstance(v, dict) else v for k, v in bio_dict.items()}

            genus_found_dict = {}
            if body_id in self.m.bodies and genus_id in self.m.bodies[body_id].bio_found:
                genus_found_dict = self.m.bodies[body_id].bio_found[genus_id]

            if  scantype == "Analyze":
                genus_scanned = 3
            else:
                genus_scanned = genus_found_dict.scanned_count or 0

            pos_first = None
            pos_second = None

            # read coordinates before scan count incrementation
            if genus_scanned == 0:
                pos_first = self.m.current_position

            if genus_scanned == 1 and genus_found_dict.pos_first is not None:
                pos_first = PSPSCoordinates.from_dict(genus_found_dict.pos_first)
                pos_second = self.m.current_position

            if genus_scanned == 3:
                pos_first = None
                pos_second = None

            if genus_found_dict == {}:
                genus_found = Genus(genusid=genus_id, localised=genus_localised, species_localised=species_localised, variant_localised=variant_localised, scanned_count=genus_scanned, min_distance=bio_helper.bioGetRange(genus_id), pos_first=pos_first, pos_second=pos_second)
            else:
                if genus_found_dict.scanned_count == 3:
                    genus_scanned = genus_found_dict.scanned_count
                else:
                    genus_scanned = genus_found_dict.scanned_count + 1

                genus_found = Genus(
                    genusid=genus_found_dict.genusid,
                    localised=genus_found_dict.localised or genus_localised,
                    species_localised=genus_found_dict.species_localised or species_localised,
                    variant_localised=genus_found_dict.variant_localised or variant_localised,
                    min_distance=genus_found_dict.min_distance or bio_helper.bioGetRange(genus_id),
                    scanned_count=genus_scanned,
                    pos_first=pos_first,
                    pos_second=pos_second
                )

            bio_found[genus_id] = genus_found

        # save/update data
        self.m.total_bodies = total_bodies or self.m.total_bodies
        if body_id is not None:
            self.m.update_body(
                systemaddress=systemaddress,
                body_id=body_id,
                body_name=body_name,
                body_type=body_type,
                scoopable=scoopable,
                distance=distance,
                landable=landable,
                biosignals=biosignals,
                geosignals=geosignals,
                materials=materials,
                scandata=scandata,
                bio_found=bio_found,
                geo_found=geo_found,
                # todo: implement rings
                rings=rings_found,
                total_bodies=total_bodies,
                radius=radius
            )

        # nothing to safe here, just update the target
        if etype == "Location":
            bodyid_int = evt.get("BodyID")
            body_id = bip + str(bodyid_int)
            self.m.target_body_id = body_id

        if update_gui and self.m.target_body_id :
            self.m.set_target(self.m.target_body_id )


