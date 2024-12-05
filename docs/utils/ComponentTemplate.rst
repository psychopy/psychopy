.. {{ cls.__name__ }}:

-------------------------------
{{ cls.title }}
-------------------------------

{{ cls.tooltip }}

Categories:
    {{ ", ".join(cls.categories) }}
Works in:
    {{ ", ".join(cls.targets) }}

Parameters
-------------------------------
{% for categ in params %}
{{ categ }}
===============================
{% for param in params[categ] %}
{{ param.label }}
    {{ param.hint }}
{% endfor %}
{% endfor %}


.. seealso::
	
	API reference for :class:`~{{ cls.__module__ }}`
