import math
from dataclasses import dataclass


@dataclass
class StarPosition:
    x: float
    y: float
    z: float

def calculate_star_system_distance(pos1: StarPosition, pos2: StarPosition) -> float:

    """Calculates Euclidean distance between two StarPosition objects."""
    dx = pos2.x - pos1.x
    dy = pos2.y - pos1.y
    dz = pos2.z - pos1.z
    return math.sqrt(dx * dx + dy * dy + dz * dz)

