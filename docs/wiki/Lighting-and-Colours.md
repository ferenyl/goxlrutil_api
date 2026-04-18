# Lighting & Colours

The library exposes the full GoXLR LED control API. Colours are passed as
either a `Colour` instance or a plain 6-character hex string (`RRGGBB` without `#`).

---

## The `Colour` Helper

```python
from goxlrutil_api import Colour

# From RGB components
red   = Colour(255, 0, 0)
teal  = Colour(0, 200, 180)

# From hex strings (# is optional)
orange = Colour.from_hex("#FF8800")
white  = Colour.from_hex("FFFFFF")

# From a packed 24-bit integer
blue = Colour.from_int(0x0000FF)

# Named constants
Colour.BLACK    # (0, 0, 0)
Colour.WHITE    # (255, 255, 255)
Colour.RED      # (255, 0, 0)
Colour.GREEN    # (0, 255, 0)
Colour.BLUE     # (0, 0, 255)
Colour.YELLOW   # (255, 255, 0)
Colour.CYAN     # (0, 255, 255)
Colour.MAGENTA  # (255, 0, 255)
Colour.ORANGE   # (255, 128, 0)
Colour.PURPLE   # (128, 0, 255)
Colour.PINK     # (255, 105, 180)

# Dim a colour (default 30 % brightness)
dimmed_red = Colour.RED.dimmed()        # Colour(76, 0, 0)
dimmed_red = Colour.RED.dimmed(0.1)     # Colour(25, 0, 0)

# str(colour) → "FF0000" — the daemon wire format
print(str(Colour.RED))   # → "FF0000"
```

Plain hex strings are accepted wherever a `Colour` is expected:

```python
await client.set_global_colour(serial, "FF8800")  # orange, no Colour object needed
```

---

## Global & Simple Colour Targets

```python
from goxlrutil_api.protocol.types import SimpleColourTargets

# Global accent colour (affects animations and unassigned LEDs)
await client.set_global_colour(serial, Colour.PURPLE)

# Named single-colour targets: Global, Accent, ScribbleBack
await client.set_simple_colour(serial, SimpleColourTargets.Accent, Colour.CYAN)
await client.set_simple_colour(serial, SimpleColourTargets.ScribbleBack, "#1A1A2E")
```

---

## Button Colours

Each button has an *on* (active) colour and an *off* (inactive) colour.

```python
from goxlrutil_api.protocol.types import Button

# Set active colour; off colour defaults to a 30 % dimmed version of on colour
await client.set_button_colour(serial, Button.Bleep, Colour.RED)

# Set both explicitly
await client.set_button_colour(serial, Button.Cough, Colour.ORANGE, Colour.from_hex("331100"))
```

### Button Off-State Style

```python
from goxlrutil_api.protocol.types import ButtonColourOffStyle

# ButtonColourOffStyle values: Dimmed, Colour2, Dimmed2
await client.set_button_off_style(serial, Button.Bleep, ButtonColourOffStyle.Dimmed)
await client.set_button_off_style(serial, Button.Cough, ButtonColourOffStyle.Colour2, Colour.BLUE)
```

### Button Group Colours

```python
from goxlrutil_api.protocol.types import ButtonColourGroups

# ButtonColourGroups values: FaderMute, EffectSelector, EffectTypes
await client.set_button_group_colour(serial, ButtonColourGroups.FaderMute, Colour.BLUE, Colour.from_hex("001040"))
await client.set_button_group_colour(serial, ButtonColourGroups.EffectTypes, Colour.GREEN, Colour.from_hex("003300"))
```

---

## Fader Colours

```python
from goxlrutil_api.protocol.types import FaderName, FaderDisplayStyle

# Set top and bottom colours for fader A
await client.set_fader_colour(serial, FaderName.A, Colour.CYAN, Colour.BLUE)
await client.set_fader_colour(serial, FaderName.B, "#00FF88", "#0044FF")

# Set display style for a single fader
# FaderDisplayStyle values: TwoColour, Gradient, Meter, GradientMeter
await client.set_fader_display_style(serial, FaderName.A, FaderDisplayStyle.Gradient)

# Apply one style to all four faders simultaneously
await client.set_all_fader_display_style(serial, FaderDisplayStyle.GradientMeter)
```

---

## Encoder Colours

Each effect encoder (Reverb, Pitch, Echo, Gender) has three LED zones:

```python
from goxlrutil_api.protocol.types import EncoderColourTargets

# EncoderColourTargets values: Reverb, Pitch, Echo, Gender
await client.set_encoder_colour(
    serial,
    EncoderColourTargets.Reverb,
    colour_left=Colour.BLUE,    # left arc
    colour_right=Colour.CYAN,   # right arc
    colour_knob=Colour.WHITE,   # knob LED
)
```

---

## Sampler Colours

```python
from goxlrutil_api.protocol.types import SamplerColourTargets, ButtonColourOffStyle

# SamplerColourTargets values: SamplerSelectA, SamplerSelectB, SamplerSelectC
await client.set_sampler_colour(
    serial,
    SamplerColourTargets.SamplerSelectA,
    colour_one=Colour.GREEN,
    colour_two=Colour.from_hex("003300"),
    colour_three=Colour.YELLOW,
)

# Off-state style for a sampler selector button
await client.set_sampler_off_style(
    serial,
    SamplerColourTargets.SamplerSelectA,
    ButtonColourOffStyle.Dimmed,
)
```

---

## Animation Mode

```python
from goxlrutil_api.protocol.types import AnimationMode, WaterfallDirection

# AnimationMode values:
#   RetroRainbow, RainbowDark, RainbowBright, Simple, Ripple, None_

# Animated rainbow across all LEDs
await client.set_animation_mode(serial, AnimationMode.RainbowBright)

# Simple static animation with custom colours and waterfall direction
# WaterfallDirection values: Down, Up, Off
await client.set_animation_mode(
    serial,
    AnimationMode.Simple,
    colour_one=Colour.BLUE,
    colour_two=Colour.CYAN,
    waterfall=WaterfallDirection.Down,
)

# Disable animation
await client.set_animation_mode(serial, AnimationMode.None_)
```
