# functions to convert spansh data format into ed-journal format  for easier processing
from typing import List, Dict


def get_journal_ring_class(spansh_ring_class: str) -> str:
    if spansh_ring_class == "Icy":
        return "eRingClass_Icy"
    if spansh_ring_class == "Metal Rich":
        return "eRingClass_MetalRich"
    if spansh_ring_class == "Metallic":
        return "eRingClass_Metalic"
    if spansh_ring_class == "Rocky":
        return "eRingClass_Rocky"


