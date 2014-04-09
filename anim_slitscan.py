#+
# Framework for generating slit-scan animations.
# For some background, see <https://en.wikipedia.org/wiki/Slitscan>.
#
# Copyright 2014 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
# Licensed under CC-BY-SA <http://creativecommons.org/licenses/by-sa/4.0/>.
#-

import math
import cairo

class Slitscan :
    "context for rendering a slitscan image. This is maintained as a bitmap which is" \
    " extent pixels tall and steps pixels wide. The draw routine takes two arguments:" \
    " a Cairo context into which to draw, and the current animation time. Drawing is" \
    " clipped to a single column of pixels corresponding to that time, transformed" \
    " to the bounding rectangle with corners at (0, 0) and (1, extent)."

#+
# Internal stuff
#-

    def time_to_offset(self, at_time) :
        return \
            round((1.0 - at_time) * self.steps - 1) % self.steps
    #end time_to_offset

    def init_background(self) :
        {3 : self.g.set_source_rgb, 4 : self.g.set_source_rgba}[len(self.background)] \
            (*self.background)
        self.g.paint()
    #end init_background

    def get_context(self, at_time) :
        "returns a graphics context for drawing the current row/column of pixels." \
        " at_time is in units such that 1.0 corresponds to the full number" \
        " of pixel steps in the pattern."
        self.g.identity_matrix()
        self.g.reset_clip()
        self.g.new_path()
        self.g.translate(self.time_to_offset(at_time), 0)
        self.g.rectangle \
          (
            0, # x
            0, # y
            1, # width
            self.extent # height
          )
        self.g.clip()
        self.g.new_path()
        self.init_background()
        return \
            self.g
    #end get_context

#+
# User-visible stuff
#-

    def __init__(self, draw, extent, steps, background) :
        self.draw = draw
        self.extent = extent
        self.steps = steps
        self.pix = cairo.ImageSurface(cairo.FORMAT_ARGB32, steps, extent)
        self.pix2 = cairo.ImageSurface(cairo.FORMAT_ARGB32, steps * 2, extent)
        self.background = background
        self.g = cairo.Context(self.pix)
        self.g2 = cairo.Context(self.pix2)
        self.pat1 = cairo.SurfacePattern(self.pix)
        self.pat1.set_extend(cairo.EXTEND_REPEAT)
        self.g2.set_source(self.pat1)
        self.pat = cairo.SurfacePattern(self.pix2)
        self.pat.set_extend(cairo.EXTEND_REPEAT)
        self.pat.set_filter(cairo.FILTER_BILINEAR)
        self.init_background()
        self.last_draw_time = None
    #end __init__

    def render(self, g, at_time, from_x, from_y, from_extent, to_x, to_y, to_extent) :
        "updates the current state of the pattern and draws it into destination Cairo context" \
        " g. The line from (from_x, from_y) to (to_x, to_y) defines the  starting and ending" \
        " points of the animation trajectory, while from_extent and to_extent define the extents" \
        " of the image perpendicular to this direction at these points, the ratio of the values" \
        " defining the amount of perspective foreshortening."
        base_offset = self.time_to_offset(at_time)
        if self.last_draw_time != at_time :
            if self.last_draw_time == None :
                self.last_draw_time = - 1 / self.steps
            #end if
            this_offset = self.time_to_offset(self.last_draw_time)
            time_steps = 0
            while this_offset != base_offset :
                time_steps += 1
                this_offset -= 1
                if this_offset < 0 :
                    this_offset += self.steps
                #end if
                this_time = self.last_draw_time + time_steps / self.steps
                self.draw(self.get_context(this_time), this_time)
            #end while
            self.last_draw_time = at_time
        #end if
        angle = math.atan2(to_y - from_y, to_x - from_x)
        # tile two copies of pix into pix2 to ensure seamless wraparound
        self.pix.flush()
        self.g2.new_path()
        self.g2.rectangle(0, 0, self.steps * 2, self.extent)
        self.g2.fill()
        self.pix2.flush()
        g.save()
        g.translate(from_x, from_y)
        g.rotate(angle) # orient source pattern parallel to x-axis
        g.translate(- from_x, - from_y)
        span = math.hypot(to_x - from_x, to_y - from_y)
        for i in range(0, math.ceil(span)) :
            dst_width = min(span - i, 1)
            dst_extent = i / span * (to_extent - from_extent) + from_extent
            dst_extent2 = (i + dst_width) / span * (to_extent - from_extent) + from_extent
            this_offset = \
                (
                    (
                            (1 / dst_extent - 1 / from_extent)
                        /
                            (1 / to_extent - 1 / from_extent)
                        *
                            self.steps
                    +
                        base_offset
                    )
                %
                    self.steps
                )
            this_offset2 = \
                (
                    (
                            (1 / dst_extent2 - 1 / from_extent)
                        /
                            (1 / to_extent - 1 / from_extent)
                        *
                            self.steps
                    +
                        base_offset
                    )
                %
                    self.steps
                )
            if this_offset2 < this_offset :
                this_offset2 += self.steps
            #end if
            dst_x = from_x + i
            src_rect = (this_offset, 0, this_offset2 - this_offset, self.extent)
            dst_rect = (dst_x, from_y - dst_extent / 2, dst_width, dst_extent)
            m = cairo.Matrix()
            m.translate(src_rect[0], src_rect[1])
            m.scale(self.extent / dst_rect[3], self.extent / dst_rect[3])
            m.translate(- dst_rect[0], - dst_rect[1])
            self.pat.set_matrix(m)
            g.set_source(self.pat)
            g.new_path()
            g.rectangle(*dst_rect)
            g.fill()
        #end for
        g.restore()
    #end render

#end Slitscan

def make_draw(slitscan, from_x, from_y, from_extent, to_x, to_y, to_extent) :

    def apply_draw(g, t) :
        slitscan.render(g, t, from_x, from_y, from_extent, to_x, to_y, to_extent)
    #end apply_draw

#begin make_draw
    return \
        apply_draw
#end make_draw
