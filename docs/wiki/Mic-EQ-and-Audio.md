# Mic, EQ & Audio

## Mic Settings

```python
from goxlrutil_api.protocol.types import MicrophoneType

# Set microphone type (affects input impedance and phantom power)
# MicrophoneType values: Dynamic, Condenser, Jack
await client.set_microphone_type(serial, MicrophoneType.Condenser)

# Set hardware gain (0–72 dB; only applies to the active mic type)
await client.set_microphone_gain(serial, MicrophoneType.Condenser, 36)
```

Read mic settings from state:

```python
mic = status.mixers[serial].mic_status
print(mic.mic_type)                       # MicrophoneType enum
print(mic.noise_gate.enabled)             # bool
print(mic.noise_gate.threshold)           # int (dB)
```

---

## Noise Gate

```python
from goxlrutil_api.protocol.types import GateTimes

# Enable/disable the noise gate
await client.set_gate_active(serial, True)

# Set the noise gate threshold (-59–0 dB; lower = more aggressive)
await client.set_gate_threshold(serial, -20)

# Gate detail parameters
await client.set_gate_attenuation(serial, 100)                # 0–100 %
await client.set_gate_attack(serial, GateTimes.Attack10ms)
await client.set_gate_release(serial, GateTimes.Attack100ms)
```

---

## EQ

The GoXLR Full has a 10-band parametric EQ; the GoXLR Mini has a 6-band EQ.

### Full EQ (10-band)

```python
from goxlrutil_api.protocol.types import EqFrequencies

# EqFrequencies values: Equalizer31Hz, Equalizer63Hz, Equalizer125Hz, Equalizer250Hz,
#   Equalizer500Hz, Equalizer1KHz, Equalizer2KHz, Equalizer4KHz, Equalizer8KHz, Equalizer16KHz

# Set gain for a band (-9..9 dB)
await client.set_eq_gain(serial, EqFrequencies.Equalizer1KHz, 3)

# Adjust the band center frequency
await client.set_eq_freq(serial, EqFrequencies.Equalizer1KHz, 1100.0)
```

### Mini EQ (6-band)

```python
from goxlrutil_api.protocol.types import MiniEqFrequencies

# MiniEqFrequencies values: Equalizer90Hz, Equalizer250Hz, Equalizer500Hz,
#   Equalizer1KHz, Equalizer3KHz, Equalizer8KHz

await client.set_eq_mini_gain(serial, MiniEqFrequencies.Equalizer1KHz, -2)
await client.set_eq_mini_freq(serial, MiniEqFrequencies.Equalizer1KHz, 950.0)
```

---

## Compressor

```python
from goxlrutil_api.protocol.types import (
    CompressorRatio, CompressorAttackTime, CompressorReleaseTime
)

await client.set_compressor_threshold(serial, -20)              # -40..0 dB
await client.set_compressor_ratio(serial, CompressorRatio.Ratio4to1)
await client.set_compressor_attack(serial, CompressorAttackTime.Attack10ms)
await client.set_compressor_release(serial, CompressorReleaseTime.Release100ms)
await client.set_compressor_makeup_gain(serial, 6)              # 0..24 dB
```

**CompressorRatio values:** `Ratio1to1`, `Ratio1_1to1`, `Ratio1_2to1`, `Ratio1_4to1`, `Ratio1_6to1`,
`Ratio1_8to1`, `Ratio2to1`, `Ratio2_5to1`, `Ratio3to1`, `Ratio3_5to1`, `Ratio4to1`, and more.

---

## De-esser

```python
await client.set_deeser(serial, 30)   # 0–100
```

---

## Monitor & VOD

```python
from goxlrutil_api.protocol.types import VodMode, OutputDevice

# Route the headphone monitor mix through effects
await client.set_monitor_with_fx(serial, True)

# Set the headphone monitor source (which output bus feeds the headphones)
await client.set_monitor_mix(serial, OutputDevice.BroadcastMix)

# VOD (streamer-safe) mode — silences music on stream while keeping it in headphones
# VodMode values: Routable, StreamNoMusic
await client.set_vod_mode(serial, VodMode.StreamNoMusic)

# Set the volume used to duck audio when the bleep/swear button is pressed (-34–0 dB)
await client.set_swear_button_volume(serial, -20)

# Percentage variant: 0 % = -34 dB (full duck), 100 % = 0 dB (no ducking)
await client.set_swear_button_volume_pct(serial, 50.0)  # ≈ -17 dB
```

---

## Submix

The submix system allows Mix A (headphones / direct monitor) and Mix B (stream / broadcast)
to have independent per-channel volumes.

```python
from goxlrutil_api.protocol.types import ChannelName, OutputDevice, Mix

# Enable the submix system
await client.set_submix_enabled(serial, True)

# Set the Mix B volume for a specific channel (0–255)
await client.set_submix_volume(serial, ChannelName.Music, 128)  # music at 50% on stream

# Link a channel's Mix B volume to its Mix A volume (they move together)
await client.set_submix_linked(serial, ChannelName.Music, True)

# Route an output to Mix A or Mix B
# Mix values: A, B
await client.set_submix_output_mix(serial, OutputDevice.BroadcastMix, Mix.B)
```

---

## Cough Button

```python
from goxlrutil_api.protocol.types import MuteFunction, MuteState

# Set the mute state of the cough button
await client.set_cough_mute_state(serial, MuteState.MutedToAll)

# Configure cough button behaviour
# MuteFunction values: All, ToStream, ToVoiceChat, ToPhones, ToLineOut
await client.set_cough_mute_function(serial, MuteFunction.ToStream)

# Hold mode: True = mute while button held, False = toggle on press
await client.set_cough_is_hold(serial, True)
```
