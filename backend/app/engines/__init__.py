"""Computation engines package.

Each engine is a pure function that turns validated input into a response
schema using an authoritative library. Engines perform no HTTP and no I/O so
they can be unit-tested in isolation.
"""
