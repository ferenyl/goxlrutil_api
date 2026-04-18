# Fader Assignment & Routing

## Assigning Channels to Faders

```python
from goxlrutil_api.protocol.types import FaderName, ChannelName, MuteFunction, MuteState

# Assign the Mic channel to fader A
await client.set_fader(serial, FaderName.A, ChannelName.Mic)

# Change how the fader A mute button behaves
# MuteFunction values: All, ToStream, ToVoiceChat, ToPhones, ToLineOut
await client.set_fader_mute_function(serial, FaderName.A, MuteFunction.All)

# Set mute state directly
# MuteState values: Unmuted, MutedToAll, MutedToX
await client.set_fader_mute_state(serial, FaderName.A, MuteState.MutedToAll)
```

**FaderName values:** `A`, `B`, `C`, `D`

**ChannelName values:** `Mic`, `LineIn`, `Console`, `System`, `Game`, `Chat`, `Sample`, `Music`, `Headphones`, `MicMonitor`, `LineOut`

---

## Routing Matrix

The routing matrix controls which input signals are routed to which output buses.

```python
from goxlrutil_api.protocol.types import InputDevice, OutputDevice

# Enable Mic → BroadcastMix cross-point
await client.set_router(serial, InputDevice.Microphone, OutputDevice.BroadcastMix, True)

# Disable Chat → Headphones cross-point
await client.set_router(serial, InputDevice.Chat, OutputDevice.Headphones, False)
```

**InputDevice values:** `Microphone`, `Chat`, `Music`, `Game`, `Console`, `LineIn`, `System`, `Samples`

**OutputDevice values:** `Headphones`, `BroadcastMix`, `LineOut`, `ChatMic`, `Sampler`
