:mod:`psychopy.tools.gltools`
-----------------------------

.. automodule:: psychopy.tools.gltools
.. currentmodule:: psychopy.tools.gltools

Shaders
~~~~~~~

Tools for creating, compiling, using, and inspecting shader programs.

.. autofunction:: createProgram
.. autofunction:: createProgramObjectARB
.. autofunction:: compileShader
.. autofunction:: compileShaderObjectARB
.. autofunction:: embedShaderSourceDefs
.. autofunction:: deleteObject
.. autofunction:: deleteObjectARB
.. autofunction:: attachShader
.. autofunction:: attachObjectARB
.. autofunction:: detachShader
.. autofunction:: detachObjectARB
.. autofunction:: linkProgram
.. autofunction:: linkProgramObjectARB
.. autofunction:: validateProgram
.. autofunction:: validateProgramARB
.. autofunction:: useProgram
.. autofunction:: useProgramObjectARB
.. autofunction:: getInfoLog
.. autofunction:: getUniformLocations
.. autofunction:: getAttribLocations

Query
~~~~~

Tools for using OpenGL query objects.

.. autofunction:: createQueryObject
.. autofunction:: QueryObjectInfo
.. autofunction:: beginQuery
.. autofunction:: endQuery
.. autofunction:: getQuery
.. autofunction:: getAbsTimeGPU

Framebuffer Objects (FBO)
~~~~~~~~~~~~~~~~~~~~~~~~~

Tools for creating Framebuffer Objects (FBOs).

.. autofunction:: createFBO
.. autofunction:: attach
.. autofunction:: deleteFBO
.. autofunction:: blitFBO
.. autofunction:: useFBO

Renderbuffers
~~~~~~~~~~~~~

Tools for creating Renderbuffers.

.. autofunction:: createRenderbuffer
.. autofunction:: deleteRenderbuffer


Textures
~~~~~~~~

Tools for creating textures.

.. autofunction:: createTexImage2D
.. autofunction:: createTexImage2dFromFile
.. autofunction:: createTexImage2DMultisample
.. autofunction:: deleteTexture
.. autofunction:: bindTexture
.. autofunction:: createCubeMap

Vertex Buffer/Array Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tools for creating and working with Vertex Buffer Objects (VBOs) and Vertex
Array Objects (VAOs).

.. autofunction:: VertexArrayInfo
.. autofunction:: createVAO
.. autofunction:: drawVAO
.. autofunction:: deleteVAO
.. autofunction:: VertexBufferInfo
.. autofunction:: createVBO
.. autofunction:: bindVBO
.. autofunction:: unbindVBO
.. autofunction:: mapBuffer
.. autofunction:: unmapBuffer
.. autofunction:: deleteVBO
.. autofunction:: setVertexAttribPointer
.. autofunction:: enableVertexAttribArray
.. autofunction:: disableVertexAttribArray

Materials and Lighting
~~~~~~~~~~~~~~~~~~~~~~

Tools for specifying the appearance of faces and shading. Note that these tools
use the legacy OpenGL pipeline which may not be available on your platform. Use
fragment/vertex shaders instead for newer applications.

.. autofunction:: createMaterial
.. autofunction:: useMaterial
.. autofunction:: createLight
.. autofunction:: useLights
.. autofunction:: setAmbientLight

Meshes
~~~~~~

Tools for loading or procedurally generating meshes (3D models).

.. autofunction:: ObjMeshInfo
.. autofunction:: loadObjFile
.. autofunction:: loadMtlFile
.. autofunction:: createUVSphere
.. autofunction:: createPlane
.. autofunction:: createMeshGridFromArrays
.. autofunction:: createMeshGrid
.. autofunction:: createBox
.. autofunction:: transformMeshPosOri
.. autofunction:: calculateVertexNormals

Miscellaneous
~~~~~~~~~~~~~

Miscellaneous tools for working with OpenGL.

.. autofunction:: getIntegerv
.. autofunction:: getFloatv
.. autofunction:: getString
.. autofunction:: getOpenGLInfo
.. autofunction:: getModelViewMatrix
.. autofunction:: getProjectionMatrix


Examples
~~~~~~~~
**Working with Framebuffer Objects (FBOs):**

Creating an empty framebuffer with no attachments::

    fbo = createFBO()  # invalid until attachments are added

Create a render target with multiple color texture attachments::

    colorTex = createTexImage2D(1024,1024)  # empty texture
    depthRb = createRenderbuffer(800,600,internalFormat=GL.GL_DEPTH24_STENCIL8)

    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo.id)
    attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
    attach(GL.GL_DEPTH_ATTACHMENT, depthRb)
    attach(GL.GL_STENCIL_ATTACHMENT, depthRb)
    # or attach(GL.GL_DEPTH_STENCIL_ATTACHMENT, depthRb)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

Attach FBO images using a context. This automatically returns to the previous
FBO binding state when complete. This is useful if you don't know the current
binding state::

    with useFBO(fbo):
        attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
        attach(GL.GL_DEPTH_ATTACHMENT, depthRb)
        attach(GL.GL_STENCIL_ATTACHMENT, depthRb)

How to set userData some custom function might access::

    fbo.userData['flags'] = ['left_eye', 'clear_before_use']

Binding an FBO for drawing/reading::

    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fb.id)

Depth-only framebuffers are valid, sometimes need for generating shadows::

    depthTex = createTexImage2D(800, 600,
                                internalFormat=GL.GL_DEPTH_COMPONENT24,
                                pixelFormat=GL.GL_DEPTH_COMPONENT)
    fbo = createFBO([(GL.GL_DEPTH_ATTACHMENT, depthTex)])

Deleting a framebuffer when done with it. This invalidates the framebuffer's ID
and makes it available for use::

    deleteFBO(fbo)
