import math
from EDXD.globals import direction_indicator

class PSPSCoordinates:
    __slots__ = ("latitude", "longitude")

    def __init__(self
                 , latitude: float
                 , longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    def to_dict(self):
        data = {
            "latitude": self.latitude,
            "longitude": self.longitude
        }
        return data

    @classmethod
    def from_dict(cls, d):
        if d is None:
            return None
        if isinstance(d, PSPSCoordinates):
            return d
        return cls(**d)

class PSPS:
    def __init__(self,
                 target_coordinates: PSPSCoordinates,
                 planet_radius_m: float = 0.0):
        self.target_coordinates = target_coordinates
        self.planet_radius = planet_radius_m / 1000.0

    def get_distance(self, current_coordinates: PSPSCoordinates = None, target_coordinates: PSPSCoordinates = None, raw: bool = False):
        if current_coordinates is None or target_coordinates is None or self.planet_radius == 0.0:
            return "N/A"

        raw_discance_km = self._calc_distance(current_coordinates, target_coordinates)

        if raw:
            return raw_discance_km

        # determine if we shall return meters or kilometers
        if raw_discance_km < 1:
            distance = f"{raw_discance_km * 1000.0:.0f} m"
        else:
            distance = f"{raw_discance_km:.2f} km"

        return distance

    def _calc_distance(self, current_coordinates: PSPSCoordinates, target_coordinates: PSPSCoordinates = None):
        if target_coordinates is None:
            target_coordinates = self.target_coordinates

        # convert target coordinates to radians
        rad_lat_target = math.radians(target_coordinates.latitude)
        rad_long_target = math.radians(target_coordinates.longitude)

        # convert current position coordinates to radians
        rad_lat_current = math.radians(current_coordinates.latitude)
        rad_long_current = math.radians(current_coordinates.longitude)

        # get delta
        rad_delta_lat = rad_lat_target - rad_lat_current
        rad_delta_long = rad_long_target - rad_long_current

        # calculate distance with Haversine formula
        #   a = half_chord_length_squared
        #   c = angular_distance
        a = math.sin(rad_delta_lat / 2) ** 2 + math.cos(rad_lat_target) * math.cos(rad_lat_current) * math.sin(rad_delta_long / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = self.planet_radius * c
        return distance

    def get_relative_bearing(self, current_coordinates: PSPSCoordinates, current_heading: float, target_coordinates: PSPSCoordinates = None):
        if self.planet_radius == 0.0:
            return None

        use_target = target_coordinates or self.target_coordinates

        bearing = self._calculate_bearing(current_coordinates, use_target)
        relative_bearing = (bearing - current_heading + 360) % 360
        return direction_indicator(relative_bearing)

    def _calculate_bearing(self, from_pos: PSPSCoordinates, to_pos: PSPSCoordinates):
        lat1 = math.radians(from_pos.latitude)
        lat2 = math.radians(to_pos.latitude)
        delta_lon = math.radians(to_pos.longitude - from_pos.longitude)

        y = math.sin(delta_lon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
        bearing_rad = math.atan2(y, x)
        bearing_deg = (math.degrees(bearing_rad) + 360) % 360
        return bearing_deg
