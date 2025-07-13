import math

class PSPSCoordinates:
    __slots__ = ("latitude", "longitude")
    def __init__(self
                 , latitude: float
                 , longitude: float):
        self.latitude = latitude
        self.longitude = longitude

class PSPS:
    def __init__(self,
                 target_coordinates: PSPSCoordinates,
                 planet_radius_m: float = 0.0):
        self.target_coordinates = target_coordinates
        self.planet_radius = planet_radius_m / 1000.0

    def get_distance(self, current_coordinates: PSPSCoordinates = None, target_coordinates: PSPSCoordinates = None):
        if current_coordinates is None or target_coordinates is None or self.planet_radius == 0.0:
            return "N/A"

        raw_discance_km = self._calc_distance(current_coordinates, target_coordinates)

        # determine if we shall return meters or kilometers
        if raw_discance_km < 1:
            distance = f"{raw_discance_km*1000.0:.0f} m"
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

