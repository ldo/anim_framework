#+
# Animations of rose curves.
# For background on the maths, see <https://en.wikipedia.org/wiki/Rose_curve>.
#
# Copyright 2014 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under CC-BY-SA <http://creativecommons.org/licenses/by-sa/4.0/>.
#-

import math
from . import \
    common

def draw(g, amplitude, freq, offset, phase, nr_steps, start = 0, end = 1) :
    # note freq must be a Fraction

    def curve_func(x) :
        # Note that the curve can still be traced twice in some situations, namely where
        # the frequency numerator and denominator are both odd, and the offset is zero.
        # But if the offset is set to nonzero, the two halves no longer overlap.
        phi = 2 * math.pi * x * freq.denominator
        theta = 2 * math.pi * (x + phase) * freq.numerator
        r = offset + math.sin(theta) * amplitude
        return \
            (r * math.cos(phi), r * math.sin(phi))
    #end curve_func

    common.draw_curve(g, f = curve_func, closed = True, nr_steps = nr_steps, start = start, end = end)
#end draw

def make_draw(amplitude, freq, offset, phase, nr_steps, start = 0, end = 1) :
    # note freq must be a Fraction
    offset = common.ensure_interpolator(offset)
    amplitude = common.ensure_interpolator(amplitude)
    freq = common.ensure_interpolator(freq)
    phase = common.ensure_interpolator(phase)
    nr_steps = common.ensure_interpolator(nr_steps)
    start = common.ensure_interpolator(start)
    end = common.ensure_interpolator(end)

    def apply_draw(g, x) :
        # note nr_steps must be integer
        draw \
          (
            g = g,
            offset = offset(x),
            amplitude = amplitude(x),
            freq = freq(x),
            phase = phase(x),
            nr_steps = round(nr_steps(x)),
            start = start(x),
            end = end(x)
          )
    #end apply_draw

    return \
        apply_draw
#end make_draw
