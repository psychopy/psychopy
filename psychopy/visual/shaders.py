#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""shaders programs for either pyglet or pygame
"""

import pyglet.gl as GL
import psychopy.tools.gltools as gltools
from ctypes import c_int, c_char_p, c_char, cast, POINTER, byref


class Shader:
    def __init__(self, vertexSource=None, fragmentSource=None):

        def compileShader(source, shaderType):
            """Compile shader source of given type (only needed by compileProgram)
            """
            shader = GL.glCreateShaderObjectARB(shaderType)
            # if Py3 then we need to convert our (unicode) str into bytes for C
            if type(source) != bytes:
                source = source.encode()
            prog = c_char_p(source)
            length = c_int(-1)
            GL.glShaderSourceARB(shader,
                                 1,
                                 cast(byref(prog), POINTER(POINTER(c_char))),
                                 byref(length))
            GL.glCompileShaderARB(shader)

            # check for errors
            status = c_int()
            GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS, byref(status))
            if not status.value:
                GL.glDeleteShader(shader)
                raise ValueError('Shader compilation failed')
            return shader

        self.handle = GL.glCreateProgramObjectARB()

        if vertexSource:
            vertexShader = compileShader(
                vertexSource, GL.GL_VERTEX_SHADER_ARB
            )
            GL.glAttachObjectARB(self.handle, vertexShader)
        if fragmentSource:
            fragmentShader = compileShader(
                fragmentSource, GL.GL_FRAGMENT_SHADER_ARB
            )
            GL.glAttachObjectARB(self.handle, fragmentShader)

        GL.glValidateProgramARB(self.handle)
        GL.glLinkProgramARB(self.handle)

        if vertexShader:
            GL.glDeleteObjectARB(vertexShader)
        if fragmentShader:
            GL.glDeleteObjectARB(fragmentShader)

    def bind(self):
        GL.glUseProgram(self.handle)

    def unbind(self):
        GL.glUseProgram(0)

    def setFloat(self, name, value):
        if type(name) is not bytes:
            name = bytes(name, 'utf-8')
        loc = GL.glGetUniformLocation(self.handle, name)
        if not hasattr(value, '__len__'):
            GL.glUniform1f(loc, value)
        elif len(value) in range(1, 5):
            # Select the correct function
            { 1 : GL.glUniform1f,
              2 : GL.glUniform2f,
              3 : GL.glUniform3f,
              4 : GL.glUniform4f
              # Retrieve uniform location, and set it
            }[len(value)](loc, *value)
        else:
            raise ValueError("Shader.setInt '{}' should be length 1-4 not {}"
                             .format(name, len(value)))

    def setInt(self, name, value):
        if type(name) is not bytes:
            name = bytes(name, 'utf-8')
        loc = GL.glGetUniformLocation(self.handle, name)
        if not hasattr(value, '__len__'):
            GL.glUniform1i(loc, value)
        elif len(value) in range(1, 5):
            # Select the correct function
            { 1 : GL.glUniform1i,
              2 : GL.glUniform2i,
              3 : GL.glUniform3i,
              4 : GL.glUniform4i
              # Retrieve uniform location, and set it
            }[len(value)](loc, value)
        else:
            raise ValueError("Shader.setInt '{}' should be length 1-4 not {}"
                             .format(name, len(value)))


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

vertPhongLighting = """
// Vertex shader for the Phong Shading Model
// 
// This code is based of the tutorial here:
//     https://www.opengl.org/sdk/docs/tutorials/ClockworkCoders/lighting.php
//
// Only supports directional and point light sources for now. Spotlights will be
// added later on.
//
#version 110
varying vec3 N;
varying vec3 v;
varying vec4 frontColor;

void main(void)  
{     
    v = vec3(gl_ModelViewMatrix * gl_Vertex);       
    N = normalize(gl_NormalMatrix * gl_Normal);
    
    gl_TexCoord[0] = gl_MultiTexCoord0;
    gl_TexCoord[1] = gl_MultiTexCoord1;
    gl_Position = ftransform();
    frontColor = gl_Color;
}
          
"""

fragPhongLighting = """
// Fragment shader for the Phong Shading Model
// 
// This code is based of the tutorial here:
//     https://www.opengl.org/sdk/docs/tutorials/ClockworkCoders/lighting.php
//
// Use `embedShaderSourceDefs` from gltools to enable the code path for diffuse 
// texture maps by setting DIFFUSE to 1. The number of lights can be specified 
// by setting MAX_LIGHTS, by default, the maximum should be 8. However, build
// your shader for the exact number of lights required. 
//
// Only supports directional and point light sources for now. Spotlights will be
// added later on.
//
#version 110
varying vec3 N;
varying vec3 v; 
varying vec4 frontColor;

#ifdef DIFFUSE_TEXTURE
    uniform sampler2D diffTexture;
#endif

// Calculate lighting attenuation using the same formula OpenGL uses
float calcAttenuation(float kConst, float kLinear, float kQuad, float dist) {
    return 1.0 / (kConst + kLinear * dist + kQuad * dist * dist);
}

void main (void)  
{  
#ifdef DIFFUSE_TEXTURE
    vec4 diffTexColor = texture2D(diffTexture, gl_TexCoord[0].st);
#endif 

#if MAX_LIGHTS > 0
    vec3 N = normalize(N);
    vec4 finalColor = vec4(0.0);
    // loop over available lights
    for (int i=0; i < MAX_LIGHTS; i++)
    {
        vec3 L;
        float attenuation = 1.0;  // default factor, no attenuation
        
        // check if directional, compute attenuation if a point source
        if (gl_LightSource[i].position.w == 0.0) 
        {
            // off at infinity, only use direction
            L = normalize(gl_LightSource[i].position.xyz);
            // attenuation is 1.0 (no attenuation for directional sources)
        } 
        else 
        {
            L = normalize(gl_LightSource[i].position.xyz - v);
            attenuation = calcAttenuation(
                gl_LightSource[i].constantAttenuation,
                gl_LightSource[i].linearAttenuation,
                gl_LightSource[i].quadraticAttenuation,
                length(gl_LightSource[i].position.xyz - v));
        }
        
        vec3 E = normalize(-v);
        vec3 R = normalize(-reflect(L, N)); 
        
        // combine scene ambient with object
        vec4 ambient = gl_FrontMaterial.diffuse * 
            (gl_FrontLightProduct[i].ambient + gl_LightModel.ambient); 
        
        // calculate diffuse component
        vec4 diffuse = gl_FrontLightProduct[i].diffuse * max(dot(N, L), 0.0);
#ifdef DIFFUSE_TEXTURE
        // multiply in material texture colors if specified
        diffuse *= diffTexColor;
        ambient *= diffTexColor;  // ambient should be modulated by diffuse color
#endif
        vec3 halfwayVec = normalize(L + E);
        vec4 specular = gl_FrontLightProduct[i].specular *
            pow(max(dot(N, halfwayVec), 0.0), gl_FrontMaterial.shininess);

        // clamp color values for specular and diffuse
        ambient = clamp(ambient, 0.0, 1.0); 
        diffuse = clamp(diffuse, 0.0, 1.0); 
        specular = clamp(specular, 0.0, 1.0); 
        
        // falloff with distance from eye? might be something to consider for 
        // realism
        vec4 emission = clamp(gl_FrontMaterial.emission, 0.0, 1.0);
        
        finalColor += (ambient + emission) + attenuation * (diffuse + specular);
    }
    gl_FragColor = finalColor;  // use texture alpha
#else
    // no lights, only track ambient and emission component
    vec4 emission = clamp(gl_FrontMaterial.emission, 0.0, 1.0);
    vec4 ambient = gl_FrontLightProduct[0].ambient * gl_LightModel.ambient; 
    ambient = clamp(ambient, 0.0, 1.0); 
#ifdef DIFFUSE_TEXTURE
    gl_FragColor = (ambient + emission) * texture2D(diffTexture, gl_TexCoord[0].st);
#else
    gl_FragColor = ambient + emission;
#endif
#endif
}
"""

vertSkyBox = """
varying vec3 texCoord;
void main(void)  
{   
    texCoord = gl_Vertex;
    gl_Position = ftransform().xyww;
}      
"""

fragSkyBox = """
varying vec3 texCoord;
uniform samplerCube SkyTexture;
void main (void)  
{  
    gl_FragColor = texture(SkyTexture, texCoord);
}
"""

fragTextBox2 = '''
    uniform sampler2D texture;
    void main() {
        vec2 uv      = gl_TexCoord[0].xy;
        vec4 current = texture2D(texture, uv);

        float r = current.r;
        float g = current.g;
        float b = current.b;
        float a = current.a;
        gl_FragColor = vec4( gl_Color.rgb, (r+g+b)/2.);
    }
    '''
fragTextBox2alpha = '''
    uniform sampler2D texture;
    void main() {
        vec4 current = texture2D(texture,gl_TexCoord[0].st);
        gl_FragColor = vec4( gl_Color.rgb, current.a);
    }
    '''
