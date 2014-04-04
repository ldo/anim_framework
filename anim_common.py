#+
# Framework for doing various animations of drawing into a Cairo
# graphics context.
#
# An “interpolator” is a function of a scalar value x (representing time)
# and returning anything. This module provides various predefined forms
# of interpolator, as well as functions for composing them into new
# interpolators, and you are free to add your own. But make sure to put
# your function through the “interpolator” function below (which can be
# used as a decorator). This allows you to freely pass combinations
# of interpolators and constant values into the animation framework, and
# it can automatically tell which values are animated and which are not.
#
# A draw procedure takes two arguments (g, t), g being a Cairo context
# into which to draw the current frame, and t being the current frame time.
#
# Copyright 2014 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under CC-BY-SA <http://creativecommons.org/licenses/by-sa/4.0/>.
#-

from types import \
    FunctionType
import os
import math
import colorsys
import cairo

#+
# Interpolators
#-

def interpolator(f) :
    "marks f as an interpolator. All functions to be used as interpolators" \
    " should be put through this."
    f.is_interpolator = True
    return f
#end interpolator

def is_interpolator(f) :
    "checks if f is an interpolator function."
    return type(f) == FunctionType and hasattr(f, "is_interpolator") and f.is_interpolator
#end is_interpolator

def constant_interpolator(y) :
    "returns a function of x that always returns the same constant value y."
    return \
        interpolator(lambda x : y)
#end constant_interpolator

def ensure_interpolator(f) :
    "ensures f is an interpolator, by creating a constant interpolator returning f if not."
    return \
        f if is_interpolator(f) else constant_interpolator(f)
#end ensure_interpolator

def linear_interpolator(from_x, to_x, from_y, to_y) :
    "returns a function of x in the range [from_x .. to_x] which returns" \
    " the corresponding linearly-interpolated value in the range [from_y .. to_y]."
    return \
        interpolator(lambda x : (x - from_x) / (to_x - from_x) * (to_y - from_y) + from_y)
#end linear_interpolator

def piecewise_interpolator(x_vals, interps) :
    "x_vals must be a monotonically-increasing sequence of x-values, defining" \
    " domain segments, and interps must be a tuple of interpolator functions," \
    " one less in length. interps[i] is used for x values in the range" \
    " x_vals[i] .. x_vals[i + 1]. The x value is first normalized to [0 .. 1]" \
    " over this range, and the returned ranges from interpolators after the first one" \
    " are adjusted, each relative to the previous one, to ensure the overall" \
    " interpolation is piecewise continuous."

    @interpolator
    def interpolate(x) :
        y_offset = 0
        i = 0
        while True :
            if i >= len(interps) - 1 or x_vals[i + 1] >= x :
                y = interps[i]((x - x_vals[i]) / (x_vals[i + 1] - x_vals[i])) + y_offset
                break
            #end if
            y_offset += interps[i](1) - interps[i + 1](0)
            i += 1
        #end while
        return y
    #end interpolate

#begin piecewise_interpolator
    assert len(x_vals) >= 2 and len(interps) + 1 == len(x_vals)
    interps = tuple(ensure_interpolator(f) for f in interps)
    return \
        interpolate
#end piecewise_interpolator

def piecewise_linear_interpolator(x_vals, y_vals) :
    "x_vals must be a monotonically-increasing sequence of x-values, defining" \
    " domain segments, and y_vals must be a monotically-increasing sequence of" \
    " the same length of corresponding y-values defining piecewise-linear" \
    " range segments. returns a function that will map an input x value to" \
    " the corresponding y value linearly-interpolated over the appropriate segment."
    assert len(x_vals) >= 2 and len(x_vals) == len(y_vals)
    return \
        piecewise_interpolator \
          (
            x_vals,
            tuple
              (
                linear_interpolator(0, 1, y_vals[i], y_vals[i + 1])
                for i in range(0, x_vals - 1)
              )
          )
#end piecewise_linear_interpolator

def func_interpolator(func, *args) :
    "given a function of n args, and n interpolators or constant values, returns an" \
    " interpolator which will return the function of those (interpolated) values at" \
    " the specified time."
    if len(args) == 1 and type(args[0]) == tuple :
        args = args[0]
    #end if
    args = tuple \
      (
        ensure_interpolator(arg)
        for arg in args
      )
    return \
        interpolator(lambda x : func(*tuple(arg(x) for arg in args)))
#end func_interpolator

def periodic_interpolator(from_x, to_x, interp, offset = 0) :
    "given an existing interpolator defined over the domain [from_x, to_x], returns" \
    " an interpolator which repeats the same function over equal-sized intervals" \
    " before and after the original domain."
    return \
        interpolator \
          (
            lambda x : interp((x - offset) % (to_x - from_x) + from_x)
          )
#end periodic_interpolator

def step_interpolator(x_vals, y_vals) :
    "x_vals must be a tuple of monotonically increasing values, and y_vals a tuple" \
    " with a length one less. returns an interpolator that returns y_vals[i] when" \
    " x_vals[i] ≤ x ≤ x_vals[i + 1]."

    @interpolator
    def step_interpolate(x) :
        i = len(x_vals) - 2
        while x_vals[i] > x :
            i -= 1
        #end while
        return \
            y_vals[i]
    #end step_interpolate

#begin step_interpolator
    assert len(x_vals) >= 2 and len(x_vals) == len(y_vals) + 1
    return \
        step_interpolate
#end step_interpolator

def transform_interpolator(interp, scale, offset) :
    "returns an interpolator which is interp operating on an x-coordinate subjected" \
    " to the specified scale and offset."
    return \
        interpolator(lambda x : interp((x - offset) / scale))
#end transform_interpolator

def hsv_to_rgb_interpolator(h, s, v) :
    "given h, s, v interpolators or constant values, returns an interpolator that" \
    " converts the interpolated values to an (r, g, b) tuple. Handy for Cairo functions" \
    " that only take r, g, b colours, because animating in HSV space usually gives more" \
    " useful effects."
    h = ensure_interpolator(h)
    s = ensure_interpolator(s)
    v = ensure_interpolator(v)
    return interpolator \
      (
        lambda x : colorsys.hsv_to_rgb(h(x), s(x), v(x))
      )
#end hsv_to_rgb_interpolator

def hsva_to_rgba_interpolator(h, s, v, a) :
    "given h, s, v, a interpolators or constant values, returns an interpolator that" \
    " converts the interpolated values to an (r, g, b, a) tuple."
    h = ensure_interpolator(h)
    s = ensure_interpolator(s)
    v = ensure_interpolator(v)
    a = ensure_interpolator(a)
    return interpolator \
      (
        lambda x : colorsys.hsv_to_rgb(h(x), s(x), v(x)) + (a(x),)
      )
#end hsv_to_rgb_interpolator

#+
# Draw procedures
#-

def null_draw(g, x) :
    "a draw procedure which does nothing."
    pass
#end null_draw

def make_draw(*draw_settings) :
    "draw_settings must be a tuple of 2-tuples; in each 2-tuple, the first element is" \
    " a Cairo context method name, and the second element is a tuple of arguments to that" \
    " method, or an interpolator function returning such a tuple. If the second element is" \
    " a tuple, then each element is either a corresponding argument value, or an interpolator" \
    " that evaluates to such an argument value. This function returns a draw procedure" \
    " that applies the specified settings to a given Cairo context at the specified time."

    def apply_settings(g, x) :
        for method, interp in draw_settings :
            if is_interpolator(interp) :
                args = interp(x)
            else : # assume tuple
                args = tuple \
                  (
                    ensure_interpolator(arg)(x)
                    for arg in interp
                  )
            #end if
            getattr(g, method)(*args)
        #end for
    #end apply_settings

#begin make_draw
    if len(draw_settings) == 1 and type(draw_settings[0]) == tuple :
        draw_settings = draw_settings[0]
    #end if
    return \
        apply_settings
#end make_draw

def draw_overlay(*draw_procs) :
    "given a sequence of draw procedures, returns a draw procedure that invokes" \
    " them one on top of the other. The Cairo context is saved/restored around each one."

    def apply_overlay(g, x) :
        for proc in draw_procs :
            g.save()
            proc(g, x)
            g.restore()
        #end for
    #end apply_overlay

#begin draw_overlay
    if len(draw_procs) == 1 and type(draw_procs[0]) == tuple :
        draw_procs = draw_procs[0]
    #end if
    return \
        apply_overlay
#end draw_overlay

def draw_compose(*draw_procs) :
    "given a sequence of draw procedures, returns a draw procedure that invokes" \
    " them one after the other. Unlike draw_overlay, the Cairo context is NOT" \
    " saved/restored around each one."

    def apply_compose(g, x) :
        for proc in draw_procs :
            proc(g, x)
        #end for
    #end apply_compose

#begin draw_compose
    if len(draw_procs) == 1 and type(draw_procs[0]) == tuple :
        draw_procs = draw_procs[0]
    #end if
    return \
        apply_compose
#end draw_compose

def draw_sequence(x_vals, draws) :
    "given a sequence of x values x_vals, and a sequence of draw procedures draws" \
    " such that len(draws) = len(x_vals) + 1, returns a draw procedure which will" \
    " invoke draws[0] during the time before x_vals[0], draws[-1] during the time" \
    " after x_vals[-1], and in-between elements of draws during the corresponding" \
    " intervals between consecutive elements of x_vals. You can use null_draw if you" \
    " don’t want drawing to happen during a particular range of times."

    def select_from_sequence(g, x) :
        i = len(x_vals)
        while True :
            if i == 0 :
                draw = draws[0]
                break
            #end if
            if x >= x_vals[i - 1] :
                draw = draws[i]
                break
            #end if
            i -= 1
        #end while
        draw(g, x)
    #end select_from_sequence

#begin draw_sequence
    assert len(draws) != 0 and len(x_vals) + 1 == len(draws)
    return \
        select_from_sequence
#end draw_sequence

def retime_draw(draw, interp) :
    "returns a draw procedure which invokes draw with the time transformed through interp."
    def apply_draw(g, x) :
        draw(g, interp(x))
    #end apply_draw
    return \
        apply_draw
#end retime_draw

#+
# Higher-level useful stuff
#-

def draw_curve(g, f, closed, nr_steps) :
    "g is a Cairo context, f is a function over [0, 1) returning a tuple of" \
    " (x, y) coordinates, defining the curve to draw, and nr_steps is the" \
    " number of straight-line segments to approximate the curve. if closed," \
    " then the end and start points will be joined by an additional segment." \
    " The path will be stroked with the current settings in g."
    g.new_path()
    setpos = g.move_to # for first point
    for i in range(0, nr_steps) :
        setpos(*f(i / nr_steps))
        setpos = g.line_to # for subsequent points
    #end for
    if closed :
        g.close_path()
    #end if
    g.stroke()
#end draw_curve

def render_anim \
  (
    width,
    height,
    start_time,
    end_time,
    frame_rate,
    draw_frame, # draw procedure
    overall_presetup, # called to do once-off setup of Cairo context
    out_dir, # where to write numbered PNG frames
    start_frame_nr # frame number corresponding to time 0
  ) :
    "renders out an animation to a sequence of PNG image files."
    pix = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    g = cairo.Context(pix)
    if overall_presetup != None :
        overall_presetup(g)
    #end if
    from_frame_nr = math.ceil(start_time * frame_rate)
    to_frame_nr = math.floor(end_time * frame_rate) + 1
    for frame_nr in range(from_frame_nr, to_frame_nr) :
        g.save()
        t = frame_nr / frame_rate
        draw_frame(g, t)
        g.restore()
        pix.flush()
        pix.write_to_png \
          (
            os.path.join(out_dir, "%04d.png" % (frame_nr + start_frame_nr))
          )
    #end for
    return \
        (from_frame_nr, to_frame_nr)
#end render_anim
