# Effects & Sampler

See [Sending Commands](Sending-Commands) for toggling effects on/off and switching presets.
This page covers the fine-grained effect parameters.

---

## Reading Effect State

```python
status = await client.get_status()
mixer = status.mixers[serial]
reverb = mixer.effects.current.reverb     # Reverb dataclass
print(reverb.style, reverb.amount)
```

---

## Reverb

```python
from goxlrutil_api.protocol.types import ReverbStyle

# ReverbStyle values: Library, DarkBloom, MusicClub, RealPlate, Chapel, HockeyArena
await client.set_reverb_style(serial, ReverbStyle.HockeyArena)
await client.set_reverb_amount(serial, 40)          # 0–100

# Fine parameters
await client.set_reverb_decay(serial, 800)          # ms
await client.set_reverb_early_level(serial, -6)     # dB
await client.set_reverb_tail_level(serial, -10)     # dB
await client.set_reverb_pre_delay(serial, 20)       # ms
await client.set_reverb_low_colour(serial, 50)
await client.set_reverb_high_colour(serial, 50)
await client.set_reverb_high_factor(serial, 50)
await client.set_reverb_diffuse(serial, 75)
await client.set_reverb_mod_speed(serial, 40)
await client.set_reverb_mod_depth(serial, 20)
```

---

## Echo

```python
from goxlrutil_api.protocol.types import EchoStyle

# EchoStyle values: Quarter, Eighth, Multihead, Studio, ClassicSlap
await client.set_echo_style(serial, EchoStyle.Studio)
await client.set_echo_amount(serial, 25)            # 0–100

# Fine parameters
await client.set_echo_feedback(serial, 50)          # 0–100
await client.set_echo_tempo(serial, 120)            # BPM
await client.set_echo_delay_left(serial, 300)       # ms
await client.set_echo_delay_right(serial, 300)      # ms
await client.set_echo_feedback_left(serial, 50)     # 0–100
await client.set_echo_feedback_right(serial, 50)    # 0–100
await client.set_echo_xfb_l_to_r(serial, 0)        # 0–100
await client.set_echo_xfb_r_to_l(serial, 0)        # 0–100
```

---

## Pitch

```python
from goxlrutil_api.protocol.types import PitchStyle

# Without HardTune: -24–24 (Wide) or same range for Narrow
# With HardTune enabled: -2–2 (Wide) or -1–1 (Narrow)
await client.set_pitch_style(serial, PitchStyle.Wide)
await client.set_pitch_amount(serial, -12)
await client.set_pitch_character(serial, 50)        # 0–100
```

---

## Gender

```python
from goxlrutil_api.protocol.types import GenderStyle

# GenderStyle values: Narrow, Medium, Wide
# Narrow: -12–12  |  Wide: -50–50
await client.set_gender_style(serial, GenderStyle.Medium)
await client.set_gender_amount(serial, 6)
```

---

## Megaphone

```python
from goxlrutil_api.protocol.types import MegaphoneStyle

# MegaphoneStyle values: Megaphone, Radio, OnThePhone, Overdrive, BuzzCutt, Tweed
await client.set_megaphone_style(serial, MegaphoneStyle.Radio)
await client.set_megaphone_amount(serial, 75)       # 0–100
await client.set_megaphone_post_gain(serial, 3)     # -20..20 dB
```

---

## Robot

```python
from goxlrutil_api.protocol.types import RobotStyle, RobotRange

# RobotStyle values: Robot1, Robot2, Robot3
await client.set_robot_style(serial, RobotStyle.Robot1)

# RobotRange values: Low, Medium, High
await client.set_robot_gain(serial, RobotRange.Low, 0)
await client.set_robot_freq(serial, RobotRange.Low, 80)
await client.set_robot_width(serial, RobotRange.Low, 45)
await client.set_robot_waveform(serial, 0)          # 0–5
await client.set_robot_pulse_width(serial, 50)      # 0–100
await client.set_robot_threshold(serial, -36)
await client.set_robot_dry_mix(serial, 0)
```

---

## HardTune

```python
from goxlrutil_api.protocol.types import HardTuneStyle, HardTuneSource

# HardTuneStyle values: Natural, Medium, Hard
await client.set_hard_tune_style(serial, HardTuneStyle.Hard)
await client.set_hard_tune_amount(serial, 100)      # 0–100
await client.set_hard_tune_rate(serial, 50)         # 0–100
await client.set_hard_tune_window(serial, 20)       # ms

# HardTuneSource values: All, Music, Game, LineIn, System
await client.set_hard_tune_source(serial, HardTuneSource.Music)
```

---

## Sampler Management

```python
from goxlrutil_api.protocol.types import SampleBank, SampleButtons, SamplePlaybackMode, SamplePlayOrder

# Add an audio file to a sampler slot (path on the daemon host)
await client.add_sample(serial, SampleBank.A, SampleButtons.TopLeft, "/home/user/sounds/fx.wav")

# Remove a sample by its index in the slot's list
await client.remove_sample_by_index(serial, SampleBank.A, SampleButtons.TopLeft, 0)

# Trim the in/out points of a sample (0.0–1.0 as fraction of file length)
await client.set_sample_start_percent(serial, SampleBank.A, SampleButtons.TopLeft, 0, 0.1)
await client.set_sample_stop_percent(serial, SampleBank.A, SampleButtons.TopLeft, 0, 0.9)

# Set the playback mode for a slot
# SamplePlaybackMode values: PlayNext, StopOnEnd, Loop, SingleLoop, OncePerPress
await client.set_sampler_function(
    serial, SampleBank.A, SampleButtons.TopLeft, SamplePlaybackMode.Loop
)

# Set the order in which samples in a slot are played
# SamplePlayOrder values: Sequential, Random
await client.set_sampler_order(
    serial, SampleBank.A, SampleButtons.TopLeft, SamplePlayOrder.Sequential
)

# Global sampler settings
await client.set_sampler_fade_duration(serial, 200)    # fade-out ms
await client.set_sampler_reset_on_clear(serial, True)  # rewind on stop
```
