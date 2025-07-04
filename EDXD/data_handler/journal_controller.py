import json, threading, queue
from os import WCONTINUED

from EDXD.data_handler.model import Model, Body
from EDXD.data_handler.helper.pausable_thread import PausableThread

# ---------------------------------------------------------------------------
# controller thread – turns Journal lines into Model updates
# ---------------------------------------------------------------------------
class JournalController(PausableThread, threading.Thread):
    def __init__(self, q: "queue.Queue[str]", model: Model):
        super().__init__()
        self.q = q
        self.m = model

    def _process_data(self):
        # noinspection PyBroadException
        evt = None
        try:
            evt = json.loads(self.q.get())
        except Exception:
            return

        self.process_event(evt=evt, update_gui=True)

    def process_event(self, evt, update_gui: bool):
        etype = evt.get("event")

        # ───── jump to a new system ───────────────────────────────
        if etype != "FSDJump":
            self.m.just_jumped = False
        if etype == "FSDJump":
            self.m.just_jumped = True
            self.m.total_bodies = None
            self.m.target_body = None
            self.m.sel_target = None
            self.m.reset_system(evt.get("StarSystem"), evt.get("SystemAddress"))

        elif etype in ("FSSDiscoveryScan", "FSSAllBodiesFound"):
            if evt.get("BodyCount") is not None:
                self.m.total_bodies = evt.get("BodyCount")

        elif etype == "Scan":
            if self.m.system_name is None:  # first scan in a fresh session
                self.m.reset_system(evt.get("StarSystem"), evt.get("SystemAddress"))
            body_name = evt.get("BodyName")
            # todo: process ring data properly
            if body_name.endswith("Ring"):
                pass # skip for now
            else:
                distance = evt.get("DistanceFromArrivalLS")
                body_id = evt.get("BodyID")
                body_type = evt.get("PlanetClass") or evt.get("StarType")
                if body_type is None and "Belt Cluster" in body_name:
                    body_type = "Belt Cluster"
                scoopable = body_type in ["K", "G", "B", "F", "O", "A", "M"]
                mats = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}

                self.m.update_body(systemaddress=evt.get("SystemAddress"), body_id=body_id,  body_name=body_name, body_type=body_type, scoopable=scoopable, landable=evt.get("Landable", False),
                                   materials=mats, scandata=evt, distance=distance)

        elif etype == "SAAMaterialsFound":
            body_name = evt.get("BodyName")
            body_id = evt.get("BodyID")
            mats = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}

            self.m.update_body(systemaddress=evt.get("SystemAddress"), body_id=body_id, body_name=body_name, landable=True, materials=mats)
            if update_gui:
                self.m.set_target(body_name)

        elif etype in ("FSSBodySignals", "SAASignalsFound"):
            body_name = evt.get("BodyName")
            # todo: process rings properly
            if body_name.endswith("Ring"):
                pass  # skip for now
            else:
                body_id = evt.get("BodyID")
                for signal in evt.get("Signals", []):
                    cbio = 0
                    cgeo = 0
                    bio_found = None
                    geo_found = None

                    if signal.get("Type") == "$SAA_SignalType_Biological;":
                        cbio = signal.get("Count")
                        bio_found = {genus["Genus_Localised"]: 0 for genus in evt.get("Genuses", [])}

                    if signal.get("Type") == "$SAA_SignalType_Geological;":
                        cgeo = signal.get("Count")

                    self.m.update_body(systemaddress=evt.get("SystemAddress"), body_id=body_id, body_name=body_name, landable=evt.get("Landable", False), biosignals=cbio, geosignals=cgeo, bio_found=bio_found, geo_found=geo_found)

        # ── SRV geology scan (CodexEntry, but not if IsNewDiscovery=false) ───
        elif etype == "CodexEntry":  # and evt.get("Category") == "$Codex_Category_Geology;":
            body_id = evt.get("BodyID")
            subcategory = evt.get("SubCategory")
            if subcategory == "$Codex_SubCategory_Geology_and_Anomalies;":
                geo_is_new = (evt.get("IsNewEntry") == "true")
                if self.m.bodies[body_id].geo_found:
                    geo_entity = {{evt.get("Name_Localised"): geo_is_new}, self.m.bodies[body_id].geo_found.items()}
                else:
                    geo_entity = {evt.get("Name_Localised"): geo_is_new}

                self.m.update_body(systemaddress=evt.get("SystemAddress"), body_id=body_id, geo_found=geo_entity)




