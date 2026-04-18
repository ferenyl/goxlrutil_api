# Sending Commands

## Profiles

```python
# List all available profiles
profiles = await client.list_profiles(serial)
print(profiles)  # ['Default', 'Streaming', 'Gaming', ...]

# Get the currently loaded profile name
current = await client.get_current_profile(serial)

# Load a profile
await client.load_profile(serial, "Gaming")

# Mic profiles work the same way
mic_profiles = await client.list_mic_profiles(serial)
current_mic = await client.get_current_mic_profile(serial)
await client.load_mic_profile(serial, "StudioMic")
```

---

## Volume

```python
from goxlrutil_api.protocol.types import ChannelName

# ChannelName values:
# Mic, LineIn, Console, System, Game, Chat, Sample, Music,
# Headphones, MicMonitor, LineOut

await client.set_volume(serial, ChannelName.Mic, 200)       # 0–255
await client.set_volume(serial, ChannelName.Game, 128)
await client.set_volume(serial, ChannelName.Headphones, 255)

# Percentage variant – maps 0–100 % to 0–255, clamped and rounded
await client.set_volume_pct(serial, ChannelName.Mic, 75.0)  # ≈ 191/255
```

---

## Fader Mute

```python
from goxlrutil_api.protocol.types import FaderName, MuteState

# FaderName values: A, B, C, D
# MuteState values: Unmuted, MutedToAll, MutedToX

await client.set_fader_mute_state(serial, FaderName.A, MuteState.MutedToAll)
await client.set_fader_mute_state(serial, FaderName.A, MuteState.Unmuted)
```

---

## Effects (FX)

```python
from goxlrutil_api.protocol.types import EffectBankPresets

# Global FX on/off
await client.set_fx_enabled(serial, True)
await client.set_fx_enabled(serial, False)

# Toggle (reads current state from cache, returns new bool)
is_on = await client.toggle_fx(serial)

# Switch active effect preset (Preset1 – Preset6)
await client.set_active_effect_preset(serial, EffectBankPresets.Preset1)

# Megaphone
await client.set_megaphone_enabled(serial, True)
enabled = await client.toggle_megaphone(serial)   # returns new bool

# Robot voice
await client.set_robot_enabled(serial, True)
enabled = await client.toggle_robot(serial)

# Hard Tune
await client.set_hard_tune_enabled(serial, True)
enabled = await client.toggle_hard_tune(serial)
```

`EffectBankPresets` values: `Preset1`, `Preset2`, `Preset3`, `Preset4`, `Preset5`, `Preset6`

> **Note:** Toggle methods read from the in-memory state cache.
> Call `await client.get_status()` at least once (or connect via WebSocket) before using them.

---

## Sampler

```python
from goxlrutil_api.protocol.types import SampleBank, SampleButtons

# Trigger playback of a sample in a specific bank + button slot
await client.play_sample(serial, SampleBank.A, SampleButtons.TopLeft)

# Stop playback for a slot
await client.stop_sample(serial, SampleBank.A, SampleButtons.TopLeft)
```

`SampleBank` values: `A`, `B`, `C`

`SampleButtons` values: `TopLeft`, `TopRight`, `BottomLeft`, `BottomRight`

---

## Raw Commands

Use `GoXLRCommand` directly for commands not covered by convenience helpers:

```python
from goxlrutil_api.protocol.commands import GoXLRCommand
from goxlrutil_api.protocol.types import FaderName, ChannelName, MuteFunction

# Assign a channel to a fader
await client.command(serial, GoXLRCommand.set_fader(FaderName.A, ChannelName.Mic))

# Set mute function for a fader
await client.command(serial, GoXLRCommand.set_fader_mute_function(FaderName.A, MuteFunction.All))
```
