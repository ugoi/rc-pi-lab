"""Wire contract emitted by model/pca9685.c (one JSON object per newline)."""
import json
import math

MAX_FRAME = 4096
EVENTS = {'reset', 'start_write', 'start_read', 'pointer', 'write', 'read',
          'stop', 'bridge_open', 'bridge_closed'}


def decode_frame(line):
    """Return a validated device row, or ValueError; never coerce PWM values."""
    if len(line) > MAX_FRAME:
        raise ValueError('frame exceeds 4096 bytes')
    try:
        row = json.loads(line)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError('invalid JSON') from exc
    if not isinstance(row, dict):
        raise ValueError('expected object')
    if set(row) != {'seq', 'ns', 'event', 'reg', 'value', 'mode1', 'mode2',
                    'prescale', 'period_us', 'high_us'}:
        raise ValueError('missing or unknown fields')
    for key, lower, upper in [('seq', 1, 2**64-1), ('ns', 0, 2**63-1),
                              ('reg', -1, 255), ('value', -1, 255),
                              ('mode1', 0, 255), ('mode2', 0, 255),
                              ('prescale', 3, 255)]:
        value = row.get(key)
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f'invalid {key}')
    if not isinstance(row.get('event'), str) or row['event'] not in EVENTS:
        raise ValueError('invalid event')
    period = row.get('period_us')
    # Model uses a fixed 25-MHz oscillator, with prescale in [3,255].
    if type(period) not in (int, float) or not 0 < period <= 41943.04:
        raise ValueError('invalid period_us')
    values = row.get('high_us')
    if not isinstance(values, list) or len(values) != 16:
        raise ValueError('high_us must contain 16 channels')
    for value in values:
        if (type(value) not in (int, float) or not 0 <= value <= period
                or not math.isfinite(value)):
            raise ValueError('high_us must be finite numbers within the period')
    return row
