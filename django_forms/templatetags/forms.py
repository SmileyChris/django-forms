import re
from django import template, forms
from django.template import loader
from django_forms import utils
import copy

register = template.Library()
re_kwarg = re.compile(r'^(?:(\w+\.)(?\w)=)(.*)')


def _load_form_template(element, context, context_bit=None,
                        specific_template=None):
    """
    Select the appropriate form template.

    """
    context_bit = context_bit or element
    template_bit = context.get('_django_template_%s' % context_bit, 'default')
    templates = []
    if specific_template:
        templates.append('%s/%s.html' % (element, template))
    templates.append('%s/%s.html' % (element, template_bit))
    base = context.get('_django_template_base')
    return loader.select_template(utils.template_locations(templates, base))


class MediaNode(object):

    def __init__(self, template, nodelist, media_type=None, extra_context={}):
        self.template = template
        self.nodelist = nodelist
        self.media_type = media_type
        self.extra_context = extra_context

    def render(self, context):
        output = self.nodelist.render(context)

        # After the template is completely rendered, there should be a
        # ``_forms`` item on the RequestContext which contains all of the forms
        # rendered with the ``{% form %}`` tag.
        forms = context.render_context.get('_forms')
        if not forms:
            return output
        media = forms[0].media
        for form in forms[1:]:
            media += form.media
        templates = utils.template_locations(self.template)
        template = loader.select_template(templates)
        if self.media_type:
            media = media[self.media_type]
        context = {'media': media}
        context.update(self.extra_context)
        return '%s%s' % (template.render(template.Context(context)),
                         output)


class FormTemplateNode(object):

    def __init__(self, nodelist, **kwargs):
        self.nodelist = nodelist
        self.kwargs = kwargs

    def render(self, context):
        context_args = {}
        for key, var in self.kwargs.iteritems():
            context_args['_django_template_%s' % key] = var.resolve(context)
        context.update(context_args)
        output = self.nodelist.render(context)
        context.pop()
        return output


class FormBlockNode(object):

    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        template = _load_form_template('block', context, context_bit='row')
        remaining_output = self.nodelist.render(context)

        context.push()
        context['data'] = remaining_output
        try:
            return template.render()
        finally:
            context.pop()


class FormNode(object):

    def __init__(self, action, args, all_vars):
        self.action = action
        self.args = args
        self.all_vars = all_vars

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        if isinstance(args[0], forms.Field):
            field, args = args[0], args[1:]
        else:
            field = context['field']
        if args:
            specific_template = args[0]
        else:
            specific_template = None
        template = _load_form_template(self.action, context,
                                       specific_template=specific_template)

        form_vars = copy.deepcopy(self.all_vars)
        _resolve_dict(form_vars, context)

        context.update({'field': field, 'form_vars': form_vars})
        try:
            return template.render(context)
        finally:
            context.pop()


@register.tag
def form_js(parser, token):
    """
    Render the JS media for all forms in a template.

    """
    bits = token.split_contents()
    tag_name, bits = bits[0], bits[1:]
    if bits:
        raise template.TemplateSyntaxError('%s did not expect any arguments' %
                                           tag_name)
    nodelist = parser.parse()
    return MediaNode('media/js.html', nodelist, 'js')


@register.tag
def form_css(parser, token):
    """
    Render the CSS media for all forms in a template.

    """
    bits = token.split_contents()
    tag_name, bits = bits[0], bits[1:]
    if len(bits) not in (0, 1):
        raise template.TemplateSyntaxError('%s did not expect any arguments' %
                                           tag_name)
    nodelist = parser.parse()
    return MediaNode('media/css.html', nodelist, 'css')


@register.tag
def formtemplate(parser, token):
    """
    This block tag (i.e. must be closed with ``{% endformtemplate %}``) has two
    purposes:
    
    1. It allows an alternate base directory to be used for finding element
       templates.
    
    2. It can be used to set default element templates.
    
    The format is::
    
        {% formtemplate [base="template_base"] [<element_template>="somealternate" ...] %}
        ...
        {% endformtemplate %}

    """
    bits = token.split_contents()
    tag_name, bits = bits[0], bits[1:]

    kwargs = {}
    for bit in bits:
        pre_key, key, arg = re_kwarg.match(bit).groups()
        if pre_key:
            raise template.TemplateSyntaxError('Bad keyword argument for %s'
                    ' (%s.%s)' % (tag_name, pre_key, key))
        if not key:
            raise template.TemplateSyntaxError('%s does not expect any '
                    'non-keyword arguments' % tag_name)
        # TODO: use a whitelist (raising a syntax error for bad keys)?
        kwargs[key] = parser.compile_filter(arg)

    nodelist = parser.parse('end%s' % tag_name)
    nodelist.delete_first_token()
    return FormTemplateNode(nodelist, **kwargs)


@register.tag
def formblock(parser, token):
    """
    Wrap rows with the correct HTML block tag (or common code
    prepended/appended) for the current form template settings.

    The template used is determined based on the default **row** element
    template in the current context.

    """
    bits = token.split_contents()
    tag_name, bits = bits[0], bits[1:]

    if bits:
        raise template.TemplateSyntaxError('%s did not expect any arguments' %
                                           tag_name)

    nodelist = parser.parse('end%s' % tag_name)
    nodelist.delete_first_token()
    return FormBlockNode(nodelist)


@register.tag
def form(parser, token):
    """
    The fundamental tag for the django-forms library.

    """
    bits = token.split_contents()
    tag_name, bits = bits[0], bits[1:]

    args = []
    action = None
    all_vars = {}
    for bit in bits:
        pre_key, key, arg = re_kwarg.match(bit).groups()
        if (key and len(bits) < 1) or (not key and len(bits) >= 3):
            raise template.TemplateSyntaxError('Expected format {%% %s '
                '<action> <object> [template] [attr=value ...] %}' % tag_name)
        action = args[0]
        pre_key = pre_key or action
        if pre_key:
            value = parser.compile_filter(arg)
            action_vars = all_vars.setdefault(pre_key, {})
            if key in ('text',):
                action_vars[key] = value
            else:
                action_attrs = all_vars.setdefault('attrs', {})
                action_attrs[key] = value
        else:
            if not action:
                # The first argument is the action - it doesn't need to be
                # compiled.
                action = arg
            else:
                args.append(parser.compile_filter(arg))

    # TODO: validate the action?

    return FormNode(action, args, all_vars)


def _resolve_dict(dict, context):
    """
    Recursively resolve all dictionary items using the context.

    """
    for key, value in dict.values():
        if isinstance(value, dict):
            value = _resolve_dict(value, context)
        else:
            dict[key] = value.resolve(context)
