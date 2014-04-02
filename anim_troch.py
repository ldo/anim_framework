#+
# Animations of trochoid patterns.
# For background on the maths, see <https://en.wikipedia.org/wiki/Spirograph>,
# <https://en.wikipedia.org/wiki/Epitrochoid> and <https://en.wikipedia.org/wiki/Hypotrochoid>.
#
# Copyright 2014 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

from fractions import \
    Fraction
from turtle import \
    Vec2D
import anim_common

def draw(g, ring_radius, wheel_radius, wheel_frac, phase, nr_steps) :
    "draws a trochoid curve into the Cairo context g. ring_radius is the radius of the" \
    " stationary ring, while wheel_radius is the radius of the moving wheel; both must" \
    " be integers. frac is the fraction of the wheel radius that the actual" \
    " point on the curve is located from the centre of the wheel. nr_steps is the" \
    " number of straight-line segments to use to approximate the curve." \
    " Setting up pen size, draw pattern etc is left up to caller."
    ratio = Fraction(ring_radius, wheel_radius)
    nr_cycles = ratio.denominator # to produce one complete traversal of curve

    def curve_func(x) :
        theta_ring = 360 * nr_cycles * x
        theta_wheel = theta_ring * (ring_radius / wheel_radius + 1)
        wheel_pos = Vec2D(ring_radius + wheel_radius, 0).rotate(theta_ring + phase)
        curve_pos = wheel_pos + Vec2D(wheel_radius * wheel_frac, 0).rotate(theta_wheel)
        return tuple(curve_pos)
    #end curve_func

    anim_common.draw_curve(g, f = curve_func, closed = True, nr_steps = nr_steps)
#end draw

def make_draw(ring_radius, wheel_radius, wheel_frac, phase, nr_steps, do_settings = None) :
    "returns a draw procedure which will draw a trochoid curve with the specified animatable" \
    " parameters."
    ring_radius = anim_common.ensure_interpolator(ring_radius)
    wheel_radius = anim_common.ensure_interpolator(wheel_radius)
    wheel_frac = anim_common.ensure_interpolator(wheel_frac)
    phase = anim_common.ensure_interpolator(phase)
    nr_steps = anim_common.ensure_interpolator(nr_steps)

    def apply_draw(g, x) :
        "draws a trochoid into the Cairo context g with the animated settings" \
        " appropriate to time x."
        if do_settings != None :
            do_settings(g, x)
        #end if
        # note ring_radius, wheel_radius and nr_steps must be integers
        draw \
          (
            g = g,
            ring_radius = round(ring_radius(x)),
            wheel_radius = round(wheel_radius(x)),
            wheel_frac = wheel_frac(x),
            phase = phase(x),
            nr_steps = round(nr_steps(x))
          )
    #end apply_draw

    return \
        apply_draw
#end make_draw
