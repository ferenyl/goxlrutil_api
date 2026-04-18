"""GoXLRClient – high-level async API for the GoXLR Utility daemon."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from goxlrutil_api.colour import Colour, ColourLike, as_hex
from goxlrutil_api.events import ButtonEvent, ButtonEventType
from goxlrutil_api.exceptions import CommandError
from goxlrutil_api.protocol.commands import DaemonRequest, GoXLRCommand
from goxlrutil_api.protocol.responses import DaemonResponse, DaemonStatus
from goxlrutil_api.protocol.types import (
    AnimationMode,
    Button,
    ButtonColourGroups,
    ButtonColourOffStyle,
    ChannelName,
    EffectBankPresets,
    EncoderColourTargets,
    FaderDisplayStyle,
    FaderName,
    MuteState,
    SampleBank,
    SampleButtons,
    SamplerColourTargets,
    SimpleColourTargets,
    WaterfallDirection,
)
from goxlrutil_api.state import DaemonState
from goxlrutil_api.transport.base import Transport

_log = logging.getLogger(__name__)

PatchListener = Callable[[DaemonStatus], Awaitable[None]]
ButtonListener = Callable[[ButtonEvent], Awaitable[None]]


class GoXLRClient:
    """
    Async client for the GoXLR Utility daemon.

    Usage::

        async with GoXLRClient(transport) as client:
            status = await client.get_status()
            serial = next(iter(status.mixers))
            await client.set_volume(serial, ChannelName.Mic, 200)

    To receive live state updates (requires WebSocketTransport)::

        async def on_update(status: DaemonStatus) -> None:
            print(status.mixers)

        async with GoXLRClient(transport, on_state_update=on_update) as client:
            ...

    To receive button press / release / long-press events (requires WebSocketTransport)::

        async def on_button(event: ButtonEvent) -> None:
            print(event.button, event.event_type, event.held_seconds)

        async with GoXLRClient(transport, on_button_event=on_button) as client:
            ...
    """

    def __init__(
        self,
        transport: Transport,
        on_state_update: PatchListener | None = None,
        on_button_event: ButtonListener | None = None,
        long_press_threshold: float = 0.5,
    ) -> None:
        self._transport = transport
        self._state = DaemonState()
        self._on_state_update = on_state_update
        self._on_button_event_cb = on_button_event
        self._long_press_threshold = long_press_threshold
        # {serial: {button_name: monotonic press time}}
        self._button_press_times: dict[str, dict[str, float]] = {}
        # {serial: {button_name: pending long-press Task}}
        self._long_press_tasks: dict[str, dict[str, asyncio.Task[None]]] = {}

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> GoXLRClient:
        await self._transport.connect()
        await self._transport.subscribe(self._on_patch)
        return self

    async def __aexit__(self, *_: object) -> None:
        self._cancel_all_long_press_tasks()
        await self._transport.disconnect()

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """Return True if the daemon responds to a ping."""
        resp = await self._transport.send(DaemonRequest.ping())
        return resp.ok

    async def get_status(self) -> DaemonStatus:
        """Fetch full daemon status and update internal state cache."""
        resp = await self._send_checked(DaemonRequest.get_status())
        if resp.raw_status is not None:
            self._state.set_raw(resp.raw_status)
        return self._state.status

    async def get_mic_level(self, serial: str) -> float:
        """Return the current microphone level (0.0–1.0) for the given mixer."""
        resp = await self._send_checked(DaemonRequest.get_mic_level(serial))
        if resp.mic_level is None:
            return 0.0
        return resp.mic_level

    async def command(self, serial: str, cmd: GoXLRCommand) -> None:
        """Send a GoXLR command to a specific mixer."""
        await self._send_checked(DaemonRequest.command(serial, cmd))

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    async def set_volume(self, serial: str, channel: ChannelName, volume: int) -> None:
        """Set channel volume (0–255)."""
        await self.command(serial, GoXLRCommand.set_volume(channel, volume))

    async def set_fader_mute_state(self, serial: str, fader: FaderName, state: MuteState) -> None:
        await self.command(serial, GoXLRCommand.set_fader_mute_state(fader, state))

    async def set_fx_enabled(self, serial: str, enabled: bool) -> None:
        """Enable or disable all effects."""
        await self.command(serial, GoXLRCommand.set_fx_enabled(enabled))

    async def toggle_fx(self, serial: str) -> bool:
        """Toggle FX on/off. Reads fresh state, returns the new enabled state."""
        status = await self.get_status()
        mixer = status.mixers.get(serial)
        current = mixer.effects.is_enabled if mixer and mixer.effects else False
        new_state = not current
        await self.set_fx_enabled(serial, new_state)
        return new_state

    # ------------------------------------------------------------------
    # Effects – presets
    # ------------------------------------------------------------------

    async def set_active_effect_preset(
        self, serial: str, preset: EffectBankPresets
    ) -> None:
        """Switch the active effect bank preset (Preset1–Preset6)."""
        await self.command(serial, GoXLRCommand.set_active_effect_preset(preset))

    # ------------------------------------------------------------------
    # Effects – individual voices
    # ------------------------------------------------------------------

    async def set_megaphone_enabled(self, serial: str, enabled: bool) -> None:
        """Enable or disable the Megaphone voice effect."""
        await self.command(serial, GoXLRCommand.set_megaphone_enabled(enabled))

    async def toggle_megaphone(self, serial: str) -> bool:
        """Toggle Megaphone on/off. Reads fresh state, returns the new enabled state."""
        status = await self.get_status()
        mixer = status.mixers.get(serial)
        current = (
            mixer.effects.current.megaphone.is_enabled
            if mixer and mixer.effects
            else False
        )
        new_state = not current
        await self.set_megaphone_enabled(serial, new_state)
        return new_state

    async def set_robot_enabled(self, serial: str, enabled: bool) -> None:
        """Enable or disable the Robot voice effect."""
        await self.command(serial, GoXLRCommand.set_robot_enabled(enabled))

    async def toggle_robot(self, serial: str) -> bool:
        """Toggle Robot on/off. Reads fresh state, returns the new enabled state."""
        status = await self.get_status()
        mixer = status.mixers.get(serial)
        current = (
            mixer.effects.current.robot.is_enabled
            if mixer and mixer.effects
            else False
        )
        new_state = not current
        await self.set_robot_enabled(serial, new_state)
        return new_state

    async def set_hard_tune_enabled(self, serial: str, enabled: bool) -> None:
        """Enable or disable the Hard Tune voice effect."""
        await self.command(serial, GoXLRCommand.set_hard_tune_enabled(enabled))

    async def toggle_hard_tune(self, serial: str) -> bool:
        """Toggle Hard Tune on/off. Reads fresh state, returns the new enabled state."""
        status = await self.get_status()
        mixer = status.mixers.get(serial)
        current = (
            mixer.effects.current.hard_tune.is_enabled
            if mixer and mixer.effects
            else False
        )
        new_state = not current
        await self.set_hard_tune_enabled(serial, new_state)
        return new_state

    # ------------------------------------------------------------------
    # Sampler
    # ------------------------------------------------------------------

    async def play_sample(
        self, serial: str, bank: SampleBank, button: SampleButtons
    ) -> None:
        """Trigger playback of the sample assigned to a bank+button slot."""
        await self.command(serial, GoXLRCommand.play_next_sample(bank, button))

    async def stop_sample(
        self, serial: str, bank: SampleBank, button: SampleButtons
    ) -> None:
        """Stop playback for the given bank+button slot."""
        await self.command(serial, GoXLRCommand.stop_sample_playback(bank, button))

    # ------------------------------------------------------------------
    # Lighting / colour helpers
    # ------------------------------------------------------------------

    async def set_button_colour(
        self,
        serial: str,
        button: Button,
        colour_on: ColourLike,
        colour_off: ColourLike | None = None,
    ) -> None:
        """Set the active (and optionally inactive) LED colour for a button.

        ``colour_off`` defaults to a dimmed version of ``colour_on`` when
        omitted.
        """
        on_hex = as_hex(colour_on)
        off_hex = (
            as_hex(colour_off) if colour_off is not None
            else str(Colour.from_hex(on_hex).dimmed())
        )
        await self.command(serial, GoXLRCommand.set_button_colours(button, on_hex, off_hex))

    async def set_button_off_style(
        self,
        serial: str,
        button: Button,
        off_style: ButtonColourOffStyle,
        colour_two: ColourLike = Colour.BLACK,
    ) -> None:
        """Set how a button appears when it is in the 'off' state."""
        await self.command(
            serial,
            GoXLRCommand.set_button_off_style(button, off_style, as_hex(colour_two)),
        )

    async def set_button_group_colour(
        self,
        serial: str,
        group: ButtonColourGroups,
        colour_one: ColourLike,
        colour_two: ColourLike,
    ) -> None:
        """Set LED colours for all buttons in a named group simultaneously."""
        await self.command(
            serial,
            GoXLRCommand.set_button_group_colours(group, as_hex(colour_one), as_hex(colour_two)),
        )

    async def set_fader_colour(
        self,
        serial: str,
        fader: FaderName,
        colour_top: ColourLike,
        colour_bottom: ColourLike,
    ) -> None:
        """Set the two LED colours for a fader channel strip."""
        await self.command(
            serial,
            GoXLRCommand.set_fader_colours(fader, as_hex(colour_top), as_hex(colour_bottom)),
        )

    async def set_fader_display_style(
        self,
        serial: str,
        fader: FaderName,
        style: FaderDisplayStyle,
    ) -> None:
        """Set the display style (gradient, meter, etc.) for a fader."""
        await self.command(serial, GoXLRCommand.set_fader_display_style(fader, style))

    async def set_all_fader_display_style(
        self, serial: str, style: FaderDisplayStyle
    ) -> None:
        """Apply the same display style to all four faders."""
        await self.command(serial, GoXLRCommand.set_all_fader_display_style(style))

    async def set_global_colour(self, serial: str, colour: ColourLike) -> None:
        """Set the global accent colour used by animations and unassigned LEDs."""
        await self.command(serial, GoXLRCommand.set_global_colour(as_hex(colour)))

    async def set_simple_colour(
        self, serial: str, target: SimpleColourTargets, colour: ColourLike
    ) -> None:
        """Set the colour for a simple single-colour target (Global, Accent, ScribbleBack)."""
        await self.command(serial, GoXLRCommand.set_simple_colour(target, as_hex(colour)))

    async def set_encoder_colour(
        self,
        serial: str,
        target: EncoderColourTargets,
        colour_left: ColourLike,
        colour_right: ColourLike,
        colour_knob: ColourLike,
    ) -> None:
        """Set the three LED zones of an encoder (left arc, right arc, knob)."""
        await self.command(
            serial,
            GoXLRCommand.set_encoder_colour(
                target, as_hex(colour_left), as_hex(colour_right), as_hex(colour_knob)
            ),
        )

    async def set_sampler_colour(
        self,
        serial: str,
        target: SamplerColourTargets,
        colour_one: ColourLike,
        colour_two: ColourLike,
        colour_three: ColourLike,
    ) -> None:
        """Set the three LED states for a sampler bank selector button."""
        await self.command(
            serial,
            GoXLRCommand.set_sampler_colour(
                target,
                as_hex(colour_one),
                as_hex(colour_two),
                as_hex(colour_three),
            ),
        )

    async def set_animation_mode(
        self,
        serial: str,
        mode: AnimationMode,
        colour_one: ColourLike = Colour.BLACK,
        colour_two: ColourLike = Colour.BLACK,
        waterfall: WaterfallDirection = WaterfallDirection.Down,
    ) -> None:
        """Set the global LED animation mode and parameters."""
        await self.command(
            serial,
            GoXLRCommand.set_animation_mode(
                mode, as_hex(colour_one), as_hex(colour_two), waterfall
            ),
        )

    # ------------------------------------------------------------------
    # State access
    # ------------------------------------------------------------------

    @property
    def state(self) -> DaemonState:
        """Access the cached daemon state directly."""
        return self._state

    # ------------------------------------------------------------------
    # Internal: patch handling
    # ------------------------------------------------------------------

    async def _send_checked(self, request: DaemonRequest) -> DaemonResponse:
        resp = await self._transport.send(request)
        if resp.error is not None:
            raise CommandError(resp.error)
        return resp

    async def _on_patch(self, ops: list[Any]) -> None:
        """Called by the transport when a live Patch event arrives."""
        # Snapshot button states before applying patch so we can diff them.
        old_button_down = {
            serial: dict(mixer.button_down)
            for serial, mixer in self._state.status.mixers.items()
        }

        self._state.apply_patch(ops)

        if self._on_state_update is not None:
            try:
                await self._on_state_update(self._state.status)
            except Exception as exc:
                _log.warning("on_state_update callback raised: %s", exc)

        if self._on_button_event_cb is not None:
            await self._handle_button_changes(old_button_down)

    # ------------------------------------------------------------------
    # Internal: button event detection
    # ------------------------------------------------------------------

    async def _handle_button_changes(
        self, old_bd: dict[str, dict[str, bool]]
    ) -> None:
        now = asyncio.get_running_loop().time()
        for serial, mixer in self._state.status.mixers.items():
            serial_times = self._button_press_times.setdefault(serial, {})
            serial_tasks = self._long_press_tasks.setdefault(serial, {})
            old = old_bd.get(serial, {})
            for btn_name, is_down in mixer.button_down.items():
                was_down = old.get(btn_name, False)
                if is_down and not was_down:
                    serial_times[btn_name] = now
                    serial_tasks[btn_name] = asyncio.create_task(
                        self._long_press_timer(serial, btn_name, now),
                        name=f"goxlr-longpress-{serial}-{btn_name}",
                    )
                    await self._fire_button_event(
                        serial, btn_name, ButtonEventType.pressed, 0.0
                    )
                elif not is_down and was_down:
                    if task := serial_tasks.pop(btn_name, None):
                        task.cancel()
                    held = now - serial_times.pop(btn_name, now)
                    await self._fire_button_event(
                        serial, btn_name, ButtonEventType.released, held
                    )

    async def _long_press_timer(
        self, serial: str, btn_name: str, press_time: float
    ) -> None:
        """Wait for long_press_threshold, then fire a long_pressed event if still held."""
        try:
            await asyncio.sleep(self._long_press_threshold)
        except asyncio.CancelledError:
            return
        mixer = self._state.status.mixers.get(serial)
        if mixer and mixer.button_down.get(btn_name, False):
            held = asyncio.get_running_loop().time() - press_time
            await self._fire_button_event(serial, btn_name, ButtonEventType.long_pressed, held)

    async def _fire_button_event(
        self,
        serial: str,
        btn_name: str,
        event_type: ButtonEventType,
        held_seconds: float,
    ) -> None:
        if self._on_button_event_cb is None:
            return
        event = ButtonEvent.from_raw(serial, btn_name, event_type, held_seconds)
        try:
            await self._on_button_event_cb(event)
        except Exception as exc:
            _log.warning("on_button_event callback raised: %s", exc)

    def _cancel_all_long_press_tasks(self) -> None:
        for serial_tasks in self._long_press_tasks.values():
            for task in serial_tasks.values():
                task.cancel()
        self._long_press_tasks.clear()
        self._button_press_times.clear()

