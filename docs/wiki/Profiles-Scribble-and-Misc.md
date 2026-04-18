# Profiles, Scribble & Misc

## Profiles

```python
# List and load profiles
profiles = await client.list_profiles(serial)
await client.load_profile(serial, "Gaming")
await client.load_mic_profile(serial, "StudioMic")

# Persist current settings
await client.save_profile(serial)

# Save as a new profile
await client.save_profile_as(serial, "MyNewProfile")

# Save mic settings (to active mic profile or as new)
await client.save_mic_profile(serial)
await client.save_mic_profile_as(serial, "NewMicProfile")

# Import only the colour settings from another profile
await client.load_profile_colours(serial, "ColoursOnly")

# Rename the active effect preset slot
await client.rename_active_preset(serial, "BrightStar")
```

---

## Scribble Strips

The GoXLR Full has small OLED displays above each fader.

```python
from goxlrutil_api.protocol.types import FaderName

# Set the display text (up to 8 characters)
await client.set_scribble_text(serial, FaderName.A, "MIC")

# Set a number label (shown below the text)
await client.set_scribble_number(serial, FaderName.A, "1")

# Set an icon by name (None clears the icon)
await client.set_scribble_icon(serial, FaderName.A, "mic.png")
await client.set_scribble_icon(serial, FaderName.A, None)   # clear

# Invert the display colours
await client.set_scribble_invert(serial, FaderName.A, True)
```

---

## Misc Settings

```python
from goxlrutil_api.protocol.types import DisplayModeComponents, DisplayMode

# Lock all faders to their current positions
await client.set_lock_faders(serial, True)

# When VC is muted, also mute the Chat Mic channel
await client.set_vc_mute_also_mute_cm(serial, True)

# How long a fader button must be held to trigger a mute-hold (ms)
await client.set_mute_hold_duration(serial, 500)

# Change the display mode for a UI component
# DisplayModeComponents values: Equaliser, NoiseGate, Compressor
# DisplayMode values: Simple, Advanced
await client.set_element_display_mode(
    serial, DisplayModeComponents.Equaliser, DisplayMode.Advanced
)
```
