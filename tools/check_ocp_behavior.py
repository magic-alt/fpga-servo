"""Stable-level digital OCP regression on exported physical-pin connectivity.

This does not simulate RC, propagation delay, metastability, rail ramps or MOSFETs.
Rail qualification is supplied as an external predicate; verify it on the bench.
"""
from itertools import permutations, product
import check_netlist_safety as graph

pins = graph.pin_nets

class Circuit:
    def __init__(self):
        self.q = 0
        self.clock = 0
        self.inputs = {"GATE_EN": 0, "FAULT_CLEAR": 0, "OCP_N": 1,
                       "PWR_GOOD": 1, "vio_ok": 1, "va_ok": 1}

    def step(self, **changes):
        self.inputs.update(changes)
        levels = {"/GND": 0, "/VIO_3V3": 1}
        def put(ref, pin, value):
            levels[pins[(ref, pin)]] = int(bool(value))
        def get(ref, pin):
            return levels[pins[(ref, pin)]]
        for name in ["GATE_EN", "FAULT_CLEAR", "OCP_N", "PWR_GOOD"]:
            levels["/" + name] = self.inputs[name]
        # Qualified supervisor RESET outputs, after timeout; not an analog model.
        put("U24", "1", self.inputs["vio_ok"] and self.inputs["va_ok"])
        for a, y in [("1", "7"), ("3", "5"), ("6", "2")]:
            put("U26", y, get("U26", a))
        put("R88", "2", get("R88", "1"))  # DC state after RC settles
        put("U21", "4", get("U21", "2"))
        put("U22", "4", not get("U22", "2"))
        put("U23", "4", all(get("U23", p) for p in ["1", "3", "6"]))
        clock = get("U20", "1")
        if not get("U20", "6"):
            self.q = 0  # asynchronous clear dominates a simultaneous clear edge
        elif not get("U20", "7"):
            raise AssertionError("preset must remain inactive")
        elif clock and not self.clock:
            self.q = get("U20", "2")
        self.clock = clock
        put("U20", "5", self.q)
        put("U11", "4", all(get("U11", p) for p in ["1", "3", "6"]))
        return self.q, get("U11", "4"), levels

    def arm(self):
        assert self.step(GATE_EN=0, FAULT_CLEAR=0)[:2] == (0, 0)
        assert self.step(FAULT_CLEAR=1)[:2] == (1, 0)
        assert self.step(FAULT_CLEAR=0)[:2] == (1, 0)
        assert self.step(GATE_EN=1)[:2] == (1, 1)

checks = 0
for fault in ["OCP_N", "PWR_GOOD", "vio_ok", "va_ok"]:
    c = Circuit()
    c.arm()
    assert c.step(**{fault: 0})[:2] == (0, 0)
    assert c.step(**{fault: 1})[:2] == (0, 0)  # no automatic restart
    assert c.step(FAULT_CLEAR=1)[:2] == (0, 0)  # EN high cannot re-arm
    c.step(GATE_EN=0, FAULT_CLEAR=0)
    assert c.step(FAULT_CLEAR=1)[:2] == (1, 0)
    checks += 1

for fault in ["OCP_N", "PWR_GOOD", "vio_ok", "va_ok"]:
    c = Circuit()
    c.step(FAULT_CLEAR=1)
    assert c.step(**{fault: 0})[:2] == (0, 0)
    assert c.step(**{fault: 1})[:2] == (0, 0)  # clear held high
    c.step(FAULT_CLEAR=0)
    assert c.step(FAULT_CLEAR=1)[:2] == (1, 0)
    c = Circuit()
    c.step(**{fault: 0})
    assert c.step(FAULT_CLEAR=1)[:2] == (0, 0)  # clear during fault
    assert c.step(**{fault: 1})[:2] == (0, 0)
    checks += 2

# Every ordering of qualified power domains rising/falling, then recovery.
for order in permutations(["vio_ok", "va_ok", "PWR_GOOD"]):
    c = Circuit()
    c.step(vio_ok=0, va_ok=0, PWR_GOOD=0)
    for rail in order:
        assert c.step(**{rail: 1})[:2] == (0, 0)
    c.arm()
    for rail in reversed(order):
        assert c.step(**{rail: 0})[:2] == (0, 0)
    for rail in order:
        assert c.step(**{rail: 1})[:2] == (0, 0)
    checks += 1

c = Circuit()
c.arm()
assert c.step(OCP_N=0, FAULT_CLEAR=1)[:2] == (0, 0)
assert c.step(OCP_N=1)[:2] == (0, 0)
checks += 1

# Enumerate all six PWM states; each actual AND output must obey RUN_OK.
for q, en, pg in product([0, 1], repeat=3):
    c = Circuit()
    c.q = q
    armed, run, levels = c.step(GATE_EN=en, PWR_GOOD=pg)
    for mask in range(64):
        for index, gate in enumerate(["U8", "U9", "U10"]):
            for channel, (a, b, out) in enumerate([("1", "2", "3"), ("5", "6", "7")]):
                raw = (mask >> (index * 2 + channel)) & 1
                levels[pins[(gate, a)]] = raw
                output = pins[(gate, out)]
                levels[output] = int(levels[pins[(gate, a)]] and levels[pins[(gate, b)]])
                driver_pin = str(index + 4 if channel == 0 else index + 1)
                assert levels[pins[("U1", driver_pin)]] == (raw and run), (gate, out, mask)
        checks += 1
print(f"OCP DIGITAL BEHAVIOR CHECK PASSED: {checks} scenarios; stable levels only")
