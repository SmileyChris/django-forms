============
Django Forms
============

A designer-focused forms control library which works as a layer over the
standard Django forms API.


Tags
====

.. _form-tag:

``{% form %}``
--------------

Render one or more forms. A basic example of rendering a standard form using
HTML paragraphs for rows would be
``{% form some_form using "forms/p.html" %}``.

Usage::

    {% form some_form [form2 form3 ...] %}

Any of the standard `tag arguments`_ can be used.

Context:

    ``forms``
        List of forms to render.

    ``errors``
        Set to ``True`` if any of the forms contain errors.

    ``non_field_errors``
        List of non-field errors.


.. _row-tag:

``{% row %}``
-------------

Used to render a row template with one or more fields with the currently
defined template.

Usage is either::

    * ``{% row field_list %}``
    * ``{% row some_form.field [some_form.field ...] %}``

Any of the standard `tag arguments`_ can be used.

Context:

    ``fields``
        List of fields to render.

    ``errors``
        List of errors relating to any of the fields in this row.

    ``required``
        The number of fields that are required.


.. _field-tag

``{% field %}``
---------------

Used to render a specific field with the currently defined field template.

Usage::

    {% field some_field %}

Requires a context variable named ``form`` to exist (and be a
`django.forms.forms.BaseForm`` instance).

Any of the standard `tag arguments`_ can be used.

Context:

    ``value``
        The value of this field.

    ``errors``
        A list of errors relating to this field.

    ``label``
        The label text for this field.
    
    ``help_text``
        The help text for this field.

    ``form``
        The form this field belongs to.
    
    ``field``
        The underlying form field being rendered.
        
    ``id``
        The id for this field (or an empty string).

    ``id_for_label``
        The id which should be assigned to the field's label

    ``name``
        The name of this field.

    ``html_name``
        The prefixed name of this field


.. _formconfig-tag

``{% formconfig %}``
--------------------

Used to configure rows and fields, as specified by the first tag argument.
Reuse of this tag overrides previously defined matching configurations.

Usage, either::

    * ``{% formconfig row ... %}``, or
    * ``{% formconfig field ... %}``

    Any of the standard `tag arguments`_ can be used.

To limit the configuration of rows for one or more specific fields, use the
``for`` argument. For example::

    {% formconfig row for form.first_name form.last_name using "forms/rows/pretty.html" %}

The ``for`` argument also accepts strings::

    {% formconfig field for "email" with help_text="Your email address" %}

Use the ``priority`` argument to `change the default order of form fields`_.
This can only be used if the configuration is limited to specific fields. For
example::

    {% formconfig field for form.first_name priority 1 %}
    {% formconfig field for form.last_name priority 2 %}


Tag Arguments
=============

These arguments can be used on any form-related tag.

Add to the context (``with``)
-----------------------------

`` with key=value [key=value key=value ...]``

Adds to the context of the template which will be rendered.

Exclude the current context (``only``)
--------------------------------------

If this argument is part of the tag, the current context will not be available
to the template that will be rendered.

.. note::

    There is one exception: any context variable named ``form`` will still be
    available (also any variable starting with ``_formconfig``, but they aren't
    available from templates anyway).


Choose the template (``using`` or ``extends``)
----------------------------------------------

There are two arguments that allow configuration of which template should be
used to render the template:

`` using some_template`` or `` using`` (as the final tag argument)
    Specify the template to use.

`` extends some_template`` or `` extends`` (as the final tag argument)
    Extends an existing template (via the use of ``{% block %}`` tags).
    See the `Extend form-related templates inline`_ section.

The ``using`` argument without a template or either form of the ``extends``
argument means that the template is being defined inline until a closing
``{% end-`` tag is reached (matching the opening tag, for example, 
``{% form extends "forms/custom.html" %}...{% endform %}``).


Other Tags
==========

``{% get_ordered_fields %}``
--------------------------

Used by form templates to retrieve an ordered list of form fields.

Usage::

    {% get_ordered_fields forms_list as var_name %}

Adds a context variable containing a list of fields.


``{% ifcontent %}``
-------------------

Not specific to forms, a useful tag which allows wrapping text if the content
contains non-whitespace. For example, conditionally showing the help text div
inside of the field template::

    {% ifcontent %}
        <div class="helptext">
            {% content %}
                {% block help %}{{ help_text }}{% endblock %}
            {% endcontent %}
        </div>
    {% endifcontent %}


Examples of extending form-related templates inline
===================================================

Here are some basic examples::

    {% form form1 form2 extends "forms/p.html" %}

        {% block config %}
            {% formconfig field using "forms/fields/booleanselect.html" for form1.accept_tos %}
        {% endblock %}

    {% endform %}


    {% form form1 extends "forms/p.html" %}

        {% block config %}
            {### Set all rows to use a special "p", except for the TOS #}
            {% formconfig row using "forms/rows/special-p.html" %}
            {% formconfig row using "forms/rows/p.html" for form1.accept_tos %}
        {% endblock %}

    {% endform %}

And here's one more slightly more complex example that extends both the form
and a field's template::

    {% form extends "forms/p.html" %}

        {% block config %}
            {% formconfig field for form.is_manager extends %}
                {% block help %}{% blocktrans with site=site.name %}Can this person manage {{ site }}?{% endblocktrans %}{% endblock %}
            {% endformconfig %}
        {% endblock %}
        
        {% block fields %}
            {% row form.first_name form.last_name %}
            {% row form.email with class="email" %}
            {% row form.is_manager %}
        {% endblock fields %}

    {% endform %}


Change the default order of form fields
=======================================

Use the ``priority`` argument of :ref:`formconfig-tag` to order fields without
the need to manually redefine all fields in the form.
To give fields a priority to the top of the form, use positive integers (the
lower the number, the higher priority).

Use negative integers to give fields a low priority (i.e. occuring after both
those with a positive priority and those without a priority set at all).

If multiple fields are given the same priority, the fields configured first
will have the highest priority::

    {% form form1 form2 extends "forms/p.html" %}

        {% block config %}
            {### Put these three fields to the top, in this order #}
            {% formconfig field for "first_name" priority 1 %}
            {% formconfig field for "last_name" priority 1 %}
            {% formconfig field for "email" priority 1 %}
            {### And put this one to the bottom #}
            {% formconfig field for "accept_tos" priority -1 %}
        {% endblock %}

    {% endform %}

If you are creating an entire form template, use this tag to initiate the
reordering of a form's fields::

    {% formreorder form %}

This is done in all the built-in form templates.


Example of a form template
==========================

``forms/p.html``::

    {% block allconfig %}
        {% formconfig row using "forms/rows/p.html" %}
        {% block config %}{% endblock %}
    {% endblock %}
    
    {% if non_field_errors %}
    <ul class="errors">
        {% for errors in form.non_field_errors %}
        <li>{{ errors }}</li>
        {% endfor %}
    </ul>
    {% endif %}
    
    {% get_rows_ordered forms as rows %}
    {% block rows %}
    {% for fields in rows %}
        {% row fields %}
    {% endfor %}
    {% endblock %}


``forms/rows/base.html``::

    {% block row_start %}{% endblock %}
    {% for form, field in fields %}
        {% block start %}{% endblock %}
        {% field field %}
        {% block end %}{% endblock %}
    {% endfor %}
    {% block row_end %}{% endblock %}


``forms/rows/p.html``::

    {% extends "forms/rows/base.html" %}
    {% block start %}<p{% if errors or required %} class="{% if errors %}errors{% if required %} {% endif %}{% endif %}{% if required %}required{% endif %}"{% endif %}>{% endblock %}
    {% block end %}</p>{% endblock %}


``form/fields/base.html``::

    {% if label %}
        <label{% if id_for_label %} for="{{ id_for_label }}">{% block label %}{{ label }}{% endblock %}</label>
    {% endif %}
    <input type="text" value="{{ value }}" id="{{ id }}" />
    {% if errors %}
    <ul class="errors">
    {% for error in errors %}
        <li>{{ error }}</li>
    {% endfor %}
    </ul>
    {% endif %}
    {% ifcontent %}
        <span class="helptext">
            {% content %}
                {% block help %}{{ help_text }}{% endblock %}
            {% endcontent %}
        </span>
    {% endifcontent %}
