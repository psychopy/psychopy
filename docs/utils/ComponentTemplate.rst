.. _{{ cls.__name__ | lower }}:

-------------------------------
{{ cls.title }}
-------------------------------

{{ cls.tooltip }}

Categories:
    {{ ", ".join(cls.categories) }}
Works in:
    {{ ", ".join(cls.targets) }}
{% if cls.beta %}
**Note: Since this is still in beta, keep an eye out for bug fixes.**{% endif %}

Parameters
-------------------------------
{% for categ in params %}
{{ categ }}
===============================

{{ categs[categ] }}

{% for param in params[categ] %}
.. _{{ cls.__name__ | lower }}-{{ param.ref }}:
{{ param.label }} {{ param.depends }}
    {{ param.hint }}
    {% if param.allowedLabels %}
    Options:
    {% for choice in param.allowedLabels %}
    * {{ choice }}
    {% endfor %}{% endif%}{% endfor %}{% endfor %}