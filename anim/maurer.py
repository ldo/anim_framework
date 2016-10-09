#+
# Animations of Maurer rose patterns.
# For background, see Peter M Maurer, “A Rose is a Rose...”
# <http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.97.8141&rep=rep1&type=pdf>.
#
# Copyright 2016 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under CC-BY-SA <http://creativecommons.org/licenses/by-sa/4.0/>.
#-

import math
from fractions import \
    gcd
import qahirah as qah
from . import \
    common

def draw(g, amplitude, delta, mod, freq, offset, phase, start = 0, end = 1) :
    "draws a Maurer rose into the qahirah.Context g. amplitude is the amplitude" \
    " of the sine wave, delta the number of steps between successive curve points" \
    " (the “d” parameter from the Maurer paper), mod the modulus (total number of" \
    " steps around curve) (the “z” parameter from the Maurer paper), freq the" \
    " “n” parameter from the Maurer paper, offset the offset of the curve from" \
    " the centre, and phase the phase angle for rotating the whole curve."

    k = gcd(delta, mod) # number of points per subcurve

    def subcurve_func(n) :
        return \
            n // mod // k
    #end subcurve_func

    def curve_func(n) :
        subcurve = n // mod // k
        step = n * delta % mod
        phi = qah.circle * (step + subcurve) / mod
        theta = qah.circle * ((step + subcurve) * freq / mod + phase)
        r = offset + math.sin(theta) * amplitude
        return \
            qah.Vector(r * math.cos(phi), r * math.sin(phi))
    #end curve_func

    common.draw_curve_discrete \
      (
        g = g,
        f = curve_func,
        closed = True,
        nr_steps = mod,
        start = start,
        end = end,
        subcurve = subcurve_func
      )
#end draw

def make_draw(amplitude, delta, mod, freq, offset, phase, start = 0, end = 1) :
    "returns a draw procedure which will draw a Maurer rose with the specified animatable" \
    " parameters."
    amplitude = common.ensure_interpolator(amplitude)
    delta = common.ensure_interpolator(delta)
    mod = common.ensure_interpolator(mod)
    freq = common.ensure_interpolator(freq)
    offset = common.ensure_interpolator(offset)
    phase = common.ensure_interpolator(phase)
    start = common.ensure_interpolator(start)
    end = common.ensure_interpolator(end)

    def apply_draw(g, x) :
        "draws a Maurer rose into the qahirah.Context g with the animated settings" \
        " appropriate to time x."
        # note delta, mod and freq must be integers
        draw \
          (
            g = g,
            amplitude = amplitude(x),
            delta = round(delta(x)),
            mod = round(mod(x)),
            freq = round(freq(x)),
            offset = offset(x),
            phase = phase(x),
            start = start(x),
            end = end(x)
          )
    #end apply_draw

    return \
        apply_draw
#end make_draw
