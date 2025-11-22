import inspect
import json
import queue
import re
import threading
from typing import Dict

import EDXD.data_handler.helper.bio_helper as bio_helper
import EDXD.data_handler.helper.data_helper as dh
from EDXD.data_handler.helper.pausable_thread import PausableThread
from EDXD.data_handler.model import Model, Genus, CodexEntry, Ring
from EDXD.data_handler.planetary_surface_positioning_system import PSPSCoordinates
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
        self.last_event = None

    def _process_data(self):
        try:
            evt = json.loads(self.q.get())
        except Exception as e:
            log_context(level=logging.ERROR, frame=inspect.currentframe(), e=e)
            return

        self.process_event(evt=evt, update_gui=True)

    def process_event(self, evt, update_gui: bool, set_timestamp: bool = True):
        etype = evt.get("event")

        #113:   after app-start, load only current SYSTEM.json
        #       store last read journal line (timestamp) and process only newer lines
        if set_timestamp:
            current_evt_timestamp_str = evt.get("timestamp")
            last_processed_timestamp_str = dh.read_last_timestamp(JOURNAL_TIMESTAMP_FILE, current_evt_timestamp_str)

            last_processed_timestamp_date = dh.parse_utc_isoformat(last_processed_timestamp_str)
            current_evt_timestamp_date = dh.parse_utc_isoformat(current_evt_timestamp_str)

            if last_processed_timestamp_date > current_evt_timestamp_date or (
                    last_processed_timestamp_date == current_evt_timestamp_date and self.last_event == evt
            ):
                self.last_event = evt
                return

            if last_processed_timestamp_date < current_evt_timestamp_date:
                self.last_event = evt
                dh.update_last_timestamp(JOURNAL_TIMESTAMP_FILE, current_evt_timestamp_str)

        #141: don't load system data of FSDTarget, if targeted system has been visited before.
        #137: reset_system no longer uses <evt.get("Name")>, as this NEVER holds the systems name
        if etype != "FSDTarget":
            systemaddress = evt.get("SystemAddress")
            total_bodies = None
            if systemaddress is not None:
                self.m.total_bodies = None
                self.m.reset_system(evt.get("StarSystem") or self.m.system_name, systemaddress)

        else:
            systemaddress = self.m.system_addr
            total_bodies = self.m.total_bodies

        # ───── jump to a new system ───────────────────────────────
        #124: system/selection is no longer reset when entering super cruise
        #130: details of selected body reset on hyper space jump
        if etype == "StartJump" and evt.get("JumpType") == "Hyperspace":
            self.m.total_bodies = None
            self.m.target_body_id = None
            self.m.selected_body_id = None
            self.m.reset_system(system_name=evt.get("StarSystem"), address=systemaddress)
            body_id = "body_1"

        if evt.get("BodyCount") is not None:
            self.m.total_bodies = evt.get("BodyCount")
            total_bodies = self.m.total_bodies
            self.m.update_body_count(
                systemaddress=systemaddress,
                total_bodies=total_bodies
            )

        if etype == "FSSDiscoveryScan":
            if evt.get("Progress")*1 == 1:
                self.m.total_bodies = evt.get("Count")
                total_bodies = self.m.total_bodies

        if etype == "FSSAllBodiesFound":
            self.m.total_bodies = evt.get("Count")
            total_bodies = self.m.total_bodies
        # initialize all parameters for update_body
        body_id         = None
        body_name       = None
        body_type       = None
        radius          = None
        scoopable       = None
        distance        = None
        landable        = None
        biosignals      = None
        geosignals      = None
        mapped          = None
        geo_complete    = None
        geo_scanned     = None
        bio_complete    = None
        bio_scanned     = None

        materials       = {}

        bio_found:      Dict[str, Genus]        = {}
        geo_found:      Dict[str, CodexEntry]   = {}
        rings_found:    Dict[str, Ring]         = {}

        scandata = evt

        self.m.read_data_from_cache(systemaddress)
        bodyid_int = None
        if etype not in {"ScanBaryCentre", "Location", "StartJump", "SupercruiseExit"}:
            if "BodyID" in evt:
                bodyid_int = evt.get("BodyID")
            if bodyid_int is None and etype == "ScanOrganic" and "Body" in evt:
                bodyid_int = evt.get("Body")
            if bodyid_int is not None:
                body_id = bip + str(bodyid_int)
            if "BodyName" in evt:
                body_name = evt.get("BodyName")
            if body_name is None and etype == "FSDJump" and "Body" in evt:
                body_name = evt.get("Body")
            if body_name is None and body_id in self.m.bodies:
                body_name = self.m.bodies[body_id].body_name

        # initialise first_*
        # 0 - no data yet
        # 1 - some one else was first
        # 2 - I am first
        first_discovered = 0
        first_mapped = 0
        first_footfalled = 0

        if body_id in self.m.bodies:
            first_discovered = self.m.bodies[body_id].first_discovered or first_discovered
            first_mapped = self.m.bodies[body_id].first_mapped or first_mapped
            first_footfalled = self.m.bodies[body_id].first_footfalled or first_footfalled

        # FSS - body scan in system
        if etype == "Scan":
            # todo: process ring data properly
            if body_name.endswith("Ring"):
                pass # skip for now
            else:
                distance = evt.get("DistanceFromArrivalLS")
                landable = evt.get("Landable")
                body_type = evt.get("PlanetClass") or evt.get("StarType")
                radius = evt.get("Radius")
                if body_type is None and "Belt Cluster" in body_name:
                    body_type = "Belt Cluster"
                scoopable = body_type in ["K", "G", "B", "F", "O", "A", "M"]
                materials = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}

                # first analyse data during FSS
                if evt.get("ScanType") in {"AutoScan", "Detailed"}:
                    # are we first to discover?
                    if not evt.get("WasDiscovered"):
                        first_discovered = 2
                    else:
                        if first_discovered != 2:
                            first_discovered = 1

                    # Is that thing mapped?
                    if not evt.get("WasMapped"):
                        # It could be I've been there, but haven't sold the mapping data yet.
                        if first_mapped != 2:
                            first_mapped = 0
                    else:
                        if first_mapped != 2:
                            first_mapped = 1

                    # Has anyone set foot on that rock?
                    if not evt.get("WasFootfalled"):
                        # It could be I've been there, but haven't sold the mapping data yet.
                        if first_footfalled != 2:
                            first_footfalled = 0
                    else:
                        if first_footfalled != 2:
                            first_footfalled = 1

        if etype == "Disembark":
            if body_id:
                body_name = evt.get("Name")
            # Has anyone set foot on that rock?
            if not evt.get("WasFootfalled"):
                # It could be I've been there, but haven't sold the footfall data yet.
                if first_footfalled != 2:
                    first_footfalled = 2
            else:
                if first_footfalled != 2:
                    first_footfalled = 1

        if etype == "SAAScanComplete":
            # todo: process ring data properly
            if body_name.endswith("Ring"):
                pass  # skip for now
            else:
                mapped = True

                # Is that thing mapped?
                if not evt.get("WasMapped"):
                    # It could be I've been there, but haven't sold the mapping data yet. Or, I'm teh first to ever map that thing.
                    if first_mapped != 2:
                        first_mapped = 2
                else:
                    if first_mapped != 2:
                        first_mapped = 1

        # FSS - scanning of bodies
        if etype == "FSSBodySignals":
            # todo: process rings properly
            if body_name.endswith("Ring"):
                pass  # skip for now
            else:
                for signal in evt.get("Signals", []):
                    if signal.get("Type") == "$SAA_SignalType_Biological;":
                        biosignals = signal.get("Count")

                    if signal.get("Type") == "$SAA_SignalType_Geological;":
                        geosignals = signal.get("Count")

        # DSS - mapping of bodies
        if etype == "SAASignalsFound":
            # todo: process rings properly
            if body_name.endswith("Ring"):
                pass  # skip for now
            else:
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
            subcategory = evt.get("SubCategory")
            if subcategory == "$Codex_SubCategory_Geology_and_Anomalies;":
                if evt.get("NearestDestination") != "$Fixed_Event_Life_Cloud;":
                    geo_id = evt.get("Name")
                    geo_localised = evt.get("Name_Localised")
                    geo_is_new = evt.get("IsNewEntry") or evt.get("IsNewEntry") == "true"
                    geo_dict = self.m.bodies[body_id].geo_found if body_id in self.m.bodies else {}
                    geo_found = {k: CodexEntry(**v) if isinstance(v, dict) else v for k, v in geo_dict.items()}
                    geo_codex_dict = {}

                    geosignals_total = self.m.bodies[body_id].geosignals if body_id in self.m.bodies else 0
                    geo_scanned = self.m.bodies[body_id].geo_scanned if body_id in self.m.bodies else 0

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

                    if geo_found is not None:
                        geo_scanned = len(geo_found)

                    if geo_scanned == geosignals_total:
                        geo_complete = True

            if subcategory == "$Codex_SubCategory_Organic_Structures;":
                genus_id = evt.get("Name")
                # generalize genus ID
                genus_id = re.sub(r'_\d+_[^_]+(?=_Name;)', '_Genus', genus_id)
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
            genus_id = evt.get("Genus")
            species_id = evt.get("Species")
            # generalize genus ID
            genus_id = re.sub(r'_\d+_[^_]+(?=_Name;)', '_Genus', genus_id)
            genus_localised = evt.get("Genus_Localised")
            species_localised = evt.get("Species_Localised")
            variant_localised = evt.get("Variant_Localised")
            bio_dict = self.m.bodies[body_id].bio_found if body_id in self.m.bodies else {}
            bio_found = {k: Genus.from_dict(v) if isinstance(v, dict) else v for k, v in bio_dict.items()}
            bio_scanned = self.m.bodies[body_id].bio_scanned if body_id in self.m.bodies else 0
            biosignals_present = self.m.bodies[body_id].biosignals if body_id in self.m.bodies else 0

            genus_found_dict = {}
            if body_id in self.m.bodies and genus_id in self.m.bodies[body_id].bio_found:
                genus_found_dict = self.m.bodies[body_id].bio_found[genus_id]

            if scantype == "Analyse":
                genus_scanned = 3
            else:
                try:
                    genus_scanned = genus_found_dict.scanned_count or 0
                except AttributeError:
                    genus_scanned = 0

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
                bio_scanned += 1

            if biosignals_present > 0 and bio_scanned == biosignals_present:
                bio_complete = True

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

            #132: remove codex doublet
            if species_id is not None and species_id in bio_found:
                bio_found.pop(species_id)

            for bf, bfg in bio_found.items():
                #111: reset unfinished genus if scan hasn't been completed yet
                if bfg.genusid != genus_id:
                    if bfg.scanned_count < 3:
                        bio_found[bfg.genusid].scanned_count = 0
                        bio_found[bfg.genusid].pos_first = None
                        bio_found[bfg.genusid].pos_second = None


        # save/update data
        self.m.total_bodies = total_bodies or self.m.total_bodies
        # todo: process ring data properly
        # workaround for empty body type
        if body_type is None and body_id in self.m.bodies:
            body_type = self.m.bodies[body_id].body_type or "🚫 no data 🚫"
        if body_type is None:
            body_type = "🚫 no data 🚫"

        if body_id is not None and (body_name is None or not body_name.endswith("Ring")):
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
                radius=radius,
                mapped=mapped,
                geo_complete=geo_complete,
                geo_scanned=geo_scanned,
                bio_complete=bio_complete,
                bio_scanned=bio_scanned,
                first_discovered=first_discovered,
                first_mapped=first_mapped,
                first_footfalled=first_footfalled
            )

        # nothing to safe here, just update the target
        if etype == "Location":
            bodyid_int = evt.get("BodyID")
            body_id = bip + str(bodyid_int)
            self.m.target_body_id = body_id

        if update_gui and self.m.target_body_id :
            self.m.set_target(self.m.target_body_id )


