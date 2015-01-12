# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from OpenGL.GL import *
from OpenGL.GL.ARB.shader_objects import *
from OpenGL.GL.ARB.fragment_shader import *
from OpenGL.GL.ARB.vertex_shader import *
import time, sys
from OpenGL.extensions import alternate
glCreateShader = alternate( 'glCreateShader', glCreateShader, glCreateShaderObjectARB )
glShaderSource = alternate( 'glShaderSource', glShaderSource, glShaderSourceARB)
glCompileShader = alternate( 'glCompileShader', glCompileShader, glCompileShaderARB)
glCreateProgram = alternate( 'glCreateProgram', glCreateProgram, glCreateProgramObjectARB)
glAttachShader = alternate( 'glAttachShader', glAttachShader,glAttachObjectARB )
glValidateProgram = alternate( 'glValidateProgram',glValidateProgram,glValidateProgramARB )
glLinkProgram = alternate( 'glLinkProgram',glLinkProgram,glLinkProgramARB )
glDeleteShader = alternate( 'glDeleteShader', glDeleteShader,glDeleteObjectARB )
glUseProgram = alternate('glUseProgram',glUseProgram,glUseProgramObjectARB )

def compileShader( source, shaderType ):
    """Compile shader source of given type"""
    shader = glCreateShader(shaderType)
    glShaderSource( shader, source )
    glCompileShader( shader )
    return shader


def compileProgram(vertexSource=None, fragmentSource=None):
    program = glCreateProgram()

    if vertexSource:
        vertexShader = compileShader(
            [vertexSource,], GL_VERTEX_SHADER_ARB
        )
        glAttachShader(program, vertexShader)
    if fragmentSource:
        fragmentShader = compileShader(
            [fragmentSource,], GL_FRAGMENT_SHADER_ARB
        )
        glAttachShader(program, fragmentShader)

    glValidateProgram( program )
    glLinkProgram(program)

    if vertexShader:
        glDeleteShader(vertexShader)
    if fragmentShader:
        glDeleteShader(fragmentShader)

    return program

fragSignedColorTex = '''
    // Fragment program
    uniform sampler2D texture;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        gl_FragColor.rgb = (textureFrag.rgb* (gl_Color.rgb*2.0-1)+1)/2;        
        gl_FragColor.a = gl_Color.a*textureFrag.a;
    }
    '''
fragSignedColorTexMask = '''
    // Fragment program
    uniform sampler2D texture, mask;
    void main() {
        vec4 textureFrag = texture2D(texture,gl_TexCoord[0].st);
        vec4 maskFrag = texture2D(mask,gl_TexCoord[1].st);
        gl_FragColor.rgb = (textureFrag.rgb* (gl_Color.rgb*2.0-1)+1)/2;        
        gl_FragColor.a = gl_Color.a*maskFrag.a;
    }
    '''
vertSimple = """
    void main() {               
            gl_FrontColor = gl_Color;
            gl_TexCoord[0] = gl_MultiTexCoord0;
            gl_TexCoord[1] = gl_MultiTexCoord1;
            gl_TexCoord[2] = gl_MultiTexCoord2;
            gl_Position =  ftransform();
    }
    """
cartoonVertexSource = '''
    // Vertex program    
    varying vec3 normal;
    void main() {
        normal = gl_NormalMatrix * gl_Normal;
        gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    }
    '''
cartoonFragSource = '''
    // Fragment program    
    varying vec3 normal;
    void main() {
        float intensity;
        vec4 color;
        vec3 n = normalize(normal);
        vec3 l = normalize(gl_LightSource[0].position).xyz;
 
        // quantize to 5 steps (0, .25, .5, .75 and 1)
        intensity = (floor(dot(l, n) * 4.0) + 1.0)/4.0;
        color = vec4(intensity*1.0, intensity*0.5, intensity*0.5,
            intensity*1.0);
 
        gl_FragColor = color;
    }
    '''

expoShaderTxt="""
!!ARBfp1.0

# Texture units:
#   0 - pattern texture
#   1 - surface mask texture
#   2 - overlay texture

ATTRIB pattern    = fragment.texcoord[0];
ATTRIB surfacemask    = fragment.texcoord[1];
ATTRIB overlaypattern = fragment.texcoord[2];

# Offset & scale constants
PARAM  offset    = { 0.5, 0.5, 0.5, 0.0 };
PARAM  gain    = { 2.0, 2.0, 2.0, 1.0 };
PARAM  contrast    = program.local[0];
PARAM  ocontrast = program.local[1];

# temp registers
TEMP t0, t1, t2;

# Get the current textel values into registers
TEX t0, pattern, texture[0], 2D;
TEX t1, surfacemask, texture[1], 2D;
TEX t2, overlaypattern, texture[2], 2D;

# Combine values
SUB t2.rgb, t2, offset;        # make signed overlay texture
MUL t2, t2, ocontrast;        # multiply texture and contrast (including alpha)

SUB t0.rgb, t0, offset;        # make signed pattern texture value
MUL t0, t0, contrast;        # multiply texture and contrast (including alpha)

MUL t0.rgb, t0, gain;        # x 2, anticipating 0.5 x 0.5 texture multiplication

MUL t0.a, t0, t1;            # multiply base texture by surface mask (currently only alpha [later for lum-alpha])
MAD result.color, t0, t2, offset;   # multiply base and overlay, restore offset

END

"""
