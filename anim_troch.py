#+
# Animations of trochoid patterns.
# For background on the maths, see <https://en.wikipedia.org/wiki/Spirograph>,
# <https://en.wikipedia.org/wiki/Epitrochoid> and <https://en.wikipedia.org/wiki/Hypotrochoid>.
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

from fractions import \
    Fraction
from turtle import \
    Vec2D
from anim_common import \
    is_interpolator, \
    constant_interpolator, \
    draw_curve

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

    draw_curve(g, f = curve_func, closed = True, nr_steps = nr_steps)
#end draw

class AnimCurve :
    "represents an animating trochoid curve. Pass interpolator functions to the constructor" \
    " which will evaluate to appropriate values for the curve parameters for given x." \
    " Then call the draw method, passing it a Cairo context and a value for x, and a curve" \
    " will be drawn into that context with the corresponding parameters."

    def __init__ \
      (
        self,
        ring_radius,
        wheel_radius,
        wheel_frac,
        phase,
        nr_steps,
        do_settings = None
      ) :
        self.ring_radius_interp = ring_radius if is_interpolator(ring_radius) else constant_interpolator(ring_radius)
        self.wheel_radius_interp = wheel_radius if is_interpolator(wheel_radius) else constant_interpolator(wheel_radius)
        self.wheel_frac_interp = wheel_frac if is_interpolator(wheel_frac) else constant_interpolator(wheel_frac)
        self.phase_interp = phase if is_interpolator(phase) else constant_interpolator(phase)
        self.nr_steps_interp = nr_steps if is_interpolator(nr_steps) else constant_interpolator(nr_steps)
        self.do_settings = do_settings
    #end __init__

    def draw(self, g, x) :
        "draws a trochoid into the Cairo context g with the animated settings" \
        " appropriate to time x."
        if self.do_settings != None :
            self.do_settings(g, x)
        #end if
        # note ring_radius, wheel_radius and nr_steps must be integers
        draw \
          (
            g = g,
            ring_radius = round(self.ring_radius_interp(x)),
            wheel_radius = round(self.wheel_radius_interp(x)),
            wheel_frac = self.wheel_frac_interp(x),
            phase = self.phase_interp(x),
            nr_steps = round(self.nr_steps_interp(x))
          )
    #end draw

#end AnimCurve
