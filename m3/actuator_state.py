"""Effective actuator state, evaluated in the physics process's wall clock."""

import math


def effective_control(source, now, timeout):
    stopped = dict(active=False, mode="STOPPED", steer=0, throttle=0)
    if source is None:
        return dict(stopped, reason="bridge_disconnected", source_status="missing")
    try:
        age = now - source["wall"]
        if not math.isfinite(age) or age < 0:
            raise ValueError("invalid clock")
        if age > timeout:
            return dict(stopped, reason="bridge_timeout", source_status="stale")
        mode = source["mode"]
        if mode not in ("STOPPED", "ARMING", "ARMED"):
            raise ValueError("invalid mode")
        for key in ("steer", "throttle"):
            value = source[key]
            if (
                type(value) not in (float, int)
                or not math.isfinite(value)
                or abs(value) > 1
            ):
                raise ValueError("invalid actuator")
        if mode == "ARMED":
            return dict(
                active=True,
                mode=mode,
                reason="armed",
                source_status="fresh",
                steer=source["steer"],
                throttle=source["throttle"],
            )
        return dict(
            stopped,
            mode=mode,
            reason=source.get("reason", "stopped"),
            source_status="fresh",
        )
    except (TypeError, KeyError, ValueError):
        return dict(stopped, reason="invalid_actuator_data", source_status="invalid")
