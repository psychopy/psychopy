.. _visual:

:mod:`psychopy.visual` - many visual stimuli
==============================================================================

.. toctree::
    :maxdepth: 1
    :hidden:
    :glob:

    *


:class:`.Window` to display all stimuli below.

Windows and and display devices:

* :class:`.Window` is the main class to display objects
* :class:`.Warper` for non-flat projection screens
* :class:`.ProjectorFramePacker` for handling displays with 'structured light mode' to achieve high framerates
* :class:`.Rift` for Oculus Rift support (Windows 64bit only)
* :class:`.VisualSystemHD` for NordicNeuralLab's VisualSystemHD in-scanner display.

Commonly used:

* :class:`.ImageStim` to show images
* :class:`.TextStim` to show text
* :class:`.TextBox2` rewrite of TextStim (faster, editable with more layout options and formatting)

Shapes (all special classes of :class:`ShapeStim`):

* :class:`.ShapeStim` to draw shapes with arbitrary numbers of vertices
* :class:`.Rect` to show rectangles
* :class:`.Circle` to show circles
* :class:`.Polygon` to show polygons
* :class:`.Line` to show a line
* :class:`.Pie` to show wedges and semi-circles

Images and patterns:

* :class:`.SimpleImageStim` to show images without bells and whistles
* :class:`.GratingStim` to show gratings
* :class:`.RadialStim` to show annulus, a rotating wedge, a checkerboard etc
* :class:`.NoiseStim` to show filtered noise patterns of various forms
* :class:`.EnvelopeGrating` to generate second-order stimuli (gratings that can have a carrier and envelope)

Multiple stimuli:

* :class:`.ElementArrayStim` to show many stimuli of the same type
* :class:`.DotStim` to show and control movement of dots

3D shapes, materials, and lighting:

* :class:`.LightSource` to define a light source in a scene
* :class:`.SceneSkybox` to render a background skybox for VR and 3D scenes
* :class:`.BlinnPhongMaterial` to specify a material using the Blinn-Phong lighting model
* :class:`.RigidBodyPose` to define poses of objects in 3D space
* :class:`.BoundingBox` to define bounding boxes around 3D objects
* :class:`.SphereStim` to show a 3D sphere
* :class:`.BoxStim` to show 3D boxes and cubes
* :class:`.PlaneStim` to show 3D plane
* :class:`.ObjMeshStim` to show Wavefront OBJ meshes loaded from files

Other stimuli:

* :class:`.MovieStim` to show movies
* :class:`.VlcMovieStim` to show movies using VLC
* :class:`.Slider` a new improved class to collect ratings
* :class:`.RatingScale` to collect ratings
* :class:`.CustomMouse` to change the cursor in windows with GUI. OBS: will be deprecated soon

Meta stimuli (stimuli that operate on other stimuli):

* :class:`.BufferImageStim` to make a faster-to-show "screenshot" of other stimuli
* :class:`.Aperture` to restrict visibility area of other stimuli

Helper functions:

* :mod:`~psychopy.visual.filters` for creating grating textures and Gaussian masks etc.
* :mod:`~psychopy.tools.visualhelperfunctions` for tests about whether one stimulus contains another
* :mod:`~psychopy.tools.unittools` to convert deg<->radians
* :mod:`~psychopy.tools.monitorunittools` to convert cm<->pix<->deg etc.
* :mod:`~psychopy.tools.colorspacetools` to convert between supported color spaces
* :mod:`~psychopy.tools.viewtools` to work with view projections
* :mod:`~psychopy.tools.mathtools` to work with vectors, quaternions, and matrices
* :mod:`~psychopy.tools.gltools` to work with OpenGL directly (under development)
