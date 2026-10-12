"""Solid species hold-up in the rotary kiln, as a parcel train.

The kiln bed is plug flow at the solid velocity u_s:

    dc/dt + u_s dc/dz = r(c, T)

and its exact solution follows the characteristics. A parcel of
solid that entered at time t0 is at z = u_s (t - t0) and has
reacted along that path at the temperatures it met. The train
keeps every parcel now inside a zone: one per dt of inflow, so ~5
per cell at dt = 10 s (burning tau_cell ~50 s) and ~3.6 in the
transition (~36 s).

One dynamic step moves every parcel u_s dt downstream. A parcel
that crosses a face spends the first part of the step in one cell
and the rest in the next, and reacts in each at that cell's
temperature, for that long. Parcels past the outlet leave with the
time they still had in the step, and the next zone's train picks
them up there.

Why this operator. Transport is exact, with no numerical
diffusion: a feed change reaches the kiln outlet after the
transit time and not before. Mass is conserved by construction,
since a parcel's species change only through the reactions, whose
CO2 is booked to the cell where it is released. And at steady
state (constant inflow and temperatures) the parcel pattern
repeats every step shifted by one parcel. A cell's per-step
release is therefore exactly what one parcel releases over its
whole stay in the cell, which is what the steady flow march
computes per cell over tau = dz/u_s:

- calcination exactly, because exp(-k h1) exp(-k h2) = exp(-k tau);
- the clinkering reactions up to the Strang splitting error, since
  a parcel splits its stay in a cell into its step pieces where
  the march takes it whole.

The reactions are applied to the parcel's species MASSES [kg]
with the same functions the march applies to flows [kg/s]. Every
one is first order in an amount (or in the min of several), so
the operation scales and is the same.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class Parcel:
    """Solid that entered the zone during one step.

    x is the position in cells (cell i spans [i, i + 1)); species
    holds the masses [kg].
    """

    x: float
    species: dict


@dataclass
class TrainStep:
    """One step of a zone's train. Rates are per second of the
    step: W for heats, kg/s for masses; the hold-ups are masses
    [kg] at the start and the end of the step."""

    parcels: list
    leaving: list
    Q_cells: np.ndarray
    Q_calcination_cells: np.ndarray
    Q_calcination_slope_cells: np.ndarray
    dm_CO2_cells: np.ndarray
    face_flow: np.ndarray
    face_species: list
    holdup_old_cells: np.ndarray
    holdup_cells: np.ndarray
    clinkering_heat: dict
    dt: float

    @property
    def stored_cells(self):
        """Rate of change of each cell's solid hold-up [kg/s]."""
        return (self.holdup_cells - self.holdup_old_cells) / self.dt


def _mass(species):
    return float(sum(species.values()))


def advance_train(parcels, entering, T_cells, cells_per_second, dt, reactor):
    """Move the zone's parcels by one step of dt [s].

    parcels: the start-of-step train; it is not modified, so the
    same start can be re-stepped at each Picard iterate.
    entering: (species [kg], time [s]) pairs entering at x = 0
    during the step; time is how much of the step each has left.
    T_cells: solid temperature of each cell [K].
    cells_per_second: u_s / dz.
    reactor(T): returns the zone's reactions at T (see
    BurningReactor, CalcinationReactor).
    """

    N = len(T_cells)
    v = float(cells_per_second)

    if not (np.isfinite(v) and v > 0.0):
        raise ValueError(f"cells_per_second must be > 0, got {v}")

    reactors = [None] * N

    Q = np.zeros(N)
    Q_calc = np.zeros(N)
    slope = np.zeros(N)
    dm_CO2 = np.zeros(N)
    face = np.zeros(N + 1)
    face_species = [dict() for _ in range(N + 1)]

    def cross(k, species):
        face[k] += _mass(species)
        for name, value in species.items():
            face_species[k][name] = face_species[k].get(name, 0.0) + value

    inside = []
    leaving = []

    def travel(x, species, remaining):

        while remaining > 0.0:

            i = int(x)

            if i >= N:
                break

            if reactors[i] is None:
                reactors[i] = reactor(float(T_cells[i]))

            to_face = (i + 1.0 - x) / v
            crosses = to_face <= remaining
            h = to_face if crosses else remaining

            if h > 0.0:
                q, q_calc, dm = reactors[i].react(species, h)

                Q[i] += q
                Q_calc[i] += q_calc
                dm_CO2[i] += dm

            remaining -= h

            if crosses:
                x = i + 1.0
                cross(i + 1, species)
            else:
                x += h * v

        if int(x) >= N:
            leaving.append((species, max(remaining, 0.0)))
        else:
            inside.append(Parcel(x, species))

    holdup_old = np.zeros(N)

    for parcel in parcels:
        holdup_old[int(parcel.x)] += _mass(parcel.species)
        travel(parcel.x, dict(parcel.species), float(dt))

    for species, remaining in entering:
        cross(0, species)
        travel(0.0, dict(species), float(remaining))

    holdup = np.zeros(N)

    for parcel in inside:
        holdup[int(parcel.x)] += _mass(parcel.species)

    # dQ/dTs of the calcination heat, per cell. Only the source-term
    # linearisation (physics.variable_flow_rows) reads it, so it is
    # a path quantity: taken in the steady march's own form, on the
    # CaCO3 that entered the cell over the step and the cell's
    # residence 1/v, once per cell rather than per parcel piece.
    # At steady state it is the march's slope exactly.
    tau_cell = 1.0 / v

    for i, r in enumerate(reactors):
        if r is not None and face[i] > 0.0:
            slope[i] = r.slope(
                {
                    name: value / dt
                    for name, value in face_species[i].items()
                },
                tau_cell,
            ) * dt

    heat = {}

    for r in reactors:
        if r is not None:
            for model, value in r.heat.items():
                heat[model] = heat.get(model, 0.0) + value

    return TrainStep(
        parcels=inside,
        leaving=leaving,
        Q_cells=Q / dt,
        Q_calcination_cells=Q_calc / dt,
        Q_calcination_slope_cells=slope / dt,
        dm_CO2_cells=dm_CO2 / dt,
        face_flow=face / dt,
        face_species=[
            {name: value / dt for name, value in f.items()}
            for f in face_species
        ],
        holdup_old_cells=holdup_old,
        holdup_cells=holdup,
        clinkering_heat={model: value / dt for model, value in heat.items()},
        dt=float(dt),
    )


def steady_train(entering, T_cells, cells_per_second, dt, reactor):
    """The train's own steady state for this per-step inflow and
    these temperatures: the parcels that entered this step, those
    that entered one step earlier and have moved one dt further,
    and so on to the outlet. Stepping it with the same inflow and
    temperatures returns it, shifted by one parcel."""

    current = advance_train(
        [], entering, T_cells, cells_per_second, dt, reactor
    ).parcels

    train = list(current)

    while current:
        current = advance_train(
            current, [], T_cells, cells_per_second, dt, reactor
        ).parcels
        train.extend(current)

    return train


class BurningReactor:
    """The burning zone's reactions at one temperature: calcination
    and the four clinkering reactions (ChemistryModel.react_burning,
    the step the steady march takes)."""

    def __init__(self, chemistry, T):
        self.chemistry = chemistry
        self.T = T
        self.rate, self.rate_calcination = chemistry.burning_rates(T)
        self.heat = {
            chemistry.belite: 0.0,
            chemistry.alite: 0.0,
            chemistry.c3a: 0.0,
            chemistry.c4af: 0.0,
        }

    def react(self, species, h):
        return self.chemistry.react_burning(
            species,
            self.T,
            h,
            self.rate,
            self.rate_calcination,
            self.heat,
        )

    def slope(self, species, h):
        return self.chemistry.calcination.reaction_heat_slope(
            float(species["CaCO3"]), self.T, h
        )


class CalcinationReactor:
    """The transition's one reaction at one temperature: residual
    calcination of the meal (CalcinationModel)."""

    def __init__(self, calcination, T):
        self.calcination = calcination
        self.T = T
        self.rate = float(calcination.reaction_rate(T))
        self.heat = {}

    def react(self, species, h):
        q, dm = self.calcination.react_flow(species, self.T, h, self.rate)
        return q, q, dm

    def slope(self, species, h):
        return self.calcination.reaction_heat_slope(
            float(species["CaCO3"]), self.T, h
        )


class TransportReactor:
    """No reactions: a bed that is only carried, the grate cooler's
    clinker. The train then is a pure plug-flow delay with an exact
    hold-up."""

    heat = {}

    def __init__(self, T=None):
        pass

    def react(self, species, h):
        return 0.0, 0.0, 0.0

    def slope(self, species, h):
        return 0.0
