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
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import os
import math
import colorsys
import cairo

def interpolator(f) :
    "marks f as an interpolator. All functions to be used as interpolators" \
    " should be put through this."
    f.is_interpolator = True
    return f
#end interpolator

function = type(lambda x : x)

def is_interpolator(f) :
    "checks if f is an interpolator function."
    return type(f) == function and hasattr(f, "is_interpolator") and f.is_interpolator
#end is_interpolator

def constant_interpolator(y) :
    "returns a function of x that always returns the same constant value y."
    return \
        interpolator(lambda x : y)
#end constant_interpolator

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
    interps = tuple(f if is_interpolator(f) else constant_interpolator(f) for f in interps)
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

def tuple_interpolator(*interps) :
    "given a tuple of interpolators or constant values, returns a function of x which will" \
    " yield the corresponding tuple of interpolated y-values for a given x."
    if len(interps) == 1 and type(interps[0]) == tuple :
        interps = interps[0]
    #end if
    interps = tuple \
      (
        interp if is_interpolator(interp) else constant_interpolator(interp)
        for interp in interps
      )
    return \
        interpolator(lambda x : tuple(interp(x) for interp in interps))
#end tuple_interpolator

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
    return interpolator \
      (
        lambda x :
            colorsys.hsv_to_rgb
              (
                h = h(x) if is_interpolator(h) else h,
                s = s(x) if is_interpolator(s) else s,
                v = v(x) if is_interpolator(v) else v
              )
      )
#end hsv_to_rgb_interpolator

def hsva_to_rgba_interpolator(h, s, v, a) :
    "given h, s, v, a interpolators or constant values, returns an interpolator that" \
    " converts the interpolated values to an (r, g, b, a) tuple."
    return interpolator \
      (
        lambda x :
                colorsys.hsv_to_rgb
                  (
                    h = h(x) if is_interpolator(h) else h,
                    s = s(x) if is_interpolator(s) else s,
                    v = v(x) if is_interpolator(v) else v
                  )
            +
                (
                    a(x) if is_interpolator(a) else a,
                )
      )
#end hsv_to_rgb_interpolator

def make_applicator(*anim_settings) :
    "anim_settings must be a tuple of 2-tuples; in each 2-tuple, the first element is" \
    " a Cairo context method name, and the second element is a tuple of arguments to that" \
    " method, or an interpolator function returning such a tuple. If the second element is" \
    " a tuple, then each element is either a corresponding argument value, or an interpolator" \
    " that evaluates to such an argument value. This function returns a procedure of 2 arguments," \
    " a Cairo context g and the current time x, which will call each Cairo method on g with" \
    " an argument list  equal to the result of the corresponding interpolator applied to" \
    " that value of x."

    def apply_settings(g, x) :
        for method, interp in anim_settings :
            if is_interpolator(interp) :
                args = interp(x)
            else : # assume tuple
                args = tuple \
                  (
                    arg(x) if is_interpolator(arg) else arg
                    for arg in interp
                  )
            #end if
            getattr(g, method)(*args)
        #end for
    #end apply_settings

#begin make_applicator
    if len(anim_settings) == 1 and type(anim_settings[0]) == tuple :
        anim_settings = anim_settings[0]
    #end if
    return \
        apply_settings
#end make_applicator

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

class NullAnim :
    "base-ish class for animatable objects."

    def draw(self, g, x) :
        "does drawing of shape into Cairo context g at animation time x."
        pass # me, I do nothing
    #end draw

#end NullAnim

class VariantAnim(NullAnim) :
    "an animatable object which does some custom setup before drawing another" \
    " animatable object. Handy for creating variants of an animatable where" \
    " this is simpler than creating a new animatable from scratch each time."

    def __init__(self, presetup, childanim) :
        self.presetup = presetup
        self.childanim = childanim
    #end __init_-

    def draw(self, g, x) :
        self.presetup(g, x)
        self.childanim.draw(g, x)
    #end draw

#end VariantAnim

class ApplicatorAnim(NullAnim) :
    "an animatable object which just does a sequence of Cairo calls into" \
    " the given context. Constructor arguments are the same as for make_applicator" \
    " (above)."

    def __init__(self, *settings) :
        self.draw = make_applicator(settings)
    #end __init__

#end ApplicatorAnim

def render_anim \
  (
    width,
    height,
    start_time,
    end_time,
    frame_rate,
    anim_objects, # sequence of NullAnim or similar
    overall_presetup, # called to do once-off setup of Cairo context
    frame_presetup, # called at start of rendering each frame
    frame_postsetup, # called at end of rendering each frame
    out_dir, # where to write numbered PNG frames
    start_frame_nr # frame number corresponding to time 0
  ) :
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
        if frame_presetup != None :
            frame_presetup(g, t)
        #end if
        for anim_object in anim_objects :
            g.save()
            anim_object.draw(g, t)
            g.restore()
        #end for
        if frame_postsetup != None :
            frame_postsetup(g, t)
        #end if
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
