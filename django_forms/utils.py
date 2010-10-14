DEFAULT_BASE = 'forms/default'


def template_locations(templates, base=None):
    """
    A generator which will produce a full list of template locations to check.

    ``templates`` can either be a string or a list of strings.

    You can provide an alternate base to check before checking the default base
    location.

    For example, if the function is called as such::

        fields = ['field/mypassword.html', 'field/password.html']
        template_locations(fields, base='myforms')

    The following template locations will be returned (in this order)::

        ['myforms/field/mypassword.html',
         'forms/default/field/mypassword.html',
         'myforms/field/password.html',
         'forms/default/field/password.html',
         'myforms/field/default.html',
         'forms/default/field/default.html']

    """
    bases = []
    if base and base != DEFAULT_BASE:
        bases.append(base)
    bases.append(DEFAULT_BASE)
    if isinstance(templates, basestring):
        templates = [templates]
    for template in templates:
        if template.startswith('/'):
            yield template[1:]
        else:
            for base in bases:
                base = base and '%s/' % base or ''
                yield '%s%s' % (base, template)
