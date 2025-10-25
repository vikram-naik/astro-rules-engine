# app/core/rules/relations/aspect_handler.py
from datetime import datetime
from typing import Optional
from app.core.common.schemas import ConditionRead
from app.core.astro.interfaces.i_astro_provider import IAstroProvider
from .i_relation import IRelationHandler

class AspectHandler(IRelationHandler):
    """
    Generic aspect handler: compares angular distance against a target angle.
    If cond.value is provided and looks numeric it is used as the target_angle.
    Otherwise, target_angle should be supplied by a wrapper or subclass.
    """

    def __init__(self, target_angle: Optional[float] = None):
        self.target_angle = float(target_angle) if target_angle is not None else None

    def check(self, provider: IAstroProvider, cond: ConditionRead, when: datetime, orb_default: float) -> bool:
        orb = cond.orb if cond.orb is not None else orb_default
        # allow numeric aspect angle in cond.value (highest priority)
        angle = None
        if cond.value is not None:
            try:
                angle = float(cond.value)
            except Exception:
                angle = None
        if angle is None and self.target_angle is not None:
            angle = self.target_angle
        print(f"angle: {angle}")    
        if angle is None:
            # no aspect defined
            return False

        planet = (cond.planet or "").lower()
        target = (cond.target or "").lower()
        print(f"planet: {planet}, target: {target}")
        try:
            lon = provider.longitude(planet, when)
            tlon = provider.longitude(target, when)
        except Exception:
            return False
        print(f"lhs_lon: {lon}, rhs_lon: {tlon}")
        d = provider.angular_distance(lon, tlon)
        print(f"angular_distance: {d}, angle: {angle}, orb: {orb}, abs(d - angle): {abs(d - angle)}")    
        return abs(d - angle) <= orb
