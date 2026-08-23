# Raspberry Pi Optical Tap-Tempo & Stop Bridge for Boss RC-2

A zero-risk, optically isolated hardware bridge that connects a Raspberry Pi's
GPIO to a Boss RC-2 loop station's TRS remote jack. DIY vactrols (LED +
photoresistor, light-sealed) replace manual foot-stomping with programmatic
control over **Tap Tempo** and **Stop**, with no electrical connection
between the Pi and the pedal.

---

## How It Works

The Pi never touches the RC-2 electrically. Each GPIO pin drives an LED
through a current-limiting resistor. That LED is taped face-to-face against
a photoresistor (LDR) inside a light-sealed sleeve — together this pair is
a **vactrol**. When the Pi turns the LED on, the LDR's resistance drops
sharply, which the RC-2 reads as a footswitch closure on its TRS remote
jack. Light is the only thing that crosses the boundary between the two
sides, so the pedal's audio circuitry is fully isolated from the Pi.

---

## Bill of Materials

| Qty | Part |
|---|---|
| 1 | Raspberry Pi (GPIO-capable) |
| 2 | Red LEDs |
| 2 | Photoresistors (LDRs) |
| 2 | Resistors, 220Ω–330Ω (current limiting for the LEDs) |
| 1 | Chopped 3.5mm TRS cable, stepped up to a 1/4" plug |
| — | Black electrical tape or heat-shrink tubing (light sealing) |
| — | Hookup wire, breadboard or solder supplies |

---

## Wiring Diagram

```
                         RASPBERRY PI (BCM)                                                    
                    ┌──────────────────────┐
                    │                      │
                    │   GPIO 17 (Tap) ●────┼───────────────┐
                    │                      │                │
                    │   GPIO 27 (Stop)●────┼───────────┐    │
                    │                      │            │    │
                    │        GND ●─────────┼───────┐    │    │
                    │                      │        │    │    │
                    └──────────────────────┘        │    │    │
                                                      │    │    │
                          ┌───────────────────────────┘    │    │
                          │        ┌────────────────────────┘    │
                          │        │        ┌───────────────────┘
                          │        │        │
                    ┌─────┼────────┼────────┼─────┐
                    │     │        │        │     │
                    │   [GND]   [Stop+]  [Tap+]    │   (Pi side — shared ground rail)
                    │     │        │        │     │
                    │     │      220-330Ω  220-330Ω │
                    │     │        │        │     │
                    │     │      LED2(-)  LED1(-)  │   Stop / Tap Red LEDs
                    │     │      LED2(+)  LED1(+)  │   (anode side, current-limited)
                    │     │        │        │     │
                    └─────┼────────┼────────┼─────┘

     ══════════════════ OPTICAL BRIDGE (light-sealed) ══════════════════

              VACTROL 2 (Stop)             VACTROL 1 (Tap Tempo)
        ┌─────────────────────┐      ┌─────────────────────┐
        │   LED2 taped face-  │      │   LED1 taped face-  │
        │   to-face with      │      │   to-face with      │
        │   Photoresistor 2   │      │   Photoresistor 1   │
        │   inside heat-shrink│      │   inside heat-shrink│
        │   + electrical tape │      │   + electrical tape │
        │   (zero light leak) │      │   (zero light leak) │
        └─────┬──────────┬────┘      └─────┬──────────┬────┘
              │          │                 │          │
           LDR2 leg1  LDR2 leg2         LDR1 leg1  LDR1 leg2
              │          │                 │          │
              │          └──────┐   ┌──────┘          │
              │                 │   │                 │
              │                 │   │                 │
        ══════╪═════════════════╪═══╪═════════════════╪══════
              │                 │   │                 │      TRS CABLE
              │                 │   │                 │      (chopped 3.5mm → 1/4")
              ▼                 ▼   ▼                 ▼
           [RING]            [SLEEVE]              [TIP]
          Stop line         Common Ground        Tap Tempo line
              │                 │                    │
              └─────────────────┼────────────────────┘
                                 │
                          ┌──────┴──────┐
                          │  1/4" TRS   │
                          │    PLUG     │
                          │  (to RC-2   │
                          │  REMOTE jack)│
                          └─────────────┘

  KEY:
  ─── wire            [X] node/junction           ══ isolation boundary
  Pi side is 3.3V logic, fully isolated from the RC-2 side — no electrical
  connection crosses the ══ boundary except through light (LED → LDR).
```

### Connection Summary

**Pi / active side**
| From | Via | To |
|---|---|---|
| GPIO 17 (Tap) | 220–330Ω resistor | LED1 anode (+) |
| LED1 cathode (−) | — | Pi GND |
| GPIO 27 (Stop) | 220–330Ω resistor | LED2 anode (+) |
| LED2 cathode (−) | — | Pi GND |

**Optical bridge (no electrical link)**
| Vactrol | LED | Photoresistor |
|---|---|---|
| 1 — Tap | LED1 | Photoresistor 1, taped face-to-face, fully light-sealed |
| 2 — Stop | LED2 | Photoresistor 2, taped face-to-face, fully light-sealed |

**Cable / passive pedal side (TRS)**
| TRS Contact | Connects to |
|---|---|
| Sleeve | Shared common ground — one leg of Photoresistor 1 **and** one leg of Photoresistor 2 |
| Tip | Photoresistor 1's other leg (Tap Tempo control line) |
| Ring | Photoresistor 2's other leg (Stop control line) |

> Both photoresistors share the Sleeve/ground leg; their other legs go
> separately to Tip and Ring. This is what makes the pedal side fully
> passive — nothing but LDR resistance changes when the Pi pulses a GPIO.

---

## Software: `bpm.py`

**Requirements:** Python 3, `gpiozero` (`pip install gpiozero`). Works on
Pi 4 and Pi 5 — `gpiozero` auto-selects the correct backend.

**Core math:**

```
interval (seconds) = 60 / BPM
```

The script pulses the Tap GPIO HIGH for ~50–100ms at that interval to
sync the RC-2's tempo, and pulses the Stop GPIO once to kill playback.

### Usage

```bash
python3 bpm.py 120                  # tap tempo at 120 BPM, runs until Ctrl+C
python3 bpm.py 90 --taps 8          # send exactly 8 taps at 90 BPM, then exit
python3 bpm.py --stop               # fire the Stop pulse once
python3 bpm.py 120 --gpio-tap 17 --gpio-stop 27 --pulse-ms 80
```

### CLI Options

| Flag | Default | Description |
|---|---|---|
| `bpm` (positional) | — | Target tempo in BPM. Omit if using `--stop` alone. |
| `--stop` | off | Fire a single Stop pulse and exit. |
| `--taps N` | run until Ctrl+C | Send exactly N tap pulses, then exit. |
| `--gpio-tap` | 17 | BCM pin driving the Tap Tempo LED. |
| `--gpio-stop` | 27 | BCM pin driving the Stop LED. |
| `--pulse-ms` | 80 | Pulse width in ms (keep within ~50–100ms). |

---

## Build Notes

- **Light sealing is the most common failure point.** Any leak causes
  false triggers or inconsistent LDR resistance. Use heat-shrink tubing
  over each LED/LDR pair, then wrap in electrical tape.
- **LED brightness / resistor choice** affects how low the LDR's
  resistance drops when lit. Aim for a value in the low hundreds of ohms
  when lit, closer to a real footswitch's near-0Ω closure, by tuning the
  current-limiting resistor within the 220–330Ω range.
- **Pulse width** should stay within ~50–100ms so the RC-2 reads it as a
  deliberate footswitch press rather than noise or a held switch.
- **Ground reference:** the Pi's GND only connects to the LED cathodes —
  it never touches the TRS Sleeve directly. The Sleeve/common ground on
  the pedal side is only linked to the Pi through the photoresistor legs,
  keeping the two sides electrically isolated.

---

## Safety

This design has no electrical path between the Raspberry Pi and the
Boss RC-2. The only thing crossing the isolation boundary is light, so
even a wiring mistake on the Pi side cannot pass current into the pedal.
