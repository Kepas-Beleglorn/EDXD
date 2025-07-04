import json, threading, queue

from EDXD.data_handler.model import Model
from EDXD.data_handler.helper.pausable_thread import PausableThread
import inspect
from EDXD.globals import logging, BODY_ID_PREFIX as bip



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
            frame = inspect.currentframe()
            func_name = frame.f_code.co_name
            arg_info = inspect.getargvalues(frame)
            logging.error(f"{'_' * 10}")
            logging.error(f"Exception in {func_name} with arguments {arg_info.locals}")
            logging.error(f"Exception type: {type(e).__name__}")
            logging.error(f"Exception args: {e.args}")
            logging.error(f"Exception str: {str(e)}")
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

        # initialize all parameters fomr update_body
        systemaddress   = evt.get("SystemAddress")
        bodyid_int      = None
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
                body_id = bip + str(bodyid_int)
                body_type = evt.get("PlanetClass") or evt.get("StarType")
                if body_type is None and "Belt Cluster" in body_name:
                    body_type = "Belt Cluster"
                scoopable = body_type in ["K", "G", "B", "F", "O", "A", "M"]
                materials = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}


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
                        bio_found = {genus["Genus_Localised"]: 0 for genus in evt.get("Genuses", [])}

                    if signal.get("Type") == "$SAA_SignalType_Geological;":
                        geosignals = signal.get("Count")

        # ── SRV geology scan (CodexEntry, but not if IsNewDiscovery=false) ───
        if etype == "CodexEntry":  # and evt.get("Category") == "$Codex_Category_Geology;":
            bodyid_int = evt.get("BodyID")
            body_id = bip + str(bodyid_int)
            subcategory = evt.get("SubCategory")
            if subcategory == "$Codex_SubCategory_Geology_and_Anomalies;":
                if evt.get("NearestDestination") != "$Fixed_Event_Life_Cloud;":
                    geo_is_new = (evt.get("IsNewEntry") == "true")
                    debug_hint = ""
                    try:
                        geo_found = self.m.bodies[body_id].geo_found  # Copy the existing dict
                        geo_name = evt.get("Name_Localised")
                        if geo_name is not None and geo_name != "":
                            geo_found[geo_name] = geo_is_new  # Add/update entry

                    except Exception as e:
                        frame = inspect.currentframe()
                        func_name = frame.f_code.co_name
                        arg_info = inspect.getargvalues(frame)
                        logging.error(f"{'_' * 10}")
                        logging.error(f"Exception in {func_name} with arguments {arg_info.locals}")
                        logging.error(f"debug_hint[{debug_hint}] {self.m.bodies[body_id].geo_found} vs. {geo_found}")
                        logging.error(f"Exception type: {type(e).__name__}")
                        logging.error(f"Exception args: {e.args}")
                        logging.error(f"Exception str: {str(e)}")

        # save/update data
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
                rings=rings,
            )

        if update_gui and body_name:
            self.m.set_target(body_name)


