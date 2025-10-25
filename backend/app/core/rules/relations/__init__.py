# app/core/rules/relations/__init__.py
from app.core.db.enums import Relation
from .registry import register_relation
from .conjunction_handler import ConjunctionHandler
from .aspect_handler import AspectHandler
from .axis_handler import AxisHandler
from .nakshatra_handler import NakshatraOwnedHandler
from .sign_handler import SignHandler
from .house_relative_handler import HouseRelativeHandler

from .combust_handler import CombustHandler
from .retrograde_handler import RetrogradeHandler

# Register generic handlers
register_relation(Relation.conjunct_with, ConjunctionHandler)
register_relation(Relation.in_axis, AxisHandler)
register_relation(Relation.in_nakshatra_owned_by, NakshatraOwnedHandler)
register_relation(Relation.in_sign, SignHandler)
register_relation(Relation.in_house_relative_to, HouseRelativeHandler)
# Generic numeric aspect handler
register_relation(Relation.aspect_with, AspectHandler)

# Register named aspects as AspectHandler instances via small wrapper classes
# We register lambdas that the registry will instantiate to AspectHandler with target angle.
# Because registry expects a class, we define tiny wrapper classes.

class _Trine(AspectHandler):
    def __init__(self): super().__init__(120.0)
class _Square(AspectHandler):
    def __init__(self): super().__init__(90.0)
class _Sextile(AspectHandler):
    def __init__(self): super().__init__(60.0)
class _Opposition(AspectHandler):
    def __init__(self): super().__init__(180.0)
class _Quincunx(AspectHandler):
    def __init__(self): super().__init__(150.0)
class _Semisextile(AspectHandler):
    def __init__(self): super().__init__(30.0)
class _Semisquare(AspectHandler):
    def __init__(self): super().__init__(45.0)
class _Quintile(AspectHandler):
    def __init__(self): super().__init__(72.0)
class _SesquiQuadrate(AspectHandler):
    def __init__(self): super().__init__(135.0)

register_relation(Relation.trine_with, _Trine)
register_relation(Relation.square_with, _Square)
register_relation(Relation.sextile_with, _Sextile)
register_relation(Relation.opposition_with, _Opposition)
register_relation(Relation.quincunx_with, _Quincunx)
register_relation(Relation.semisextile_with, _Semisextile)
register_relation(Relation.semisquare_with, _Semisquare)
register_relation(Relation.quintile_with, _Quintile)
register_relation(Relation.sesquiquadrate_with, _SesquiQuadrate)

register_relation(Relation.combust_by_sun, CombustHandler)
register_relation(Relation.retrograde, RetrogradeHandler)