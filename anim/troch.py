#+
# Animations of trochoid patterns.
# For background on the maths, see <https://en.wikipedia.org/wiki/Spirograph>,
# <https://en.wikipedia.org/wiki/Epitrochoid> and <https://en.wikipedia.org/wiki/Hypotrochoid>.
#
# Copyright 2014 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under CC-BY-SA <http://creativecommons.org/licenses/by-sa/4.0/>.
#-

from fractions import \
    Fraction
from qahirah import \
    circle, \
    Vector
from . import \
    common

def draw(g, ring_radius, wheel_radius, wheel_frac, phase, nr_steps, start = 0, end = 1) :
    "draws a trochoid curve into the qahirah.Context g. ring_radius is the radius of the" \
    " stationary ring, while wheel_radius is the radius of the moving wheel; both must" \
    " be integers. frac is the fraction of the wheel radius that the actual" \
    " point on the curve is located from the centre of the wheel. nr_steps is the" \
    " number of straight-line segments to use to approximate the curve." \
    " Setting up pen size, draw pattern etc is left up to caller."
    ratio = Fraction(ring_radius, wheel_radius)
    nr_cycles = ratio.denominator # to produce one complete traversal of curve

    def curve_func(x) :
        theta_ring = circle * nr_cycles * x
        theta_wheel = theta_ring * (ring_radius / wheel_radius + 1)
        wheel_pos = Vector(ring_radius + wheel_radius, 0).rotate(theta_ring + phase * circle)
        curve_pos = wheel_pos + Vector(wheel_radius * wheel_frac, 0).rotate(theta_wheel)
        return curve_pos
    #end curve_func

    common.draw_curve(g, f = curve_func, closed = True, nr_steps = nr_steps, start = start, end = end)
#end draw

def make_draw(ring_radius, wheel_radius, wheel_frac, phase, nr_steps, start = 0, end = 1) :
    "returns a draw procedure which will draw a trochoid curve with the specified animatable" \
    " parameters."
    ring_radius = common.ensure_interpolator(ring_radius)
    wheel_radius = common.ensure_interpolator(wheel_radius)
    wheel_frac = common.ensure_interpolator(wheel_frac)
    phase = common.ensure_interpolator(phase)
    nr_steps = common.ensure_interpolator(nr_steps)
    start = common.ensure_interpolator(start)
    end = common.ensure_interpolator(end)

    def apply_draw(g, x) :
        "draws a trochoid into the qahirah.Context g with the animated settings" \
        " appropriate to time x."
        # note ring_radius, wheel_radius and nr_steps must be integers
        draw \
          (
            g = g,
            ring_radius = round(ring_radius(x)),
            wheel_radius = round(wheel_radius(x)),
            wheel_frac = wheel_frac(x),
            phase = phase(x),
            nr_steps = round(nr_steps(x)),
            start = start(x),
            end = end(x)
          )
    #end apply_draw

    return \
        apply_draw
#end make_draw
