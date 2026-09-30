#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""shaders programs for either pyglet or pygame
"""

import psychopy.tools.pygletgl as GL
import psychopy.tools.gltools as gltools
from ctypes import c_int, c_char_p, c_char, cast, POINTER, byref

# for backwards compatibility with legacy (fixed-function) OpenGL
USE_LEGACY_GL = GL.USE_LEGACY_GL

# Vertex attributes the non-legacy shaders read, bound to the locations that
# `gltools.drawClientArrays` and `gltools.createVAO` use for 'gl_Vertex',
# 'gl_Normal', 'gl_Color' and 'gl_MultiTexCoord0/1'.
_ATTRIB_LOCATIONS = {
    'aPosition': gltools.VERTEX_ATTRIB_POSITION,
    'aNormal': gltools.VERTEX_ATTRIB_NORMAL,
    'aColor': gltools.VERTEX_ATTRIB_COLOR,
    'aTexCoord0': gltools.VERTEX_ATTRIB_MULTITEXCOORD0,
    'aTexCoord1': gltools.VERTEX_ATTRIB_MULTITEXCOORD1,
}


def _addPreamble(source, shaderType):
    """Prefix non-legacy shader source with a preamble for the current context.

    The non-legacy shaders are written to compile as either GLSL 3.30 (core
    profile contexts, e.g. with pyglet 2+ on macOS) or GLSL 1.20 (legacy
    contexts older than OpenGL 3.3, e.g. with pyglet 1.x on macOS). Their
    sources use `ATTRIB` and `VARYING` for inputs and outputs, `fragColor` for
    the fragment color, and `texture1D`, `texture2D` or `textureCube` to
    sample textures.

    Parameters
    ----------
    source : str or list of str
        GLSL source.
    shaderType : int
        Shader type, either `GL_VERTEX_SHADER` or `GL_FRAGMENT_SHADER`.

    Returns
    -------
    str or list of str
        Source with the preamble, the same type as `source`.

    """
    if GL.gl_info.have_version(3, 3):
        lines = [
            '#version 330 core',
            '#define ATTRIB in',
            '#define texture1D texture',
            '#define texture2D texture',
            '#define textureCube texture']
        if shaderType == GL.GL_VERTEX_SHADER:
            lines.append('#define VARYING out')
        else:
            lines += ['#define VARYING in', 'out vec4 fragColor;']
    else:
        lines = [
            '#version 120',
            '#define ATTRIB attribute',
            '#define VARYING varying',
            '#define fragColor gl_FragColor']

    preamble = '\n'.join(lines) + '\n'
    if isinstance(source, (list, tuple)):
        return [preamble] + list(source)

    return preamble + source


class Shader:
    def __init__(self, vertexSource=None, fragmentSource=None):
        if not USE_LEGACY_GL:
            self.handle = compileProgram(vertexSource, fragmentSource)
            return

        def compileShader(source, shaderType):
            """Compile shader source of given type (only needed by compileProgram)
            """
            shader = GL.glCreateShader(shaderType)
            # if Py3 then we need to convert our (unicode) str into bytes for C
            if type(source) != bytes:
                source = source.encode()
            prog = c_char_p(source)
            length = c_int(-1)
            GL.glShaderSource(
                shader, 
                1,
                cast(byref(prog), POINTER(POINTER(c_char))),
                byref(length))
            GL.glCompileShader(shader)

            # check for errors
            status = c_int()
            GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS, byref(status))
            if not status.value:
                GL.glDeleteShader(shader)
                raise ValueError('Shader compilation failed')
            return shader

        self.handle = GL.glCreateProgram()

        if vertexSource:
            vertexShader = compileShader(
                vertexSource, GL.GL_VERTEX_SHADER
            )
            GL.glAttachShader(self.handle, vertexShader)
        if fragmentSource:
            fragmentShader = compileShader(
                fragmentSource, GL.GL_FRAGMENT_SHADER
            )
            GL.glAttachShader(self.handle, fragmentShader)

        GL.glValidateProgram(self.handle)
        GL.glLinkProgram(self.handle)

        if vertexShader:
            GL.glDeleteShader(vertexShader)
        if fragmentShader:
            GL.glDeleteShader(fragmentShader)

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

    With non-legacy OpenGL (`USE_LEGACY_GL` is `False`), the sources are
    prefixed with a preamble for the current context (see `_addPreamble`) and
    vertex attributes are bound to the locations in `_ATTRIB_LOCATIONS`.

    Parameters
    ----------
    vertexSource, fragmentSource : str or list of str
        Vertex and fragment shader GLSL sources.

    Returns
    -------
    int
        Program object handle.

    """
    program = gltools.createProgram()

    vertexShader = fragmentShader = None
    if vertexSource:
        if not USE_LEGACY_GL:
            vertexSource = _addPreamble(vertexSource, GL.GL_VERTEX_SHADER)
        vertexShader = gltools.compileShader(
            vertexSource, GL.GL_VERTEX_SHADER)
        gltools.attachShader(program, vertexShader)
    if fragmentSource:
        if not USE_LEGACY_GL:
            fragmentSource = _addPreamble(fragmentSource, GL.GL_FRAGMENT_SHADER)
        fragmentShader = gltools.compileShader(
            fragmentSource, GL.GL_FRAGMENT_SHADER)
        gltools.attachShader(program, fragmentShader)

    if not USE_LEGACY_GL:
        # must be done before linking, names the shader doesn't use are ignored
        for name, location in _ATTRIB_LOCATIONS.items():
            GL.glBindAttribLocation(program, location, name.encode())

    gltools.linkProgram(program)
    # gltools.validateProgramARB(program)

    if vertexShader:
        gltools.detachShader(program, vertexShader)
        gltools.deleteObject(vertexShader)
    if fragmentShader:
        gltools.detachShader(program, fragmentShader)
        gltools.deleteObject(fragmentShader)

    return program


"""NOTE about frag shaders using FBO. If a floating point texture is being
used as a frame buffer (FBO object) then we should keep in the range -1:1
during frag shader. Otherwise we need to convert to 0:1. This means that
some shaders differ for FBO use if they're performing any signed math.
"""

if USE_LEGACY_GL:
    fragFBOtoFrame = """
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
        """

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

            float coverage = (current.r + current.g + current.b) / 3.;
            coverage = clamp(coverage, 0.0, 1.0);
            gl_FragColor = vec4(gl_Color.rgb, gl_Color.a * coverage);
        }
        '''
    fragTextBox2_adding = '''
        uniform sampler2D texture;
        void main() {
            vec2 uv      = gl_TexCoord[0].xy;
            vec4 current = texture2D(texture, uv);

            float coverage = (current.r + current.g + current.b) / 3.;
            coverage = clamp(coverage, 0.0, 1.0);
            gl_FragColor = vec4((gl_Color.rgb * 2.0 - 1.0) / 2.0,
                                gl_Color.a * coverage);
        }
        '''
    fragTextBox2alpha = '''
        uniform sampler2D texture;
        void main() {
            vec4 current = texture2D(texture,gl_TexCoord[0].st);

            gl_FragColor = vec4(gl_Color.rgb, gl_Color.a * current.a);
        }
        '''
    fragTextBox2alpha_adding = '''
        uniform sampler2D texture;
        void main() {
            vec4 current = texture2D(texture,gl_TexCoord[0].st);

            gl_FragColor = vec4((gl_Color.rgb * 2.0 - 1.0) / 2.0,
                                gl_Color.a * current.a);
        }
        '''
else:
    # Sources are prefixed by `_addPreamble()` when compiled, so they work as
    # GLSL 3.30 (core profile) or GLSL 1.20. Vertex attributes are bound to the
    # locations in `_ATTRIB_LOCATIONS`.

    # for stimuli with no texture (e.g. shapes)
    fragSignedColor = """
        uniform vec4 uColor;
        void main() {
            fragColor.rgb = ((uColor.rgb * 2.0 - 1.0) + 1.0) / 2.0;
            fragColor.a = uColor.a;
        }
        """
    fragSignedColor_adding = """
        uniform vec4 uColor;
        void main() {
            fragColor.rgb = (uColor.rgb * 2.0 - 1.0) / 2.0;
            fragColor.a = uColor.a;
        }
        """
    # for stimuli with just a colored texture
    fragSignedColorTex = """
        uniform vec4 uColor;
        uniform sampler2D uTexture;
        VARYING vec4 vTexCoord0;
        void main() {
            vec4 textureFrag = texture2D(uTexture, vTexCoord0.st);
            fragColor.rgb = (textureFrag.rgb * (uColor.rgb * 2.0 - 1.0) + 1.0) / 2.0;
            fragColor.a = uColor.a * textureFrag.a;
        }
        """
    fragSignedColorTex_adding = """
        uniform vec4 uColor;
        uniform sampler2D uTexture;
        VARYING vec4 vTexCoord0;
        void main() {
            vec4 textureFrag = texture2D(uTexture, vTexCoord0.st);
            fragColor.rgb = textureFrag.rgb * (uColor.rgb * 2.0 - 1.0) / 2.0;
            fragColor.a = uColor.a * textureFrag.a;
        }
        """
    # the shader for pyglet fonts doesn't use multitextures - just one texture
    fragSignedColorTexFont = """
        uniform sampler2D uTexture;
        uniform vec3 rgb;
        VARYING vec4 vColor;
        VARYING vec4 vTexCoord0;
        void main() {
            vec4 textureFrag = texture2D(uTexture, vTexCoord0.st);
            fragColor.rgb = rgb;
            fragColor.a = vColor.a * textureFrag.a;
        }
    """

    # for stimuli with a colored texture and a mask (gratings, etc.)
    fragSignedColorTexMask = """
        uniform vec4 uColor;
        uniform sampler2D uTexture, uMask;
        VARYING vec4 vTexCoord0;
        VARYING vec4 vTexCoord1;
        void main() {
            vec4 textureFrag = texture2D(uTexture, vTexCoord0.st);
            vec4 maskFrag = texture2D(uMask, vTexCoord1.st);
            fragColor.a = uColor.a * maskFrag.a * textureFrag.a;
            fragColor.rgb = (textureFrag.rgb * (uColor.rgb * 2.0 - 1.0) + 1.0) / 2.0;
        }
        """
    fragSignedColorTexMask_adding = """
        uniform vec4 uColor;
        uniform sampler2D uTexture, uMask;
        VARYING vec4 vTexCoord0;
        VARYING vec4 vTexCoord1;
        void main() {
            vec4 textureFrag = texture2D(uTexture, vTexCoord0.st);
            vec4 maskFrag = texture2D(uMask, vTexCoord1.st);
            fragColor.a = uColor.a * maskFrag.a * textureFrag.a;
            fragColor.rgb = textureFrag.rgb * (uColor.rgb * 2.0 - 1.0) / 2.0;
        }
        """
    # RadialStim uses a 1D mask with a 2D texture
    fragSignedColorTexMask1D = """
        uniform vec4 uColor;
        uniform sampler2D uTexture;
        uniform sampler1D uMask;
        VARYING vec4 vTexCoord0;
        VARYING vec4 vTexCoord1;
        void main() {
            vec4 textureFrag = texture2D(uTexture, vTexCoord0.st);
            vec4 maskFrag = texture1D(uMask, vTexCoord1.s);
            fragColor.a = uColor.a * maskFrag.a * textureFrag.a;
            fragColor.rgb = (textureFrag.rgb * (uColor.rgb * 2.0 - 1.0) + 1.0) / 2.0;
        }
        """
    fragSignedColorTexMask1D_adding = """
        uniform vec4 uColor;
        uniform sampler2D uTexture;
        uniform sampler1D uMask;
        VARYING vec4 vTexCoord0;
        VARYING vec4 vTexCoord1;
        void main() {
            vec4 textureFrag = texture2D(uTexture, vTexCoord0.st);
            vec4 maskFrag = texture1D(uMask, vTexCoord1.s);
            fragColor.a = uColor.a * maskFrag.a * textureFrag.a;
            fragColor.rgb = textureFrag.rgb * (uColor.rgb * 2.0 - 1.0) / 2.0;
        }
        """
    # imageStim is providing its texture unsigned
    fragImageStim = """
        uniform vec4 uColor;
        uniform sampler2D uTexture;
        uniform sampler2D uMask;
        VARYING vec4 vTexCoord0;
        VARYING vec4 vTexCoord1;

        void main() {
            vec4 textureFrag = texture2D(uTexture, vTexCoord0.st);
            vec4 maskFrag = texture2D(uMask, vTexCoord1.st);
            fragColor.a = uColor.a * maskFrag.a * textureFrag.a;
            fragColor.rgb = ((textureFrag.rgb * 2.0 - 1.0) * (uColor.rgb * 2.0 - 1.0) + 1.0) / 2.0;
        }
        """
    # imageStim is providing its texture unsigned
    fragImageStim_adding = """
        uniform vec4 uColor;
        uniform sampler2D uTexture;
        uniform sampler2D uMask;
        VARYING vec4 vTexCoord0;
        VARYING vec4 vTexCoord1;

        void main() {
            vec4 textureFrag = texture2D(uTexture, vTexCoord0.st);
            vec4 maskFrag = texture2D(uMask, vTexCoord1.st);
            fragColor.a = uColor.a * maskFrag.a * textureFrag.a;
            fragColor.rgb = (textureFrag.rgb * 2.0 - 1.0) * (uColor.rgb * 2.0 - 1.0) / 2.0;
        }
        """
    # copies the FBO to the back buffer
    fragFBOtoFrame = """
        uniform sampler2D uTexture;
        VARYING vec4 vTexCoord0;

        float rand(vec2 seed){
            return fract(sin(dot(seed.xy ,vec2(12.9898,78.233))) * 43758.5453);
        }

        void main() {
            vec4 textureFrag = texture2D(uTexture, vTexCoord0.st);
            fragColor.rgb = textureFrag.rgb;
            //! if too high then show red/black noise
            if ( fragColor.r>1.0 || fragColor.g>1.0 || fragColor.b>1.0) {
                fragColor.rgb = vec3 (rand(vTexCoord0.st), 0, 0);
            }
            //! if too low then show red/black noise
            else if ( fragColor.r<0.0 || fragColor.g<0.0 || fragColor.b<0.0) {
                fragColor.rgb = vec3 (0, 0, rand(vTexCoord0.st));
            }
        }
        """

    # vertex shader for pyglet text rendering, with per-vertex colors
    vertSimpleText = """
        ATTRIB vec4 aPosition;
        ATTRIB vec4 aColor;
        ATTRIB vec4 aTexCoord0;
        uniform mat4 uModelViewMatrix;  // combined for 2D rendering
        uniform mat4 uProjectionMatrix;
        VARYING vec4 vColor;
        VARYING vec4 vTexCoord0;
        void main() {
                vColor = aColor;
                vTexCoord0 = aTexCoord0;
                gl_Position = uProjectionMatrix * uModelViewMatrix * aPosition;
        }
        """

    vertSimple = """
        ATTRIB vec4 aPosition;
        ATTRIB vec4 aTexCoord0;
        ATTRIB vec4 aTexCoord1;
        uniform mat4 uModelViewMatrix;  // combined for 2D rendering
        uniform mat4 uProjectionMatrix;
        VARYING vec4 vTexCoord0;
        VARYING vec4 vTexCoord1;
        void main() {
                vTexCoord0 = aTexCoord0;
                vTexCoord1 = aTexCoord1;
                gl_Position = uProjectionMatrix * uModelViewMatrix * aPosition;
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
    ATTRIB vec4 aPosition;
    ATTRIB vec3 aNormal;
    ATTRIB vec4 aTexCoord0;
    uniform mat4 uModelViewMatrix;
    uniform mat4 uProjectionMatrix;
    uniform mat4 uNormalMatrix;
    VARYING vec3 N;
    VARYING vec3 v;
    VARYING vec4 vTexCoord0;

    void main(void)
    {
        v = vec3(uModelViewMatrix * aPosition);
        N = normalize(mat3(uNormalMatrix) * aNormal);

        vTexCoord0 = aTexCoord0;
        gl_Position = uProjectionMatrix * uModelViewMatrix * aPosition;
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
    // Lights and materials are uniforms mirroring the fixed-function OpenGL state
    // (`gl_LightSource`, `gl_FrontMaterial` and `gl_LightModel`), which isn't
    // available with core profile contexts. Light positions are in eye space.
    //
    struct LightSource {
        vec4 ambient;
        vec4 diffuse;
        vec4 specular;
        vec4 position;
        float constantAttenuation;
        float linearAttenuation;
        float quadraticAttenuation;
    };

    struct Material {
        vec4 ambient;
        vec4 diffuse;
        vec4 specular;
        vec4 emission;
        float shininess;
    };

    // without lights, light 0's ambient color is still used, as with the
    // fixed-function pipeline
    #if MAX_LIGHTS > 0
        uniform LightSource uLightSource[MAX_LIGHTS];
    #else
        uniform LightSource uLightSource[1];
    #endif
    uniform Material uFrontMaterial;
    uniform vec4 uLightModelAmbient;

    VARYING vec3 N;
    VARYING vec3 v;
    VARYING vec4 vTexCoord0;

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
        vec4 diffTexColor = texture2D(diffTexture, vTexCoord0.st);
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
            if (uLightSource[i].position.w == 0.0)
            {
                // off at infinity, only use direction
                L = normalize(uLightSource[i].position.xyz);
                // attenuation is 1.0 (no attenuation for directional sources)
            }
            else
            {
                L = normalize(uLightSource[i].position.xyz - v);
                attenuation = calcAttenuation(
                    uLightSource[i].constantAttenuation,
                    uLightSource[i].linearAttenuation,
                    uLightSource[i].quadraticAttenuation,
                    length(uLightSource[i].position.xyz - v));
            }

            vec3 E = normalize(-v);
            vec3 R = normalize(-reflect(L, N));

            // combine scene ambient with object
            vec4 ambient = uFrontMaterial.diffuse *
                (uFrontMaterial.ambient * uLightSource[i].ambient + uLightModelAmbient);

            // calculate diffuse component
            vec4 diffuse = uFrontMaterial.diffuse * uLightSource[i].diffuse * max(dot(N, L), 0.0);
    #ifdef DIFFUSE_TEXTURE
            // multiply in material texture colors if specified
            diffuse *= diffTexColor;
            ambient *= diffTexColor;  // ambient should be modulated by diffuse color
    #endif
            vec3 halfwayVec = normalize(L + E);
            vec4 specular = uFrontMaterial.specular * uLightSource[i].specular *
                pow(max(dot(N, halfwayVec), 0.0), uFrontMaterial.shininess);

            // clamp color values for specular and diffuse
            ambient = clamp(ambient, 0.0, 1.0);
            diffuse = clamp(diffuse, 0.0, 1.0);
            specular = clamp(specular, 0.0, 1.0);

            // falloff with distance from eye? might be something to consider for
            // realism
            vec4 emission = clamp(uFrontMaterial.emission, 0.0, 1.0);

            finalColor += (ambient + emission) + attenuation * (diffuse + specular);
        }
        fragColor = finalColor;  // use texture alpha
    #else
        // no lights, only track ambient and emission component
        vec4 emission = clamp(uFrontMaterial.emission, 0.0, 1.0);
        vec4 ambient = uFrontMaterial.ambient * uLightSource[0].ambient * uLightModelAmbient;
        ambient = clamp(ambient, 0.0, 1.0);
    #ifdef DIFFUSE_TEXTURE
        fragColor = (ambient + emission) * texture2D(diffTexture, vTexCoord0.st);
    #else
        fragColor = ambient + emission;
    #endif
    #endif
    }
    """

    vertSkyBox = """
    ATTRIB vec4 aPosition;
    uniform mat4 uModelViewMatrix;
    uniform mat4 uProjectionMatrix;
    VARYING vec3 texCoord;
    void main(void)
    {
        texCoord = aPosition.xyz;
        gl_Position = (uProjectionMatrix * uModelViewMatrix * aPosition).xyww;
    }
    """

    fragSkyBox = """
    VARYING vec3 texCoord;
    uniform samplerCube SkyTexture;
    void main (void)
    {
        fragColor = textureCube(SkyTexture, texCoord);
    }
    """
    fragTextBox2 = '''
    uniform sampler2D uTexture;
    uniform vec4 uColor;
    VARYING vec4 vTexCoord0;
    void main()
    {
        vec2 uv      = vTexCoord0.xy;
        vec4 current = texture2D(uTexture, uv);

        float coverage = (current.r + current.g + current.b) / 3.;
        coverage = clamp(coverage, 0.0, 1.0);
        fragColor = vec4(uColor.rgb, uColor.a * coverage);
    }
    '''
    fragTextBox2_adding = '''
    uniform sampler2D uTexture;
    uniform vec4 uColor;
    VARYING vec4 vTexCoord0;
    void main()
    {
        vec2 uv      = vTexCoord0.xy;
        vec4 current = texture2D(uTexture, uv);

        float coverage = (current.r + current.g + current.b) / 3.;
        coverage = clamp(coverage, 0.0, 1.0);
        fragColor = vec4((uColor.rgb * 2.0 - 1.0) / 2.0,
                         uColor.a * coverage);
    }
    '''
    fragTextBox2alpha = '''
    uniform sampler2D uTexture;
    uniform vec4 uColor;
    VARYING vec4 vTexCoord0;
    void main()
    {
        vec4 current = texture2D(uTexture, vTexCoord0.st);

        fragColor = vec4(uColor.rgb, uColor.a * current.a);
    }
    '''
    fragTextBox2alpha_adding = '''
    uniform sampler2D uTexture;
    uniform vec4 uColor;
    VARYING vec4 vTexCoord0;
    void main()
    {
        vec4 current = texture2D(uTexture, vTexCoord0.st);

        fragColor = vec4((uColor.rgb * 2.0 - 1.0) / 2.0,
                         uColor.a * current.a);
    }
    '''
