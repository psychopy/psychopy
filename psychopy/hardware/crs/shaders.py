#!/usr/bin/env python
#coding=utf-8

# LICENSE INFORMATION
# ==========================
# This file contains code derived from shader programs contained in Psychtoolbox
# version 3.0.9 (http://psychtoolbox.org/) and shader compilation code in
# PsychoPy 1.65.02 (http://psychopy.org/). Although these projects are both
# released under GPL licenses (versions 2 and 3 respectively) the authors
# (Mario Kleiner and Jonathan Peirce) have given permission for these parts of
# their code to be reused here under the more permissive license
# used by the pycrsltd library
#
#
# Copyright (c) 2011 Jon Peirce <jon@peirce.org.uk>, Cambridge Research Systesm (CRS) Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from ctypes import *
from pyglet import gl

FRAG = gl.GL_FRAGMENT_SHADER_ARB
VERT = gl.GL_VERTEX_SHADER_ARB
shaderTypes=[FRAG, VERT]

class ShaderCode:
    def __init__(self, src, shaderType):
        self.src=src
        if shaderType not in shaderTypes:
            print "warning: shaderType was not a known type"
        else:
            self.type=shaderType

def compileProgram(vertex=None, fragment=None, attachments=[]):
    """Create and compile a vertex and fragment shader pair from their sources (strings)

    Usage::

        prog = compileProgram(vertex, fragment, attachments=[])

    where:

        - vertex is the main vertex shader source (or ShaderCode object)
        - fragment is the main fragment shader source (or ShaderCode object)
        - attachments is a list of ShaderCode objects, with valid shaderType set

    """

    #Derived from shader compilation code in PsychoPy 1.65.02, with permission
    # from JWP to reuse under more permissive license

    def compileShader( source, shaderType ):
            """Compile shader source of given type (only needed by compileProgram)"""
            shader = gl.glCreateShaderObjectARB(shaderType)

            #were we given a source string or a ShaderCode object?
            if hasattr(source, 'src'): source = source.src

            prog = c_char_p(source)
            length = c_int(-1)
            gl.glShaderSourceARB(shader,
                              1,
                              cast(byref(prog), POINTER(POINTER(c_char))),
                              byref(length))
            gl.glCompileShaderARB(shader)

            #check for errors
            status = c_int()
            gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS, byref(status))
            if not status.value:
                #	retrieve the log length
                gl.glGetShaderiv(shader, gl.GL_INFO_LOG_LENGTH, byref(status))
                # create a buffer for the log
                buffer = create_string_buffer(status.value)#from ctypes
                # retrieve the log text
                gl.glGetProgramInfoLog(shader, status, None, buffer)
                # print the log to the console
                print buffer.value
                gl.glDeleteShader(shader)
                raise ValueError, 'Shader compilation failed'
            return shader

    program = gl.glCreateProgramObjectARB()

    #compile attachments before main vertex and frag progs
    for thisAttachment in attachments:
        attachment = compileShader(thisAttachment, thisAttachment.type)
        gl.glAttachObjectARB(program, attachment)
    if vertex:
            vertexShader = compileShader(vertex, VERT)
            gl.glAttachObjectARB(program, vertexShader)
    if fragment:
            fragmentShader = compileShader(fragment, FRAG)
            gl.glAttachObjectARB(program, fragmentShader)
    #compile the overall program
    gl.glValidateProgramARB( program )
    gl.glLinkProgramARB(program)
    #cleanup
    if vertex:
            gl.glDeleteObjectARB(vertexShader)
    if fragment:
            gl.glDeleteObjectARB(fragmentShader)
    return program

gammaCorrectionFrag= ShaderCode(src="""
/* Shader for gamma correction of RGB and Luminance textures.
 * Uses extended formula for gamma correction:
 * out = bias + gain * ( ( (in - Lmin) / (Lmax - Lmin) ) ^ Gamma ).
 * 'Gamma' is the factor to apply, ie. the inverse gamma 1/G,
 * if applying correction for a display with gamma G.
 * 'in' is the input value (e.g., luminance), Lmin and Lmax are the expected
 * minimum and maximum values for 'in', 'gain' is a gain to post-multiply,
 * 'bias' is an offset to add to the final result.
 *
 * This shader is used by PsychColorCorrection() in 'SimpleGammaXXX' mode,
 * as part of PTB's built-in stimulus gamma correction.
 *
 * (w)2008, 2009 by Mario Kleiner.
*/

/* (RedGamma, GreenGamma, BlueGamma) vector of encoding gammas: */
/* To be initialized by PsychColorCorrection() typically: */
uniform vec3    ICMEncodingGamma;
uniform vec3    ICMMinInLuminance;
uniform vec3    ICMMaxInLuminance;
uniform vec3    ICMReciprocalLuminanceRange;
uniform vec3    ICMOutputGain;
uniform vec3    ICMOutputBias;

/* Allowable range for output values: To be initialized by PsychColorCorrection() typically: */
uniform vec2    ICMClampToColorRange;

vec4 gammaCorrect3(vec4 incolor)
{
    vec4 outcolor;

    /* Return alpha component unmodified: */
    outcolor.a = incolor.a;

    /* Clamp input to valid [ICMMinInLuminance ; ICMMaxInLuminance] range: */
    incolor.rgb = clamp(incolor.rgb, ICMMinInLuminance, ICMMaxInLuminance);

    /* Convert clamped input to normalized 0-1 interval: */
    incolor.rgb = (incolor.rgb - ICMMinInLuminance) * ICMReciprocalLuminanceRange;

    /* Map RGB components through power function with Gamma coeff.: */
    outcolor.rgb = (pow(incolor.rgb, ICMEncodingGamma) * ICMOutputGain) + ICMOutputBias;

    /* Clamp outcolor to range given by ICMClampToColorRange: */
    outcolor.rgb = clamp(outcolor.rgb, vec3(ICMClampToColorRange[0]), vec3(ICMClampToColorRange[1]));

    return(outcolor);
}

float gammaCorrect1(float incolor)
{
    float outcolor;

    /* Clamp input to valid [ICMMinInLuminance ; ICMMaxInLuminance] range: */
    incolor = clamp(incolor, ICMMinInLuminance.r, ICMMaxInLuminance.r);

    /* Convert clamped input to normalized 0-1 interval: */
    incolor = (incolor - ICMMinInLuminance.r) * ICMReciprocalLuminanceRange.r;

    /* Map luminance component through power function with Gamma coeff.: */
    outcolor = (pow(incolor, ICMEncodingGamma.r) * ICMOutputGain.r) + ICMOutputBias.r;

    /* Clamp outcolor to range given by ICMClampToColorRange: */
    outcolor = clamp(outcolor, ICMClampToColorRange[0], ICMClampToColorRange[1]);

    return(outcolor);
}
""", shaderType=FRAG)

bitsMonoModeFrag=ShaderCode(src="""
/* Mono++ output formatter
 *
 * This shader converts a HDR texture into a RGBA8 8bpc framebuffer
 * image, suitable for display with the CRS Bits++ system in Mono++
 * mode. It expects the luminance image data in the red channel of
 * the texture, with values ranging from 0.0 - 1.0, remaps it into
 * the 16 bit data range of Bits++, then encodes the 16 bit luminance
 * value into the red+green channels (8 MSB in red, 8 LSB in green). The
 * blue channel is set to 0.0, i.e., black. The alpha channel is set to
 * a fixed maximum value of 1.0, because alpha blending on such an image
 * would be an undefined operation.
 *
 * This shader is intended for use as a plugin for the 'FinalOutputFormattingBlit'
 * chain of the Psychtoolbox-3 imaging pipeline.
 *
 * (c)2007 by Mario Kleiner, part of PTB-3, converted from GPL with permission
 *
 */

#extension GL_ARB_texture_rectangle : enable

uniform sampler2DRect Image;
uniform sampler1D moduloLUT;

void main()
{
    /* Retrieve RGBA HDR input color value. */
    float incolor = texture2DRect(Image, gl_TexCoord[0].st).r;

    /* Remap red channel from 0.0 - 1.0 to 0 to 65535: */
    float index = (incolor * 65535.0) / 256.0;

    /* Compute high byte (8 MSBs) and store in red output color. */
    gl_FragColor.r = floor(index) / 255.0;

    /* Compute low byte (8 LSBs) and store in green output color. */
    gl_FragColor.g = texture1D(moduloLUT, mod(index, 1.0)).r;

    /* Fix blue channel to 0.0, fix alpha channel to 1.0. */
    gl_FragColor.ba = vec2(0.0, 1.0);
}
""", shaderType=FRAG)

bitsColorModeFrag=ShaderCode(src="""
/* Bits++_Color++_FormattingShader.frag.txt -- Color++ output formatter
 *
 * This shader converts a HDR texture into a RGBA8 8bpc framebuffer
 * image, suitable for display with the CRS Bits++ system in Color++
 * mode. It expects the RGB image data in the respective channels of
 * the texture, with values ranging from 0.0 - 1.0, remaps it into
 * the 16 bit data range of Bits++, then encodes the 16 bit values
 * value into the red+green+blue channels of consecutive pixels. Each 16 bit
 * valus is split into 8 Most significant bits and 8 least significant bits,
 * and these are stored in consecutive color components of pixels. This way,
 * two color components encode one color channel and one needs two consecutive
 * horizontal pixels in the framebuffer to encode one Bits++ color pixel.
 *
 * Encoding schema:
 * The high bytes are encoded in  components of even pixels,
 * The low bytes are encoded in components of consecutive odd pixels,
 * The alpha channel is set to a fixed maximum value of 1.0, because alpha
 * blending on such an image would be an undefined operation.
 *
 * This approach reduces the effectively useable horizontal display resolution to
 * half the "real" display resolution.
 *
 * This shader is intended for use as a plugin for the 'FinalOutputFormattingBlit'
 * chain of the Psychtoolbox-3 imaging pipeline.
 *
 * (c)2007, 2008 by Mario Kleiner, part of PTB-3, licensed to you under GPL v2.
 * See file License.txt in the Psychtoolbox root folder for the license.
 *
 */

#extension GL_ARB_texture_rectangle : enable

uniform sampler2DRect Image;
uniform float         sampleSpacing;

/* Declare external function for color conversion: */
vec4 gammaCorrect(vec4 incolor);

void main()
{
    /* Get default texel read position (x,y): x is column, y is row of image. */
    vec2 readpos = gl_FragCoord.xy;

    /* Update the s (==column) component to only read even or odd lines, replicating them. */
    readpos.s = (readpos.s - mod(readpos.s, 2.0)) * sampleSpacing;

    /* Retrieve RGBA HDR input color value for a virtual Bits++ pixel. */
    vec4 incolor = texture2DRect(Image, readpos);

    /* Apply some color transformation (clamping, gamma correction etc.): */
    incolor = gammaCorrect(incolor);

    /* Remap all color channels from 0.0 - 1.0 to 0 to 65535: */
    /* Perform rounding for non-integral numbers and add a small epsilon to take numeric roundoff into account: */
    vec3 index = floor(incolor.rgb * 65535.0 + 0.5) + 0.01;

    /* Compute high bytes (8 MSBs) for all color components. */
    vec3 hibytes = floor(index / 256.0) / 255.0;

    /* Compute low bytes (8 LSBs) for color components. */
    vec3 lobytes = mod(index, 256.0) / 255.0;

    /* Distribution of bytes into output pixel components is dependent */
    /* on our output pixel location. Are we writing an even or odd pixel? */
    if (mod(gl_FragCoord.x, 2.0) < 1.0) {
        /* Even output pixel: */
        gl_FragColor.r = hibytes.r;
        gl_FragColor.g = hibytes.g;
        gl_FragColor.b = hibytes.b;
    }
    else {
        /* Odd output pixel: */
        gl_FragColor.r = lobytes.r;
        gl_FragColor.g = lobytes.g;
        gl_FragColor.b = lobytes.b;
    }

    /* Fix alpha channel to 1.0. */
    gl_FragColor.a = 1.0;
}
""", shaderType=FRAG)
bitsColorModeFrag=ShaderCode(src="""
/* Bits++_Color++_FormattingShader.frag.txt -- Color++ output formatter
 *
 * This shader converts a HDR texture into a RGBA8 8bpc framebuffer
 * image, suitable for display with the CRS Bits++ system in Color++
 * mode. It expects the RGB image data in the respective channels of
 * the texture, with values ranging from 0.0 - 1.0, remaps it into
 * the 16 bit data range of Bits++, then encodes the 16 bit values
 * value into the red+green+blue channels of consecutive pixels. Each 16 bit
 * valus is split into 8 Most significant bits and 8 least significant bits,
 * and these are stored in consecutive color components of pixels. This way,
 * two color components encode one color channel and one needs two consecutive
 * horizontal pixels in the framebuffer to encode one Bits++ color pixel.
 *
 * Encoding schema:
 * The high bytes are encoded in  components of even pixels,
 * The low bytes are encoded in components of consecutive odd pixels,
 * The alpha channel is set to a fixed maximum value of 1.0, because alpha
 * blending on such an image would be an undefined operation.
 *
 * This approach reduces the effectively useable horizontal display resolution to
 * half the "real" display resolution.
 *
 * This shader is intended for use as a plugin for the 'FinalOutputFormattingBlit'
 * chain of the Psychtoolbox-3 imaging pipeline.
 *
 * (c)2007, 2008 by Mario Kleiner, part of PTB-3, licensed to you under GPL v2.
 * See file License.txt in the Psychtoolbox root folder for the license.
 *
 */

#extension GL_ARB_texture_rectangle : enable

uniform sampler2DRect Image;
uniform float         sampleSpacing;

/* Declare external function for color conversion: */
vec4 gammaCorrect3(vec4 incolor);

void main()
{
    /* Get default texel read position (x,y): x is column, y is row of image. */
    vec2 readpos = gl_FragCoord.xy;

    /* Update the s (==column) component to only read even or odd lines, replicating them. */
    readpos.s = (readpos.s - mod(readpos.s, 2.0)) * sampleSpacing;

    /* Retrieve RGBA HDR input color value for a virtual Bits++ pixel. */
    vec4 incolor = texture2DRect(Image, readpos);

    /* Apply some color transformation (clamping, gamma correction etc.): */
    incolor = gammaCorrect3(incolor);

    /* Remap all color channels from 0.0 - 1.0 to 0 to 65535: */
    /* Perform rounding for non-integral numbers and add a small epsilon to take numeric roundoff into account: */
    vec3 index = floor(incolor.rgb * 65535.0 + 0.5) + 0.01;

    /* Compute high bytes (8 MSBs) for all color components. */
    vec3 hibytes = floor(index / 256.0) / 255.0;

    /* Compute low bytes (8 LSBs) for color components. */
    vec3 lobytes = mod(index, 256.0) / 255.0;

    /* Distribution of bytes into output pixel components is dependent */
    /* on our output pixel location. Are we writing an even or odd pixel? */
    if (mod(gl_FragCoord.x, 2.0) < 1.0) {
        /* Even output pixel: */
        gl_FragColor.r = hibytes.r;
        gl_FragColor.g = hibytes.g;
        gl_FragColor.b = hibytes.b;
    }
    else {
        /* Odd output pixel: */
        gl_FragColor.r = lobytes.r;
        gl_FragColor.g = lobytes.g;
        gl_FragColor.b = lobytes.b;
    }

    /* Fix alpha channel to 1.0. */
    gl_FragColor.a = 1.0;
}
""", shaderType=FRAG)