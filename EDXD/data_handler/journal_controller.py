import json, threading, queue

from EDXD.data_handler.model import Model, Genus, CodexEntry
from EDXD.data_handler.helper.pausable_thread import PausableThread
import inspect
from EDXD.globals import logging, BODY_ID_PREFIX, log_context
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

    def process_event(self, evt, update_gui: bool):
        etype = evt.get("event")
        total_bodies = None
        bodyid_int = None

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

        # initialize all parameters fomr update_body
        systemaddress   = evt.get("SystemAddress")
        body_id         = None
        body_name       = None
        body_type       = None
        scoopable       = None
        distance        = None
        landable        = None
        biosignals      = None
        geosignals      = None
        materials       = {}
        scandata        = evt
        bio_found       = {}
        geo_found       = {}
        rings           = {}

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
                if body_type is None and "Belt Cluster" in body_name:
                    body_type = "Belt Cluster"
                scoopable = body_type in ["K", "G", "B", "F", "O", "A", "M"]
                materials = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}

        # DSS - mapping of bodies and rings
        if etype in ("FSSBodySignals", "SAASignalsFound"):
            body_name = evt.get("BodyName")
            # todo: process rings properly
            if body_name.endswith("Ring"):
                pass  # skip for now
            else:
                bodyid_int = evt.get("BodyID")
                body_id = bip + str(bodyid_int)
                for signal in evt.get("Signals", []):
                    biosignals = 0
                    geosignals = 0
                    bio_found = None
                    geo_found = None

                    if signal.get("Type") == "$SAA_SignalType_Biological;":
                        biosignals = signal.get("Count")
                        bio_found = self.m.bodies[body_id].bio_found if body_id in self.m.bodies else None
                        for genus in evt.get("Genuses", []):
                            genus_id = genus.get("Genus")
                            genus_localised = genus.get("Genus_Localised")
                            if bio_found and genus_id in bio_found:
                                # nothing to do, as the entry is already known
                                pass
                            else:
                                # todo: add min distance for diversity
                                genus_found = Genus(genusid=genus_id, localised=genus_localised)
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
                    geo_is_new = (evt.get("IsNewEntry") == "true")
                    geo_codex_found = self.m.bodies[body_id].geo_found[geo_id] if body_id in self.m.bodies and geo_id in self.m.bodies[body_id].geo_found else None
                    if geo_codex_found is None:
                        geo_codex_found = CodexEntry(codexid=geo_id, localised=geo_localised, is_new=geo_is_new, body_id=body_id)
                    else:
                        if isinstance(geo_codex_found, CodexEntry):
                            geo_codex_found.codexid = geo_id
                            geo_codex_found.localised = geo_localised
                            geo_codex_found.is_new = geo_is_new
                            geo_codex_found.body_id = body_id
                    geo_found[geo_id] = geo_codex_found

        if etype == "ScanOrganic":
            body_int = evt.get("Body")
            body_id = bip + str(body_int)
            genus_id = evt.get("Genus")
            genus_localised = evt.get("Genus_Localised")
            species_localised = evt.get("Species_Localised")
            variant_localised = evt.get("Variant_Localised")
            genus_found = self.m.bodies[body_id].bio_found[genus_id] if body_id in self.m.bodies and genus_id in self.m.bodies[body_id].bio_found else None
            if genus_found is None:
                genus_found = Genus(genusid=genus_id, localised=genus_localised, species_localised=species_localised, variant_localised=variant_localised, scanned_count=1)
            else:
                genus_found.genusid = genus_id
                genus_found.localised = genus_localised
                genus_found.species_localised = species_localised
                genus_found.variant_localised = variant_localised
                genus_found.scanned_count += 1
                # todo: add min distance for diversity

            bio_found[genus_id] = genus_found
            biosignals = self.m.bodies[body_id].biosignals or biosignals or (len(self.m.bodies[body_id].bio_found) if self.m.bodies[body_id].bio_found else 0)

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
                #  rings=rings,
                total_bodies=total_bodies,
            )

        # nothing to safe here, just update the target
        if etype == "Location":
            bodyid_int = evt.get("BodyID")
            body_id = bip + str(bodyid_int)
            self.m.target_body_id = body_id

        if update_gui and self.m.target_body_id :
            self.m.set_target(self.m.target_body_id )


