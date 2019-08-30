#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""shaders programs for either pyglet or pygame
"""

from __future__ import absolute_import, print_function

import pyglet.gl as GL
import psychopy.tools.gltools as gltools


def compileProgram(vertexSource=None, fragmentSource=None):
    """Create and compile a vertex and fragment shader pair from their sources.

    Parameters
    ----------
    vertexSource, fragmentSource : str or list of str
        Vertex and fragment shader GLSL sources.

    Returns
    -------
    int
        Program object handle.

    """
    program = gltools.createProgramObjectARB()

    vertexShader = fragmentShader = None
    if vertexSource:
        vertexShader = gltools.compileShaderObjectARB(
            vertexSource, GL.GL_VERTEX_SHADER_ARB)
        gltools.attachObjectARB(program, vertexShader)
    if fragmentSource:
        fragmentShader = gltools.compileShaderObjectARB(
            fragmentSource, GL.GL_FRAGMENT_SHADER_ARB)
        gltools.attachObjectARB(program, fragmentShader)

    gltools.linkProgramObjectARB(program)
    # gltools.validateProgramARB(program)

    if vertexShader:
        gltools.detachObjectARB(program, vertexShader)
        gltools.deleteObjectARB(vertexShader)
    if fragmentShader:
        gltools.detachObjectARB(program, fragmentShader)
        gltools.deleteObjectARB(fragmentShader)

    return program


"""NOTE about frag shaders using FBO. If a floating point texture is being
used as a frame buffer (FBO object) then we should keep in the range -1:1
during frag shader. Otherwise we need to convert to 0:1. This means that
some shaders differ for FBO use if they're performing any signed math.
"""

fragFBOtoFrame = '''
    uniform sampler2D texture;

    float rand(vec2 seed){
        return fract(sin(dot(seed.xy ,vec2(12.9898,78.233))) * 43758.5453);
    }

    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        gl_FragColor.rgb = textureFrag.rgb;
        //! if too high then show red/black noise
        if ( gl_FragColor.r>1.0 || gl_FragColor.g>1.0 || gl_FragColor.b>1.0) {
            gl_FragColor.rgb = vec3 (rand(gl_TexCoord[0].st), 0, 0);
        }
        //! if too low then show red/black noise
        else if ( gl_FragColor.r<0.0 || gl_FragColor.g<0.0 || gl_FragColor.b<0.0) {
            gl_FragColor.rgb = vec3 (0, 0, rand(gl_TexCoord[0].st));
        }
    }
    '''

# for stimuli with no texture (e.g. shapes)
fragSignedColor = '''
    void main() {
        gl_FragColor.rgb = ((gl_Color.rgb*2.0-1.0)+1.0)/2.0;
        gl_FragColor.a = gl_Color.a;
    }
    '''
fragSignedColor_adding = '''
    void main() {
        gl_FragColor.rgb = (gl_Color.rgb*2.0-1.0)/2.0;
        gl_FragColor.a = gl_Color.a;
    }
    '''
# for stimuli with just a colored texture
fragSignedColorTex = '''
    uniform sampler2D texture;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        gl_FragColor.rgb = (textureFrag.rgb* (gl_Color.rgb*2.0-1.0)+1.0)/2.0;
        gl_FragColor.a = gl_Color.a*textureFrag.a;
    }
    '''
fragSignedColorTex_adding = '''
    uniform sampler2D texture;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        gl_FragColor.rgb = textureFrag.rgb * (gl_Color.rgb*2.0-1.0)/2.0;
        gl_FragColor.a = gl_Color.a * textureFrag.a;
    }
    '''
# the shader for pyglet fonts doesn't use multitextures - just one texture
fragSignedColorTexFont = '''
    uniform sampler2D texture;
    uniform vec3 rgb;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        gl_FragColor.rgb=rgb;
        gl_FragColor.a = gl_Color.a*textureFrag.a;
    }
    '''
# for stimuli with a colored texture and a mask (gratings, etc.)
fragSignedColorTexMask = '''
    uniform sampler2D texture, mask;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        vec4 maskFrag = texture2D(mask,gl_TexCoord[1].st);
        gl_FragColor.a = gl_Color.a*maskFrag.a*textureFrag.a;
        gl_FragColor.rgb = (textureFrag.rgb* (gl_Color.rgb*2.0-1.0)+1.0)/2.0;
    }
    '''
fragSignedColorTexMask_adding = '''
    uniform sampler2D texture, mask;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        vec4 maskFrag = texture2D(mask,gl_TexCoord[1].st);
        gl_FragColor.a = gl_Color.a * maskFrag.a * textureFrag.a;
        gl_FragColor.rgb = textureFrag.rgb * (gl_Color.rgb*2.0-1.0)/2.0;
    }
    '''
# RadialStim uses a 1D mask with a 2D texture
fragSignedColorTexMask1D = '''
    uniform sampler2D texture;
    uniform sampler1D mask;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        vec4 maskFrag = texture1D(mask,gl_TexCoord[1].s);
        gl_FragColor.a = gl_Color.a*maskFrag.a*textureFrag.a;
        gl_FragColor.rgb = (textureFrag.rgb* (gl_Color.rgb*2.0-1.0)+1.0)/2.0;
    }
    '''
fragSignedColorTexMask1D_adding = '''
    uniform sampler2D texture;
    uniform sampler1D mask;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        vec4 maskFrag = texture1D(mask,gl_TexCoord[1].s);
        gl_FragColor.a = gl_Color.a * maskFrag.a*textureFrag.a;
        gl_FragColor.rgb = textureFrag.rgb * (gl_Color.rgb*2.0-1.0)/2.0;
    }
    '''
# imageStim is providing its texture unsigned
fragImageStim = '''
    uniform sampler2D texture;
    uniform sampler2D mask;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        vec4 maskFrag = texture2D(mask,gl_TexCoord[1].st);
        gl_FragColor.a = gl_Color.a*maskFrag.a*textureFrag.a;
        gl_FragColor.rgb = ((textureFrag.rgb*2.0-1.0)*(gl_Color.rgb*2.0-1.0)+1.0)/2.0;
    }
    '''
# imageStim is providing its texture unsigned
fragImageStim_adding = '''
    uniform sampler2D texture;
    uniform sampler2D mask;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        vec4 maskFrag = texture2D(mask,gl_TexCoord[1].st);
        gl_FragColor.a = gl_Color.a*maskFrag.a*textureFrag.a;
        gl_FragColor.rgb = (textureFrag.rgb*2.0-1.0)*(gl_Color.rgb*2.0-1.0)/2.0;
    }
    '''
# in every case our vertex shader is simple (we don't transform coords)
vertSimple = """
    void main() {
            gl_FrontColor = gl_Color;
            gl_TexCoord[0] = gl_MultiTexCoord0;
            gl_TexCoord[1] = gl_MultiTexCoord1;
            gl_TexCoord[2] = gl_MultiTexCoord2;
            gl_Position =  ftransform();
    }
    """
