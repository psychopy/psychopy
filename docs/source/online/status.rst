.. _onlineStatus:
.. role:: darkred
.. role:: darkgreen
.. role:: darkorange

Status of online options
--------------------------

The table below shows you the current state of play of PsychoJS. Per feature we list whether it's:

1. :darkgreen:`Built-in` Supported via the PsychoPy Builder
2. :darkorange:`Prototype` Supported via tutorials or customized experiments that can be cloned and adapted. Kudos to our users for pushing the envelope!
3. :darkred:`Not supported` Supported by PsychoPy, but not yet supported by PsychoJS

.. csv-table::
  :header: "Feature","Status","Notes"
  :align: left
  :widths: 15,15,70
  :escape: \

  **Stimuli**,,
    :doc:`Dots (RDK) <../builder/components/dots>`, :darkorange:`Prototype`, Random Dot Kinematogram. Try it out via `staircaserdk <https://gitlab.pavlovia.org/Francesco_Cabiddu/staircaserdk>`_
    :doc:`Images <../builder/components/image>`, :darkgreen:`Built-in`, Try it out via `e2e_img <https://gitlab.pavlovia.org/tpronk/e2e_img>`_
    :doc:`Movies <../builder/components/movie>`, :darkgreen:`Built-in`, Try it out via `demo_video <https://gitlab.pavlovia.org/tpronk/demo_video>`_    
    :doc:`Polygons <../builder/components/polygon>`, :darkgreen:`Built-in`, Try it out via `e2e_polygons <https://gitlab.pavlovia.org/tpronk/e2e_polygons>`_
    :doc:`Sounds <../builder/components/sound>`, :darkgreen:`Built-in`, Try it out via `demo_sound <https://gitlab.pavlovia.org/tpronk/demo_sound>`_
    :doc:`Text <../builder/components/text>`, :darkgreen:`Built-in`, Try it out via `e2e_text <https://gitlab.pavlovia.org/tpronk/e2e_text>`_
    :doc:`Textbox <../builder/components/textbox>`, :darkgreen:`Built-in`, Try it out via `e2e_textbox <https://gitlab.pavlovia.org/tpronk/e2e_textbox>`_    
    , :darkred:`Not supported`, Apertures\, Envelope Gratings\, Gratings\, Noise
  **Responses**,,
    :doc:`Form <../builder/components/form >`, :darkgreen:`Built-in`, 
    Gyroscope, :darkorange:`Prototype`, Measures the orientation of tablets and smartphones. Try it out via `demo_gyroscope <https://gitlab.pavlovia.org/tpronk/demo_gyroscope>`_
    Eye-tracking, :darkorange:`Prototype`, Try it out via `demo_eye_tracking2 <https://gitlab.pavlovia.org/tpronk/demo_eye_tracking2/>`_
    :doc:`Keyboard <../builder/components/keyboard>`, :darkgreen:`Built-in`, 
    :doc:`Mouse <../builder/components/mouse>`, :darkgreen:`Built-in`, 
    :doc:`Slider <../builder/components/slider>`, :darkgreen:`Built-in`, 
    :doc:`Textbox <../builder/components/textbox>`, :darkgreen:`Built-in`, Try it out via `e2e_textbox <https://gitlab.pavlovia.org/tpronk/e2e_textbox>`_
    , :darkred:`Not supported`, Brush\, Joystick\, Microphone\, Button boxes (Cedrus & IO Labs)
  **Data**,,
    :doc:`CSV files <../general/dataOutputs>`, :darkgreen:`Built-in`, These can easily be imported into analysis software\, such as Matlab\, R\, JAMOVI\, or JASP
    :doc:`Log files <../general/dataOutputs>`, :darkgreen:`Built-in`, Low-level logs. These offer detailed information\, but are hard to analyze
    :doc:`MongoDB`, :darkgreen:`Built-in`, Similar to CSV\, but stored in a database instead of files
    , :darkred:`Not supported`, XLSX
  **Flow and Logic**,,
    :doc:`Code <../builder/components/code>`, :darkgreen:`Built-in`, Insert snippets of programming code\, which can be automatically translated from Python to JavaScript
    :ref:`Loops <loops>`, :darkgreen:`Built-in`, Loops allow randomization and importing condition files. Try it out via `e2e_conditions <https://gitlab.pavlovia.org/tpronk/e2e_conditions>`_
    :ref:`Staircases <staircaseMethods>`, :darkorange:`Prototype`, Adapt aspects of a trial based on earlier responses of a participant. Try out a "Just Noticable Difference" staircase via  `staircase-demo <https://gitlab.pavlovia.org/lpxrh6/staircase-demo>`_ or a "Method-of-Adjustment" staircase via `method-of-adjustment <https://gitlab.pavlovia.org/lpxrh6/method-of-adjustment>`_
  **External Tools**,,
    :doc:`Any Tool`, :darkgreen:`Built-in`, General instructions are at :doc:`Recruiting participants and connecting with online services <onlineParticipants>`
    :doc:`AMT`, :darkgreen:`Built-in`, Amazon Mechanical Turk. See instructions in this `forum post <https://discourse.psychopy.org/t/how-to-use-mturk-for-recruiting/8486/7>`_
    :doc:`Prolific`, :darkgreen:`Built-in`, See instructions at :doc:`Recruiting with Prolific <prolificIntegration>`
    :doc:`Qualtrics`, :darkgreen:`Built-in`, There are many guides available for different ways of integrating Qualtrics on our `forum <https://discourse.psychopy.org/search?q=qualtrics>`_
    :doc:`Sona`, :darkgreen:`Built-in`, See instructiong at the `Sona Systems website <https://www.sona-systems.com/help/psychopy.aspx>`_

*Thanks go out to Anastasia Carter, Arnon Weinberg, Francesco Cabiddu, Lindsay Santacroce, and Wakefield Carter; they made tutorials and/or demo experiments available that we referenced in the list above.*

Anything else we should add to the list above? Built a cool prototype? Please tell us via the `PsychoPy Forum <https://discourse.psychopy.org/c/online/14>`_.
