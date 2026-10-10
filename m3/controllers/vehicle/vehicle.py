"""Webots physics consumer. No browser command or pose teleportation API here."""

from controller import Supervisor
import json, math, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "build/m3"
EVID = ROOT / "evidence/m3"
p = json.loads((ROOT / "m3/parameters.json").read_text())
robot = Supervisor()
step = int(p["step_ms"])
car = robot.getSelf()
names = ["fl", "fr", "rl", "rr"]
drives = []
brakes = []
sensors = []
for n in names:
    motor = robot.getDevice("drive_" + n)
    motor.setPosition(float("inf"))
    motor.setVelocity(0)
    drives.append(motor)
    brakes.append(robot.getDevice("brake_" + n))
    sensor = robot.getDevice("wheel_sensor_" + n)
    sensor.enable(step)
    sensors.append(sensor)
steers = [robot.getDevice("steer_" + n) for n in names[:2]]
ss = [robot.getDevice("steer_sensor_" + n) for n in names[:2]]
for s in ss:
    s.enable(step)
wheels = [robot.getFromDef("WHEEL_" + n.upper()) for n in names]
log = (EVID / ("physics-" + uuid.uuid4().hex + ".jsonl")).open("w", buffering=1)
previous = time.monotonic()
start_wall = previous
start_sim = robot.getTime()
last_log = 0
epoch = None
reverse_wait = 0
direction = 0
while robot.step(step) != -1:
    now = time.monotonic()
    reason = "bridge_timeout"
    active = False
    throttle = steer = 0
    try:
        c = json.loads((RUN / "actuators.json").read_text())
        if 0 <= now - c["wall"] <= p["bridge_timeout_s"] and c["mode"] == "ARMED":
            active = True
            reason = "armed"
            throttle = c["throttle"]
            steer = c["steer"]
        else:
            reason = c.get("reason", "stopped")
    except (OSError, ValueError, KeyError):
        pass
    speed = math.sqrt(sum(v * v for v in car.getVelocity()[:3]))
    desired_direction = (throttle > 0) - (throttle < 0)
    # Reversing first brakes to rest; explicit neutral dwell before opposite drive.
    if desired_direction and direction and desired_direction != direction:
        reverse_wait = robot.getTime() + 0.3
        direction = 0
    if robot.getTime() < reverse_wait or (direction == 0 and speed > 0.05):
        throttle = 0
        reason = "reversal_braking"
    elif desired_direction:
        direction = desired_direction
    if throttle == 0 and speed < 0.03:
        direction = 0
    for motor, brake in zip(drives, brakes):
        brake.setDampingConstant(p["brake_damping_nms"] if throttle == 0 else 0)
        motor.setVelocity(throttle * p["max_wheel_speed_rad_s"])
    for servo in steers:
        servo.setPosition(steer * p["steering_limit_rad"] if active else 0)
    data = dict(
        wall=now,
        unix_ms=time.time() * 1000,
        sim_s=robot.getTime(),
        factor=(robot.getTime() - start_sim) / max(now - start_wall, 0.001),
        position=car.getPosition(),
        orientation=car.getOrientation(),
        velocity=car.getVelocity(),
        speed_m_s=speed,
        wheels=[
            dict(position=w.getPosition(), orientation=w.getOrientation())
            for w in wheels
        ],
        wheel_angles=[s.getValue() for s in sensors],
        steering=[s.getValue() for s in ss],
        contact_count=len(car.getContactPoints(True)),
        contacts=[list(v.point) for v in car.getContactPoints(True)],
        drive=throttle,
        steer=steer,
        reason=reason,
        source=c if "c" in locals() else None,
    )
    if now - last_log >= 0.08:
        last_log = now
        tmp = RUN / "telemetry.tmp"
        tmp.write_text(json.dumps(data))
        tmp.replace(RUN / "telemetry.json")
        log.write(json.dumps(data) + "\n")
