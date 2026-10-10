"""Generate a pinned primitive-only world. All vehicle motion is ODE joint/contact physics."""

import json
from pathlib import Path

root = Path(__file__).resolve().parent
p = json.loads((root / "parameters.json").read_text())
for name, low, high in [
    ("chassis_length_m", 0.1, 1.5),
    ("chassis_width_m", 0.1, 1.5),
    ("chassis_height_m", 0.1, 1.5),
    ("chassis_mass_kg", 0.1, 20),
    ("wheel_radius_m", 0.02, 0.3),
    ("wheel_width_m", 0.001, 0.5),
    ("wheel_mass_kg", 0.01, 5),
    ("tire_friction", 0.1, 2),
    ("steering_limit_rad", 0.05, 0.6),
    ("step_ms", 1, 32),
]:
    assert type(p[name]) in (int, float) and low <= p[name] <= high, name
assert 0 < p["wheelbase_m"] < p["chassis_length_m"]
assert p["track_m"] > p["chassis_width_m"]
L, W, H = (p[k] for k in ("chassis_length_m", "chassis_width_m", "chassis_height_m"))
m = p["chassis_mass_kg"]
r = p["wheel_radius_m"]
width = p["wheel_width_m"]
wm = p["wheel_mass_kg"]
inertia = (
    f"{m * (W * W + H * H) / 12} {m * (L * L + H * H) / 12} {m * (L * L + W * W) / 12}"
)
w = f"""#VRML_SIM R2025a utf8
WorldInfo {{ basicTimeStep {p["step_ms"]} coordinateSystem "ENU"
 contactProperties [ ContactProperties {{ material1 "rubber" material2 "ground" coulombFriction [ {p["tire_friction"]} ] bumpSound "" rollSound "" slideSound "" bounce 0 softERP 0.3 softCFM 0.00001 }} ] }}
Viewpoint {{ orientation 0.3 0.7 0.65 2.3 position 2 -2 1.8 }}
Background {{ skyColor [ 0.07 0.10 0.16 ] }}
DirectionalLight {{ direction -1 1 -2 }}
Solid {{ translation 0 0 -0.05 name "ground" contactMaterial "ground"
 children [ Shape {{ appearance PBRAppearance {{ baseColor 0.25 0.32 0.26 roughness 1 metalness 0 }} geometry Box {{ size 20 20 0.1 }} }} ] boundingObject Box {{ size 20 20 0.1 }} }}
DEF OBSTACLE Solid {{ translation 1.8 0 0.10 name "obstacle" contactMaterial "ground"
 children [ Shape {{ appearance PBRAppearance {{ baseColor 0.72 0.38 0.15 roughness 1 metalness 0 }} geometry Box {{ size 0.30 1.2 0.20 }} }} ] boundingObject Box {{ size 0.30 1.2 0.20 }} }}
DEF CAR Robot {{ translation 0 0 0.15 name "provisional 4x4" supervisor TRUE controller "vehicle"
 children [
 Shape {{ appearance PBRAppearance {{ baseColor 0.1 0.65 0.9 roughness 0.6 metalness 0 }} geometry Box {{ size {L} {W} {H} }} }}
"""
for name, x, y in [
    ("fl", p["wheelbase_m"] / 2, p["track_m"] / 2),
    ("fr", p["wheelbase_m"] / 2, -p["track_m"] / 2),
    ("rl", -p["wheelbase_m"] / 2, p["track_m"] / 2),
    ("rr", -p["wheelbase_m"] / 2, -p["track_m"] / 2),
]:
    z = -0.06
    if name[0] == "f":
        w += f"""Hinge2Joint {{ jointParameters HingeJointParameters {{ axis 0 0 1 anchor {x} {y} {z} minStop -0.5 maxStop 0.5 }}
 device [ RotationalMotor {{ name "steer_{name}" sound "" maxVelocity {p["steering_speed_rad_s"]} maxTorque {p["steering_torque_nm"]} minPosition -0.5 maxPosition 0.5 }} PositionSensor {{ name "steer_sensor_{name}" }} ]
 jointParameters2 JointParameters {{ axis 0 1 0 dampingConstant 0.001 }}
 device2 ["""
    else:
        w += f"""HingeJoint {{ jointParameters HingeJointParameters {{ axis 0 1 0 anchor {x} {y} {z} dampingConstant 0.001 }} device ["""
    w += f""" RotationalMotor {{ name "drive_{name}" sound "" maxVelocity {p["max_wheel_speed_rad_s"]} acceleration {p["wheel_acceleration_rad_s2"]} maxTorque {p["wheel_torque_nm"]} }} Brake {{ name "brake_{name}" }} PositionSensor {{ name "wheel_sensor_{name}" }} ]
 endPoint DEF WHEEL_{name.upper()} Solid {{ translation {x} {y} {z} rotation 1 0 0 1.57079632679 name "wheel_{name}" contactMaterial "rubber"
 children [ Shape {{ appearance PBRAppearance {{ baseColor 0.045 0.05 0.06 roughness 1 metalness 0 }} geometry Cylinder {{ radius {r} height {width} subdivision 24 }} }} ]
 boundingObject Cylinder {{ radius {r} height {width} subdivision 24 }}
 physics Physics {{ density -1 mass {wm} }} }} }}
"""
w += f"""] boundingObject Box {{ size {L} {W} {H} }}
 physics Physics {{ density -1 mass {m} centerOfMass [0 0 -0.01] inertiaMatrix [ {inertia}, 0 0 0 ] }} }}
"""
(root / "worlds/offroad.wbt").write_text(w)
