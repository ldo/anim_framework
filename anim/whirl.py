#+
# Animations of whirl patterns.
# For background, see <http://mathworld.wolfram.com/Whirl.html>. Also, nested
# polygons <http://mathworld.wolfram.com/NestedPolygon.html> are a variation on
# this.
#
# Copyright 2016 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under CC-BY-SA <http://creativecommons.org/licenses/by-sa/4.0/>.
#-

import math
import qahirah as qah
from . import \
    common

def draw(g, radius, nr_sides, poly_shrink, nr_polys, phase, start = 0, end = None) :
    "draws a whirl pattern into the qahirah.Context g. radius is the radius of" \
    " the outermost polygon, nr_sides is the number of sides per polygon," \
    " poly_shrink is the shrink factor for each successive nested polygon," \
    " in [-1, +1], nr_polys is how many nested polygons to draw, and phase" \
    " is the phase angle for rotating the entire pattern."

    def subcurve_func(step) :
        return \
            step // nr_sides
    #end subcurve_func

    def curve_func(step) :
        subcurve_idx = step // nr_sides
        side_idx = step % nr_sides
        # distance from centre of polygons to centre of one side of outermost polygon =
        #    radius * math.sin(corner_angle / 2)
        # therefore, distance from centre of polygons to corner of next-inner polygon =
        #    radius * step_scale_factor
        # such that
        #     step_scale_factor = math.sin(corner_angle / 2) / math.cos(math.pi / nr_sides - abs(step_rotate))
        # where
        #     step_rotate = math.pi / nr_sides * poly_shrink
        step_rotate = math.pi / nr_sides * poly_shrink
        corner_angle = (0.5 - 1 / nr_sides) * qah.circle
        step_scale_factor = math.sin(corner_angle / 2) / math.cos(math.pi / nr_sides - abs(step_rotate))
        scale = step_scale_factor ** subcurve_idx
        rotate = \
            (
                phase
            +
                step_rotate * subcurve_idx
            +
                qah.circle / nr_sides * side_idx
            )
        return \
            qah.Vector(radius * scale, 0).rotate(rotate)
    #end curve_func

    common.draw_curve_discrete \
      (
        g = g,
        f = curve_func,
        closed = True,
        nr_steps = nr_polys * nr_sides,
        start = start,
        end = end,
        subcurve = subcurve_func
      )
#end draw

def make_draw(radius, nr_sides, poly_shrink, nr_polys, phase, start = 0, end = None) :
    "returns a draw procedure which will draw a whirl pattern with the specified animatable" \
    " parameters."
    radius = common.ensure_interpolator(radius)
    nr_sides = common.ensure_interpolator(nr_sides)
    poly_shrink = common.ensure_interpolator(poly_shrink)
    nr_polys = common.ensure_interpolator(nr_polys)
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
            radius = radius(x),
            nr_sides = round(nr_sides(x)),
            poly_shrink = poly_shrink(x),
            nr_polys = round(nr_polys(x)),
            phase = phase(x),
            start = start(x),
            end = end(x)
          )
    #end apply_draw

    return \
        apply_draw
#end make_draw
