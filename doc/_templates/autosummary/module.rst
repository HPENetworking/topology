{{ fullname }}
{{ underline }}

.. automodule:: {{ fullname }}
   :show-inheritance:

   {% block functions %}
   {% if functions %}
   .. rubric:: Functions

   .. autosummary::
   {% for item in functions %}
      {{ item }}
   {%- endfor %}

   {% for item in functions %}
   .. autofunction:: {{ item }}
   {%- endfor %}

   {% endif %}
   {% endblock %}


   {% block classes %}
   {% if classes %}
   .. rubric:: Classes

   .. autosummary::
   {% for item in classes %}
      {{ item }}
   {%- endfor %}

   {% for item in classes %}
   .. autoclass:: {{ item }}
      :show-inheritance:
      :members:
   {%- endfor %}

   {% endif %}
   {% endblock %}


   {% block exceptions %}
   {% if exceptions %}
   .. rubric:: Exceptions

   .. autosummary::
   {% for item in exceptions %}
      {{ item }}
   {%- endfor %}

   {% for item in exceptions %}
   .. autoexception:: {{ item }}
      :show-inheritance:
   {%- endfor %}

   {% endif %}
   {% endblock %}
