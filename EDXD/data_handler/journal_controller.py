import json, threading, queue
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
        # In JournalController.run()
        if etype == "FSDJump":
            self.m.just_jumped = True
            self.m.total_bodies = None
            self.m.target_body = None
            self.m.sel_target = None
            self.m.reset_system(evt.get("StarSystem"), evt.get("SystemAddress"))

        elif etype in ("FSSDiscoveryScan", "FSSAllBodiesFound"):
            # Now update bodies/count
            for entry in evt.get("Bodies", []):
                bn = entry.get("BodyName")
                if bn and bn not in self.m.bodies:
                    self.m.bodies[bn] = Body(name=bn, landable=False, materials={})
            if evt.get("BodyCount") is not None:
                self.m.total_bodies = evt.get("BodyCount")

        # ── on-foot DNA sample or SRV organic scan ─────────────────────
        elif etype in ("ExobiologySample", "OrganicScan"):
            body = evt.get("BodyName")  # present in Odyssey 4.0+
            genus = evt.get("Genus") or evt.get("Species")  # 4.1 uses "Species"
            if body and genus:
                b = self.m.bodies.setdefault(body, Body(name=body, landable=False, materials={}))
                b.bio_found[genus] = min(b.bio_found.get(genus, 0) + 1, 3)

        # ── SRV geology scan (CodexEntry, but not if IsNewDiscovery=false) ───
        elif etype == "CodexEntry" and evt.get("Category") == "$Codex_Category_Geology;":
            body = evt.get("BodyName")
            site = evt.get("Name") or evt.get("EntryID")
            if body and site:
                b = self.m.bodies.setdefault(body, Body(name=body, landable=False, materials={}))
                b.geo_found[site] = True

        elif etype == "Scan":
            if self.m.system_name is None:  # first scan in a fresh session
                self.m.reset_system(evt.get("StarSystem"), evt.get("SystemAddress"))
            distance = evt.get("DistanceFromArrivalLS")
            body_name = evt.get("BodyName")
            body_type = evt.get("PlanetClass") or evt.get("StarType")
            if body_type is None and "Belt Cluster" in body_name:
                body_type = "Belt Cluster"
            scoopable = body_type in ["K", "G", "B", "F", "O", "A", "M"]
            mats = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}
            self.m.update_body(systemaddress=evt.get("SystemAddress"), name=body_name, body_type=body_type, scoopable=scoopable, landable=evt.get("Landable", False), materials=mats, scandata=evt,
                               distance=distance)

        elif etype in ("FSSBodySignals", "SAASignalsFound"):
            body_name = evt.get("BodyName")
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

                self.m.update_body(systemaddress=evt.get("SystemAddress"), name=body_name, landable=evt.get("Landable", False), biosignals=cbio, geosignals=cgeo, bio_found=bio_found, geo_found=geo_found)


        elif etype == "SAAMaterialsFound":
            body_name = evt.get("BodyName")
            mats = {m["Name"]: m["Percent"] for m in evt.get("Materials", [])}
            # noinspection PyArgumentList
            self.m.update_body(systemaddress=evt.get("SystemAddress"), name=body_name, landable=True, materials=mats)
            if update_gui:
                self.m.set_target(body_name)

        # --- in-game target changed -----------------------------------
        elif etype in ("FSDTarget", "Target", "SAATarget", "SupercruiseTarget"):
            name = evt.get("Name") or evt.get("BodyName")
            if name and update_gui:
                self.m.set_target(name)
