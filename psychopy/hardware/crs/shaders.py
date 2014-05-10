#!/usr/bin/env python
#coding=utf-8

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

#Acknowledgements:
#    This code was mostly written by Jon Peirce.
#    CRS Ltd provided support as needed.
#    Shader code for mono++ and color++ modes was based on code in Psythtoolbox
#    (Kleiner) but does not actually use that code directly

from psychopy._shadersPyglet import compileProgram, vertSimple

bitsMonoModeFrag="""
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
        index = fboFrag.r * 65535.0;
        gl_FragColor.r = floor(index / 256.0) / 255.0;
        gl_FragColor.g = mod(index, 256.0) / 255.0;
    }
"""

bitsColorModeFrag = """
/* Mono++ output formatter
 *
 * Converts from a 16bit framebuffer object into a 8bit per channel frame
 * for use in mono++ mode of Bits# and Bits++ devices
 *
 */
    #extension GL_ARB_texture_rectangle : enable
    uniform sampler2D fbo;
    vec3 index;

    void main() {
        vec2 scrPos = gl_TexCoord[0].st;
        scrPos.t = (scrPos.t - mod(scrPos.t, 2.0));
        vec4 fboFrag = texture2D(fbo, scrPos);

        index = fboFrag.rgb * 65535.0;

        if (mod(gl_FragCoord.x, 2.0) < 1.0) {
            /* Even output pixel: high byte */
            gl_FragColor.rgb = floor(index / 256.0) / 255.0;
        }
        else {
            /* Odd output pixel: low byte */
            gl_FragColor.rgb = mod(index, 256.0) / 255.0;
        }
    }
"""
