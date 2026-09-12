"""Feedback-driven discovery planning for two separated coarse objects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiscoveryConfig:
    x_min_mm: float = 65.0
    x_max_mm: float = 145.0
    discovery_y_mm: float = 105.0
    coarse_pitch_mm: float = 5.0
    edge_refinement_pitch_mm: float = 1.0
    minimum_contact_samples: int = 2

    def coarse_x_positions(self) -> tuple[float, ...]:
        count = round((self.x_max_mm - self.x_min_mm) / self.coarse_pitch_mm)
        return tuple(
            self.x_min_mm + index * self.coarse_pitch_mm
            for index in range(count + 1)
        )


@dataclass(frozen=True)
class DiscoverySample:
    x_mm: float
    contact: bool
    trigger_z_mm: float | None = None


@dataclass(frozen=True)
class ContactComponent:
    first_contact_x_mm: float
    last_contact_x_mm: float
    estimated_center_x_mm: float
    sampled_width_mm: float
    contact_count: int


def contact_components(
    samples: list[DiscoverySample],
    config: DiscoveryConfig | None = None,
) -> tuple[ContactComponent, ...]:
    config = config or DiscoveryConfig()
    ordered = sorted(samples, key=lambda sample: sample.x_mm)
    groups: list[list[DiscoverySample]] = []
    current: list[DiscoverySample] = []
    for sample in ordered:
        if sample.contact:
            if current and sample.x_mm - current[-1].x_mm > config.coarse_pitch_mm * 1.5:
                groups.append(current)
                current = []
            current.append(sample)
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)

    return tuple(
        ContactComponent(
            first_contact_x_mm=group[0].x_mm,
            last_contact_x_mm=group[-1].x_mm,
            estimated_center_x_mm=(group[0].x_mm + group[-1].x_mm) / 2.0,
            sampled_width_mm=group[-1].x_mm - group[0].x_mm,
            contact_count=len(group),
        )
        for group in groups
        if len(group) >= config.minimum_contact_samples
    )


def refinement_x_positions(
    samples: list[DiscoverySample],
    config: DiscoveryConfig | None = None,
) -> tuple[float, ...]:
    """Return unmeasured 1 mm locations around measured contact transitions."""
    config = config or DiscoveryConfig()
    ordered = sorted(samples, key=lambda sample: sample.x_mm)
    measured = {round(sample.x_mm, 6) for sample in ordered}
    candidates: set[float] = set()
    for left, right in zip(ordered, ordered[1:]):
        if left.contact == right.contact:
            continue
        value = left.x_mm + config.edge_refinement_pitch_mm
        while value < right.x_mm - 1e-9:
            if round(value, 6) not in measured:
                candidates.add(round(value, 3))
            value += config.edge_refinement_pitch_mm
    return tuple(sorted(candidates))
