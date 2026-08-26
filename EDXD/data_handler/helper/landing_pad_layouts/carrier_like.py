from dataclasses import dataclass
from typing import Optional, List

# dimensions and margin
OFFSET_X  :int  = 25
OFFSET_Y  :int  = 75
MARGIN    :int  = 2
RATIO     :float  = 1.5
WIDTH_S   :int  = 40
HEIGHT_S  :int  = int(RATIO*WIDTH_S)
WIDTH_M   :int  = int(1.5*WIDTH_S)
HEIGHT_M  :int  = int(RATIO*WIDTH_M)
WIDTH_L   :int  = int(2*WIDTH_S)
HEIGHT_L  :int  = int(RATIO*WIDTH_L)

@dataclass
class CarrierPad:
    """Represents a single carrier landing pad"""
    pad_number: int
    size: str  # 'L', 'M', or 'S'
    x: int  # X position in pixels
    y: int  # Y position in pixels
    width: int
    height: int


@dataclass
class CarrierLayout:
    """Fleet carrier landing pad layout"""
    carrier_name: str
    carrier_id: str
    pads: List[CarrierPad]
    assigned_pad: Optional[int] = None

class CarrierDataGenerator:
    """Generate fleet carrier landing pad layout with precise pixel positioning"""

    @staticmethod
    def generate_carrier(carrier_name: str, carrier_id: str) -> CarrierLayout:
        """
        Generate carrier layout with exact pixel positions.
        """
        pads = []

        # Define each pad with exact pixel coordinates
        # Format: (pad_number, size, x_position, y_position)

        X1_L = 2 * WIDTH_S + 4 * MARGIN     # Left large pads
        X2_L = X1_L + 2 * MARGIN + WIDTH_L  # Right large pads

        X1_M = X1_L - 2 * MARGIN - WIDTH_M  # Left medium pads
        X2_M = X2_L + 2 * MARGIN + WIDTH_L  # Right medium pads

        Y1_M = 4 * HEIGHT_L + 6 * MARGIN - HEIGHT_M # lower medium pads
        Y2_M = Y1_M - 2 * MARGIN - HEIGHT_M         # upper medium pads

        X_S = X2_L + WIDTH_L + 2 * MARGIN
        Y_S = Y2_M - 2 * MARGIN - HEIGHT_S

        pad_layout = [
            # Large pads
            {"num": 7, "size": "L", "x":    X1_L,   "y": 0},
            {"num": 8, "size": "L", "x":    X2_L,   "y": 0},
            {"num": 5, "size": "L", "x":    X1_L,   "y": HEIGHT_L + 2 * MARGIN},
            {"num": 6, "size": "L", "x":    X2_L,   "y": HEIGHT_L + 2 * MARGIN},
            {"num": 3, "size": "L", "x":    X1_L,   "y": 2 * HEIGHT_L + 4 * MARGIN},
            {"num": 4, "size": "L", "x":    X2_L,   "y": 2 * HEIGHT_L + 4 * MARGIN},
            {"num": 1, "size": "L", "x":    X1_L,   "y": 3 * HEIGHT_L + 6 * MARGIN},
            {"num": 2, "size": "L", "x":    X2_L,   "y": 3 * HEIGHT_L + 6 * MARGIN},

            # Medium pads
            {"num": 9,  "size": "M", "x": X1_M, "y": Y1_M},
            {"num": 10, "size": "M", "x": X1_M, "y": Y2_M},
            {"num": 11, "size": "M", "x": X2_M, "y": Y1_M},
            {"num": 12, "size": "M", "x": X2_M, "y": Y2_M},

            # Small pads
            {"num": 13, "size": "S", "x": 0, "y": Y_S},
            {"num": 16, "size": "S", "x": WIDTH_S + 2 * MARGIN, "y": Y_S},
            {"num": 14, "size": "S", "x": X_S, "y": Y_S},
            {"num": 15, "size": "S", "x": X_S + 2 * MARGIN + WIDTH_S, "y": Y_S},
        ]

        for pad_info in pad_layout:
            size = str(pad_info["size"])
            spec = CarrierDataGenerator.get_pad_spec(size)

            pads.append(CarrierPad(
                pad_number=int(pad_info["num"]),
                size=size,
                x=int(pad_info["x"]),
                y=int(pad_info["y"]),
                width=spec['width'],
                height=spec['height']
            ))

        return CarrierLayout(
            carrier_name=carrier_name,
            carrier_id=carrier_id,
            pads=pads,
            assigned_pad=5  # Default assigned pad
        )

    @staticmethod
    def get_pad_spec(size: str) -> dict:
        """Get pad dimensions for a given size"""
        specs = {
            'S': {'width': WIDTH_S, 'height': HEIGHT_S},
            'M': {'width': WIDTH_M, 'height': HEIGHT_M},
            'L': {'width': WIDTH_L, 'height': HEIGHT_L},
        }
        return specs[size]