from dataclasses import dataclass
from typing import Optional, List, Tuple

@dataclass
class LandingPad:
    """Represents a single landing pad"""
    pad_number: int
    clock_pos: int
    start_angle: float
    end_angle: float
    ring_start: int
    ring_end: int


@dataclass
class StationLayout:
    """Station landing pad layout"""
    station_name: str
    station_type: str
    pads: List[LandingPad]
    assigned_pad: Optional[int] = None

class CoriolisDataGenerator:
    """Generate Coriolis station layout from specification table"""

    @staticmethod
    def get_clock_angles(clock_num: int) -> Tuple[float, float]:
        """Get start and end angles for a clock position (30° segments)"""
        # Clock 12 = North (-90°), Clock 6 = South (-270° or 90°)
        # Each clock is 30° wide, centered on the clock number
        center = (clock_num - 3) * 30.0

        start = center - 14.0
        end = center + 14.0

        return start, end

    @staticmethod
    def generate_coriolis(station_name: str, station_type: str) -> StationLayout:
        pads = []

        # Exact pad layout as specification matrix
        # Format: (pad_number, clock_position, ring_start, ring_end)
        # pad_number = 0 means GAP
        match station_type:
            case "AsteroidBase":
                pad_layout = [
                    (0, 6, 7, 7),
                    (2, 6, 4, 6),
                    (0, 6, 1, 3),
                    (5, 7, 6, 7),
                    (0, 7, 5, 5),
                    (7, 7, 3, 4),
                    (0, 7, 1, 2),
                    (0, 8, 4, 7),
                    (10, 8, 1, 3),
                    (0, 9, 6, 7),
                    (12, 9, 5, 5),
                    (0, 9, 3, 4),
                    (15, 9, 1, 2),
                    (0, 10, 7, 7),
                    (17, 10, 4, 6),
                    (0, 10, 1, 3),
                    (20, 11, 6, 7),
                    (0, 11, 5, 5),
                    (22, 11, 3, 4),
                    (0, 11, 1, 2),
                    (24, 12, 5, 7),
                    (0, 12, 1, 4),
                    (26, 1, 6, 7),
                    (27, 1, 5, 5),
                    (0, 1, 4, 4),
                    (29, 1, 3, 3),
                    (0, 1, 1, 2),
                    (0, 2, 7, 7),
                    (32, 2, 4, 6),
                    (0, 2, 1, 3),
                    (0, 3, 5, 7),
                    (37, 3, 3, 4),
                    (0, 3, 1, 2),
                    (0, 4, 4, 7),
                    (40, 4, 1, 3),
                    (0, 5, 6, 7),
                    (42, 5, 5, 5),
                    (0, 5, 3, 4),
                    (45, 5, 1, 2),
                ]
            case _:
                pad_layout = [
                    (1, 6, 7, 7),
                    (2, 6, 4, 6),
                    (3, 6, 2, 3),
                    (4, 6, 1, 1),
                    (5, 7, 6, 7),
                    (6, 7, 5, 5),
                    (7, 7, 3, 4),
                    (8, 7, 1, 2),
                    (9, 8, 5, 7),
                    (0, 8, 4, 4),  # GAP
                    (10, 8, 1, 3),
                    (11, 9, 6, 7),
                    (12, 9, 5, 5),
                    (13, 9, 4, 4),
                    (14, 9, 3, 3),
                    (15, 9, 1, 2),
                    (16, 10, 7, 7),
                    (17, 10, 4, 6),
                    (18, 10, 2, 3),
                    (19, 10, 1, 1),
                    (20, 11, 6, 7),
                    (21, 11, 5, 5),
                    (22, 11, 3, 4),
                    (23, 11, 1, 2),
                    (24, 12, 5, 7),
                    (0, 12, 4, 4),  # GAP
                    (25, 12, 1, 3),
                    (26, 1, 6, 7),
                    (27, 1, 5, 5),
                    (28, 1, 4, 4),
                    (29, 1, 3, 3),
                    (30, 1, 1, 2),
                    (31, 2, 7, 7),
                    (32, 2, 4, 6),
                    (33, 2, 2, 3),
                    (34, 2, 1, 1),
                    (35, 3, 6, 7),
                    (36, 3, 5, 5),
                    (37, 3, 3, 4),
                    (38, 3, 1, 2),
                    (39, 4, 5, 7),
                    (0, 4, 4, 4),  # GAP
                    (40, 4, 1, 3),
                    (41, 5, 6, 7),
                    (42, 5, 5, 5),
                    (43, 5, 4, 4),
                    (44, 5, 3, 3),
                    (45, 5, 1, 2),
                ]

        for pad_num, clock_pos, ring_start, ring_end in pad_layout:
            start_angle, end_angle = CoriolisDataGenerator.get_clock_angles(clock_pos)

            pads.append(LandingPad(
                pad_number=pad_num,
                clock_pos=clock_pos,
                start_angle=start_angle,
                end_angle=end_angle,
                ring_start=ring_start,
                ring_end=ring_end
            ))

        return StationLayout(
            station_name=station_name,
            station_type=station_type,
            pads=pads,
            assigned_pad=29
        )

