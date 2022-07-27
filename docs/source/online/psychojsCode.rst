
Manual coding of PsychoJS studies
-----------------------------------

**Note that PsychoJS is very much under development and all parts of the API are subject to change**

Some people may want to write a JS script from scratch or convert their PsychoPy Python script into `PsychoJS`_. However, supporting this approach is beyond the scope of our documentation and our `forum <https://discourse.psychopy.org/c/online/14>`_.

Working with JS Code Components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Code components can automatically convert Python to JavaScript. However, this doesn't always work. Below are some pointers to help you out:

- For common JS functions, see the `PsychoPy to JS crib sheet <https://docs.google.com/document/d/183xmwDgSbnJZHMGf3yWpieV9Bx8y7fOCm3QKkMOOXFQ/edit?usp=sharing>`_ by `Wakefield Morys-Carter <https://twitter.com/Psych_Stats/>`_
- For finding out how to manipulate PsychoJS components via code, see the `PsychoJS API <https://psychopy.github.io/psychojs/>`_. The `tutorial_js_expose_psychojs experiment <https://gitlab.pavlovia.org/tpronk/tutorial_js_expose_psychojs>`_ shows how to expose PsychoJS objects to the web browser, so that you can access them via the browser console, and try things out in order to see what works (or not).
- If you're looking for a JS equivalent of a Python function, try searching 'JS equivalent/version of function X' on `stack overflow <https://stackoverflow.com/>`_ or `Google <https://google.com>`_
- Still stuck? Try asking for help on the `forum <https://discourse.psychopy.org/c/online/14>`_. For giving researchers access to the repository of your experiment, see :ref:`contributingToPavlovia`

Adding JS functions
~~~~~~~~~~~~~~~~~~~
If you have a function you want to use, and you find the equivalent on the crib sheet or stack overflow, add an 'initialization' code component to the start of your experiment. Set code type to be 'JS' and copy and paste the function(s) you want there in the 'Begin experiment' tab. These functions will then be available to be called throughout the rest of the task.

.. image:: initializeJScode.png

Don't change the generated JS file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When you export an experiment to HTML from the PsychoPy builder, it generates a JS file. We recommend *not* to edit this JS file, for the reasons below:

- Changes you make in your .js file will not be reflected back in your builder file; it is a one way street.
- It becomes more difficult to sync your experiment with |Pavlovia| from the |PsychoPy| builder
- Researchers that would like to replicate your experiment but aren't very JavaScript-savvy might be better off using the PsychoPy Builder