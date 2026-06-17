from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AxisLimit:
    name: str
    spm_safe_min: float
    spm_safe_max: float
    firmware_min: float
    firmware_max: float
    unit: str = "mm"

    def spm_hint(self) -> str:
        return f"SPM safe {self.spm_safe_min:g}..{self.spm_safe_max:g} {self.unit}"

    def firmware_hint(self) -> str:
        return f"MK4S soft {self.firmware_min:g}..{self.firmware_max:g} {self.unit}"


@dataclass(frozen=True)
class SPMHardwareProfile:
    x: AxisLimit
    y: AxisLimit
    z: AxisLimit
    recommended_resolution: str
    resolution_tip: str
    scan_tuning_tip: str
    official_build_volume: str = "250 x 210 x 220 mm"
    manual_source: str = "Prusa MK4S handbook v1.01, Product Information"

    @classmethod
    def from_config(cls, config: dict) -> "SPMHardwareProfile":
        limits = config["motion_limits"]
        safe_limits = config.get("spm_safe_limits", limits)
        return cls(
            x=AxisLimit("X", safe_limits["x"][0], safe_limits["x"][1], limits["x"][0], limits["x"][1]),
            y=AxisLimit("Y", safe_limits["y"][0], safe_limits["y"][1], limits["y"][0], limits["y"][1]),
            z=AxisLimit("Z", safe_limits["z"][0], safe_limits["z"][1], limits["z"][0], limits["z"][1]),
            recommended_resolution="5 x 5 safe demo; 9 x 9 for careful development",
            resolution_tip=(
                "Higher resolution means more MK4S moves. Start 5 x 5, then 9 x 9, "
                "and only increase after the probe/sample clearance is proven."
            ),
            scan_tuning_tip=(
                "Machine limits now follow the original MK4S build volume. "
                "For SPM work, keep routine scans near 46..54 mm and Z near 20 mm until the probe is mounted."
            ),
        )

    def axis_hint(self, axis: str) -> str:
        axis_limit = getattr(self, axis.lower())
        return f"{axis_limit.spm_hint()} | {axis_limit.firmware_hint()}"

    def compact_axis_range(self, axis: str) -> str:
        axis_limit = getattr(self, axis.lower())
        return f"{axis_limit.firmware_min:g}-{axis_limit.firmware_max:g}"

    def compact_resolution_range(self) -> str:
        return "3-250; start 3/5"

    def scan_mode_limits_text(self, mode: str) -> str:
        return (
            f"Scan mode: {mode}\n\n"
            f"Official MK4S build volume: {self.official_build_volume}\n"
            f"Source: {self.manual_source}\n"
            "Official maxima tested: X250, Y210, Z220\n"
            "Official X/Y minima tested: X0, Y0\n"
            "Z0 is not auto-tested because it is collision-sensitive.\n\n"
            "Current machine numeric limits:\n"
            f"X min {self.x.firmware_min:g} / max {self.x.firmware_max:g}\n"
            f"Y min {self.y.firmware_min:g} / max {self.y.firmware_max:g}\n"
            f"Z min {self.z.firmware_min:g} / max {self.z.firmware_max:g}\n"
            f"Resolution: {self.compact_resolution_range()}\n\n"
            "Recommended SPM-safe routine range:\n"
            f"X min {self.x.spm_safe_min:g} / max {self.x.spm_safe_max:g}\n"
            f"Y min {self.y.spm_safe_min:g} / max {self.y.spm_safe_max:g}\n"
            f"Z min {self.z.spm_safe_min:g} / max {self.z.spm_safe_max:g}"
        )

    def summary(self) -> str:
        return (
            "Hardware tuning: "
            f"Official MK4S build volume {self.official_build_volume}; "
            f"machine X {self.x.firmware_min:g}..{self.x.firmware_max:g}, "
            f"Y {self.y.firmware_min:g}..{self.y.firmware_max:g}, "
            f"Z {self.z.firmware_min:g}..{self.z.firmware_max:g}. "
            f"{self.scan_tuning_tip}"
        )
