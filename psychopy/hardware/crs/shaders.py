#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Acknowledgements:
#    Written by Jon Peirce
#
#    Based on shader code for mono++ and color++ modes code in Psythtoolbox
#    (Mario Kleiner) but does not use that code directly
#    It is, for example, Mario's idea to add the 0.01 to avoid rounding issues

from __future__ import absolute_import, print_function
from psychopy.visual.shaders import compileProgram, vertSimple

bitsMonoModeFrag = """
/* Mono++ output formatter
 *
 * Converts from a 16bit framebuffer object into a 8bit per channel frame
 * for use in mono++ mode of Bits# and Bits++ devices
 *
 */

    uniform sampler2D fbo;
    float index;

    void main() {
        vec4 fboFrag = texture2D(fbo, gl_TexCoord[0].st);
        gl_FragColor.rgb = fboFrag.rgb;
        index = fboFrag.r * 65535.0 + 0.01;
        gl_FragColor.r = floor(index / 256.0) / 255.0;
        gl_FragColor.g = mod(index, 256.0) / 255.0;
        gl_FragColor.b = 0.0;
    }
"""

bitsColorModeFrag = """
/* Mono++ output formatter
 *
 * Converts from a 16bit framebuffer object into a 8bit per channel frame
 * for use in color++ mode of Bits# and Bits++ devices
 *
 */
    uniform sampler2D fbo;
    vec3 index;

    void main() {
        vec4 fboFrag = texture2D(fbo, gl_TexCoord[0].st);
        gl_FragColor.rgb = fboFrag.rgb;
        index = floor(fboFrag.rgb * 65535.0 + 0.5) + 0.01;
        if (mod(gl_FragCoord.x, 2.0) < 1.0){
          gl_FragColor.rgb = floor(index / 256.0) / 255.0;
        }
        else {
            /* Odd output pixel: */
          gl_FragColor.rgb = mod(index, 256.0) / 255.0;
        /* Ensure alpha channel to 1.0. */
        gl_FragColor.a = 1.0;
        }
    }
"""
