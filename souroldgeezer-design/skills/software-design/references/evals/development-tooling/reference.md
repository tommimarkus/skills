# Lantern bench rules, revision 1

Original synthetic reference authored for this repository; no external rules copied.
Declared extraction scope: PULSE, DRAIN, RELAY. Energy is measured in sparks;
one pulse is one tick. Initial energy is zero.

## PULSE

Each pulse adds 2 sparks, to a maximum of 6 sparks. A damp pulse adds nothing.
The maximum applies after every pulse, including consecutive pulses.

## DRAIN

A drain removes 3 sparks, stopping at zero. It can follow a pulse in the same run.

## RELAY

A relay shares energy with a linked lamp. This revision leaves the order of
sharing and the recipient's cap unresolved. Do not choose an ordering implicitly.
