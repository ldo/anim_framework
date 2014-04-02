#+
# Animations of rose curves.
# For background on the maths, see <https://en.wikipedia.org/wiki/Rose_curve>.
#
# Copyright 2014 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import math
from fractions import \
    Fraction
import anim_common

def draw(g, radius, amplitude, freq_numer, freq_denom, phase, nr_steps) :
    ratio = Fraction(freq_numer, freq_denom)
    nr_cycles = ratio.denominator # to produce one complete traversal of curve

    def curve_func(x) :
        phi = 2 * math.pi * x * nr_cycles * freq_denom
        theta = 2 * math.pi * (x + phase) * nr_cycles * freq_numer
        r = radius + math.sin(theta) * amplitude
        return \
            (
                r * math.cos(phi),
                r * math.sin(phi)
            )
    #end curve_func

    anim_common.draw_curve(g, f = curve_func, closed = True, nr_steps = nr_steps)
#end draw

def make_draw(radius, amplitude, freq_numer, freq_denom, phase, nr_steps, do_settings = None) :
    radius = anim_common.ensure_interpolator(radius)
    amplitude = anim_common.ensure_interpolator(amplitude)
    freq_numer = anim_common.ensure_interpolator(freq_numer)
    freq_denom = anim_common.ensure_interpolator(freq_denom)
    phase = anim_common.ensure_interpolator(phase)
    nr_steps = anim_common.ensure_interpolator(nr_steps)

    def apply_draw(g, x) :
        if do_settings != None :
            do_settings(g, x)
        #end if
        # note freq_numer, freq_denom and nr_steps must be integers
        draw \
          (
            g = g,
            radius = radius(x),
            amplitude = amplitude(x),
            freq_numer = round(freq_numer(x)),
            freq_denom = round(freq_denom(x)),
            phase = phase(x),
            nr_steps = round(nr_steps(x))
          )
    #end apply_draw

    return \
        apply_draw
#end make_draw
