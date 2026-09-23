from EDXD.data_handler.helper.dotted_dictionary import DotDict, create_dot_dict_from_string, load_json_from_url_as_dotdict


SOURCE_FSD_MODULES = "https://raw.githubusercontent.com/EDCD/coriolis-data/master/modules/standard/frame_shift_drive.json"
SOURCE_FSD_BOOSTER = "https://raw.githubusercontent.com/EDCD/coriolis-data/master/modules/internal/guardian_fsd_booster.json"

class ShipFSDModules:
    def __init__(self):
        self.fsd_modules: DotDict = load_json_from_url_as_dotdict(SOURCE_FSD_MODULES)
        self.fsd_booster: DotDict = load_json_from_url_as_dotdict(SOURCE_FSD_BOOSTER)

    @staticmethod
    def _get_fsd_module_from_slef(ship_data: DotDict) -> DotDict | None:
        fsd_module = None
        for module in ship_data.data.Modules:
            if module.Slot == "FrameShiftDrive":
                fsd_module = module
                break

        return DotDict(fsd_module)

    @staticmethod
    def _get_fsd_boost_module_from_slef(ship_data: DotDict) -> DotDict | None:
        fsd_module = None
        for module in ship_data.data.Modules:
            if "guardianfsdbooster" in module.Item:
                fsd_module = module
                break

        return DotDict(fsd_module)

    def get_optimal_mass(self, ship_data: DotDict) -> float:
        # Assuming you saved the file as 'self_loadout.json' in the same directory
        optimal_mass = 0
        fsd_item = ""
        try:
            fsd_module = self._get_fsd_module_from_slef(ship_data)

            if fsd_module:
                fsd_item = fsd_module.Item
                if hasattr(fsd_module, 'Engineering'):
                    # Accessing modifiers
                    for mod in fsd_module.Engineering.Modifiers:
                        if mod.Label == "FSDOptimalMass":
                            optimal_mass = mod.Value
                            break

        except AttributeError as e:
            print(f"Access Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        if optimal_mass == 0:
            for mod in self.fsd_modules.fsd:
                if mod.symbol.lower() == fsd_item.lower():
                    optimal_mass = mod.optmass
                    break

        return optimal_mass

    def get_max_fuel_per_jump(self, ship_data: DotDict) -> float:
        fsd_item = ""
        max_fuel_per_jump: float = 0.0
        try:
            fsd_module = self._get_fsd_module_from_slef(ship_data)

            if fsd_module:
                fsd_item = fsd_module.Item

        except AttributeError as e:
            print(f"Access Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        for mod in self.fsd_modules.fsd:
            if mod.symbol.lower() == fsd_item.lower():
                max_fuel_per_jump = mod.maxfuel
                break

        return max_fuel_per_jump

    def get_fuel_multiplier(self, ship_data: DotDict) -> float:
        fsd_item = ""
        fuel_multiplier: float = 0.0
        try:
            fsd_module = self._get_fsd_module_from_slef(ship_data)

            if fsd_module:
                fsd_item = fsd_module.Item

        except AttributeError as e:
            print(f"Access Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        for mod in self.fsd_modules.fsd:
            if mod.symbol.lower() == fsd_item.lower():
                fuel_multiplier = mod.fuelmul
                break

        return fuel_multiplier

    def get_fuel_power(self, ship_data: DotDict) -> float:
        fsd_item = ""
        fuel_power: float = 0.0
        try:
            fsd_module = self._get_fsd_module_from_slef(ship_data)

            if fsd_module:
                fsd_item = fsd_module.Item

        except AttributeError as e:
            print(f"Access Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        for mod in self.fsd_modules.fsd:
            if mod.symbol.lower() == fsd_item.lower():
                fuel_power = mod.fuelpower
                break

        return fuel_power

    def get_jump_boost(self, ship_data: DotDict) -> float:
        fsd_item = ""
        fsd_boost: float = 0.0
        try:
            fsd_module = self._get_fsd_boost_module_from_slef(ship_data)

            if fsd_module:
                fsd_item = fsd_module.Item

        except AttributeError as e:
            print(f"Access Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        for mod in self.fsd_booster.gfsb:
            if mod.symbol.lower() == fsd_item.lower():
                fsd_boost = mod.jumpboost
                break

        return fsd_boost

    def get_super_charge_multiplier(self, ship_data: DotDict) -> int:
        fsd_item = ""
        sc_multiplier: int = 4
        try:
            fsd_module = self._get_fsd_module_from_slef(ship_data)

            if fsd_module:
                fsd_item = fsd_module.Item

        except AttributeError as e:
            print(f"Access Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        if str(fsd_item).lower().endswith("_mkii"):
            sc_multiplier = 6

        return sc_multiplier



