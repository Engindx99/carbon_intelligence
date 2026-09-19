"""Inverse solves: move a real operator handle until a real
process specification is met.

This is deliberately NOT physics/ (it moves no closure), NOT
reporter/ (it writes state) and NOT validators/ (it does not
check a balance). It is the layer that does to the fuel rate
what physics.gas_mass_balance already does to the excess-air
ratio: solves an input against an achieved quantity.
"""
