#+
# Animations of spirolateral patterns.
# For background, see <http://www.mi.sanu.ac.rs/vismath/krawczyk/spdesc00.htm>.
#
# Copyright 2016 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under CC-BY-SA <http://creativecommons.org/licenses/by-sa/4.0/>.
#-

import math
from fractions import \
    Fraction
import qahirah as qah
from qahirah import \
    Vector
from . import \
    common

def draw(g, step, n, angle, reversed, phase, start = 0, end = 1) :
    "draws a spirolateral curve into the qahirah.Context g. step is the length" \
    " of a unit step, n is the maximum line length in unit steps, angle is the" \
    " angle between line segments as a rational Fraction of a circle, reversed" \
    " is a set of integer line lengths for which to reverse the angle," \
    " and phase the phase angle for rotating the whole curve."

    if reversed == None :
        reversed = frozenset()
    #end if
    start_point = Vector(0, 0)
    seg_points = []
    point = start_point
    dirn = 0
    for i in range(1, n + 1) :
        seg_points.append(point)
        point += Vector(i * step, 0).rotate(float(dirn) * qah.circle)
        dirn += (Fraction(1, 2) - angle) * (1, -1)[i in reversed]
    #end for
    end_point = point
    point_delta = end_point - start_point
    seg_rotate = dirn
    # at this point, seg_rotate is the fraction of a circle turned through by one curve segment.
    point = start_point
    origin = Vector(0, 0)
    dirn = Fraction(0, 1)
    for i in range(seg_rotate.denominator) :
        origin += point
        point += point_delta.rotate(float(dirn) * qah.circle)
        dirn += seg_rotate
    #end for
    closed = abs(start_point - point) < 1e-7
    if not closed :
        seg_points.append(point)
    #end if
    origin /= seg_rotate.denominator
    seg_points = list(point - origin for point in seg_points)
    nr_steps = seg_rotate.denominator * len(seg_points)

    def curve_func(step) :
        return \
            seg_points[step % len(seg_points)].rotate \
              (
                    float(seg_rotate) * (step // len(seg_points)) * qah.circle
                +
                    phase
              )
    #end curve_func

    common.draw_curve_discrete \
      (
        g = g,
        f = curve_func,
        closed = closed,
        nr_steps = nr_steps,
        start = start,
        end = end
      )
#end draw

def make_draw(step, n, angle, reversed, phase, start = 0, end = 1) :
    "returns a draw procedure which will draw a spirolateral curve with the" \
    " specified animatable parameters."
    step = common.ensure_interpolator(step)
    n = common.ensure_interpolator(n)
    angle = common.ensure_interpolator(angle)
    reversed = common.ensure_interpolator(reversed)
    phase = common.ensure_interpolator(phase)
    start = common.ensure_interpolator(start)
    end = common.ensure_interpolator(end)

    def apply_draw(g, x) :
        "draws a spirolateral curve into the qahirah.Context g with the animated settings" \
        " appropriate to time x."
        # note n must be integer and angle must be Fraction
        draw \
          (
            g = g,
            step = step(x),
            n = round(n(x)),
            angle = angle(x),
            reversed = reversed(x),
            phase = phase(x),
            start = start(x),
            end = end(x)
          )
    #end apply_draw

    return \
        apply_draw
#end make_draw
