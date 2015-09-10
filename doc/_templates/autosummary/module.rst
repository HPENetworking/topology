{{ fullname }}
{{ underline }}

.. automodule:: {{ fullname }}
   :show-inheritance:

   .. contents::
      :local:

.. currentmodule:: {{ fullname }}


{% block functions -%}
{%- if functions -%}
Functions
---------

.. autosummary::
{% for item in functions %}
   {{ item }}
{%- endfor %}

{% for item in functions %}
.. autofunction:: {{ item }}
{##}
{%- endfor -%}
{%- endif -%}
{%- endblock %}

{% block classes -%}
{%- if classes -%}
Classes
-------

.. autosummary::
{% for item in classes %}
   {{ item }}
{%- endfor %}

{% for item in classes %}
.. autoclass:: {{ item }}
   :members:

   .. rubric:: Inheritance
   .. inheritance-diagram:: {{ item }}
{##}
{%- endfor -%}
{%- endif -%}
{%- endblock %}

{% block exceptions -%}
{% if exceptions -%}
Exceptions
----------

.. autosummary::
{% for item in exceptions %}
   {{ item }}
{%- endfor %}

{% for item in exceptions %}
.. autoexception:: {{ item }}

   .. rubric:: Inheritance
   .. inheritance-diagram:: {{ item }}
{##}
{%- endfor -%}
{%- endif -%}
{%- endblock %}
