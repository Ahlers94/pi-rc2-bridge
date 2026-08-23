#!/usr/bin/env python3
"""
bpm.py -- Optical Tap-Tempo & Stop Bridge for Boss RC-2

Drives two GPIO-controlled LEDs (via DIY vactrols) that optically bridge
into the RC-2's TRS remote jack:
    GPIO Pin A -> Tap Tempo vactrol LED
    GPIO Pin B -> Stop vactrol LED

Switch polarity: Boss footswitch inputs (including the RC-2's remote
jack) are Normally Closed (NC) -- LED ON at rest, briefly OFF for each
tap or stop. Other brands are commonly Normally Open (NO) -- LED OFF at
rest, briefly ON for each tap or stop. Default is NC; pass --polarity no
to switch, e.g. when adapting this bridge to a different pedal.

Requires: gpiozero (works on any GPIO-capable Pi -- Zero through 5;
auto-selects lgpio/RPi.GPIO backend as needed)
    pip install gpiozero

Usage:
    python3 bpm.py 120                 # tap tempo at 120 BPM, NC (default), runs until Ctrl+C
    python3 bpm.py 90 --taps 8         # send exactly 8 taps at 90 BPM, then exit
    python3 bpm.py --stop              # fire the Stop pulse once
    python3 bpm.py 120 --polarity no   # use for a normally-open pedal instead
    python3 bpm.py 120 --gpio-tap 22 --gpio-stop 27 --pulse-ms 80
"""

import argparse
import sys
import time

try:
    from gpiozero import OutputDevice
except ImportError:
    sys.exit(
        "Missing dependency 'gpiozero'. Install with:\n"
        "    pip install gpiozero"
    )

# Defaults -- adjust to match your wiring
# Note: GPIO17 is NOT used here -- on Patchbox OS / Pisound HAT setups it's
# claimed by the onboard "pisound-btn" hardware button (see `gpioinfo`).
DEFAULT_TAP_PIN = 22   # BCM numbering
DEFAULT_STOP_PIN = 27  # BCM numbering
DEFAULT_PULSE_MS = 80  # within the RC-2's expected footswitch press window (50-100ms)
DEFAULT_POLARITY = "nc"  # Boss gear is NC; use --polarity no for NO-style pedals


def device_kwargs(polarity: str) -> dict:
    """
    NC (normally closed): LED on at rest, briefly off for the break.
    NO (normally open):    LED off at rest, briefly on for the press.
    """
    if polarity == "nc":
        return {"active_high": False, "initial_value": True}
    return {"active_high": True, "initial_value": False}


def pulse(pin_device: OutputDevice, pulse_ms: int, label: str) -> None:
    """Momentarily actuate the switch (NC: break; NO: close) to simulate a
    footswitch press, then release it back to rest."""
    pin_device.on()
    time.sleep(pulse_ms / 1000.0)
    pin_device.off()
    print(f"[{label}] pulsed ({pulse_ms} ms)")


def run_tap_tempo(bpm: float, tap_pin: int, pulse_ms: int, taps: int | None, polarity: str) -> None:
    if bpm <= 0:
        sys.exit("BPM must be a positive number.")

    interval = 60.0 / bpm
    if interval <= (pulse_ms / 1000.0):
        sys.exit(
            f"BPM {bpm} gives an interval of {interval*1000:.0f} ms, which is "
            f"shorter than the pulse width ({pulse_ms} ms). Lower the BPM or "
            f"shorten --pulse-ms."
        )

    print(f"Tap tempo: {bpm} BPM -> {interval:.4f}s interval, pulse {pulse_ms}ms, polarity {polarity.upper()}")
    print("Press Ctrl+C to stop." if taps is None else f"Sending {taps} taps.")

    tap = OutputDevice(tap_pin, **device_kwargs(polarity))
    try:
        count = 0
        next_tap = time.monotonic()
        while taps is None or count < taps:
            now = time.monotonic()
            sleep_for = next_tap - now
            if sleep_for > 0:
                time.sleep(sleep_for)
            pulse(tap, pulse_ms, "TAP")
            count += 1
            next_tap += interval
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        tap.close()


def run_stop(stop_pin: int, pulse_ms: int, polarity: str) -> None:
    stop = OutputDevice(stop_pin, **device_kwargs(polarity))
    try:
        pulse(stop, pulse_ms, "STOP")
    finally:
        stop.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Optical Tap-Tempo & Stop Bridge for Boss RC-2"
    )
    parser.add_argument(
        "bpm", type=float, nargs="?", default=None,
        help="Target tempo in beats per minute. Omit if using --stop alone."
    )
    parser.add_argument(
        "--stop", action="store_true",
        help="Fire a single Stop pulse (kills playback) and exit."
    )
    parser.add_argument(
        "--taps", type=int, default=None,
        help="Send this many tap pulses then exit. Default: run until Ctrl+C."
    )
    parser.add_argument(
        "--gpio-tap", type=int, default=DEFAULT_TAP_PIN,
        help=f"BCM pin number for the Tap Tempo LED (default: {DEFAULT_TAP_PIN})"
    )
    parser.add_argument(
        "--gpio-stop", type=int, default=DEFAULT_STOP_PIN,
        help=f"BCM pin number for the Stop LED (default: {DEFAULT_STOP_PIN})"
    )
    parser.add_argument(
        "--polarity", type=str.lower, choices=["nc", "no"], default=DEFAULT_POLARITY,
        help=f"Switch convention: 'nc' (normally closed, e.g. Boss gear) or "
             f"'no' (normally open, most third-party pedals). Default: {DEFAULT_POLARITY}"
    )
    parser.add_argument(
        "--pulse-ms", type=int, default=DEFAULT_PULSE_MS,
        help=f"Pulse width in milliseconds (default: {DEFAULT_PULSE_MS}, "
             f"keep within ~50-100ms to read as a footswitch press)"
    )

    args = parser.parse_args()

    if args.stop and args.bpm is not None:
        sys.exit("Choose either a BPM (tap tempo) or --stop, not both.")

    if args.stop:
        run_stop(args.gpio_stop, args.pulse_ms, args.polarity)
    elif args.bpm is not None:
        run_tap_tempo(args.bpm, args.gpio_tap, args.pulse_ms, args.taps, args.polarity)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
