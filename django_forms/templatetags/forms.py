import ttag
from ttag import core
from django import template
from django.forms.forms import BoundField
from django.template.loader import get_template
from django.template.loader_tags import BlockNode, ExtendsNode, \
    BLOCK_CONTEXT_KEY, BlockContext

register = template.Library()
CONFIG_KEY = '_formconfig'
INHERIT = object()


class TemplateArg(ttag.Arg):

    def clean(self, value):
        if value is None or value is INHERIT:
            return None
        if hasattr(value, 'render'):
            return value
        return get_template(value)

    def resolve(self, value, context):
        if value is None:
            return INHERIT
        return super(TemplateArg, self).resolve(value, context)


class FormOptions(core.Options):

    def __init__(self, meta, *args, **kwargs):
        super(FormOptions, self).__init__(meta=meta, *args, **kwargs)
        self.default_template = getattr(meta, 'default_template', None)


class FormMetaclass(core.DeclarativeArgsMetaclass):
    options_class = FormOptions


class FormOptionsTag(core.BaseTag):
    __metaclass__ = FormMetaclass


class ConfigMixin(object):

    def get_fields(self, data):
        return []

    def init_config(self, context):
        context[CONFIG_KEY] = {}

    def get_config(self, type, data, context, fields=None):
        config_fields = context.get(CONFIG_KEY, {}).get(type)
        if not config_fields:
            return None
        if fields is None:
            fields = self.get_fields(data)
        for field in fields:
            field_repr = (field.form, field.name)
            config = config_fields.get(field_repr,
                config_fields.get(field.name))
            if config is not None:
                return config
        return config_fields.get(None)

    def set_config(self, type, data, context, value, set_none=False):
        if set_none or value is not None:
            config_fields = context[CONFIG_KEY].setdefault(type, {})
            fields = self.get_fields(data)
            if fields:
                for field in fields:
                    if isinstance(field, BoundField):
                        field = (field.form, field.name)
                    config_fields[field] = value
            else:
                config_fields[None] = value
            return True


class BaseFormTag(FormOptionsTag, ConfigMixin):
    with_ = ttag.KeywordsArg(required=False, named=True)
    only = ttag.BooleanArg()
    using = TemplateArg(required=False, named=True)
    extends = TemplateArg(required=False, named=True)

    def __init__(self, parser, *args, **kwargs):
        super(BaseFormTag, self).__init__(parser, *args, **kwargs)
        if 'using' in self._vars and 'extends' in self._vars:
            raise template.TemplateSyntaxError("Can't provide both 'using' "
                "and 'extends'.")
        using_inline = 'using' in self._vars and not self._vars['using']
        if using_inline or 'extends' in self._vars:
            nodelist = parser.parse([self._meta.end_block])
            parser.delete_first_token()
            if using_inline:
                self._vars['using'] = template.Template('')
                self._vars['using'].nodelist = nodelist
            else:
                self.blocks = dict([(n.name, n) for n in
                    nodelist.get_nodes_by_type(BlockNode)])

    def clean(self, data, context):
        data = super(BaseFormTag, self).clean(data, context)
        form_template = data.get('using') or data.get('extends')
        if not form_template:
            if not self._meta.default_template:
                return data
            form_template = self.get_config('%s_template' % self._meta.name,
                data, context) or self._meta.default_template
        if isinstance(form_template, basestring):
            form_template = get_template(form_template)
        data['template'] = form_template
        return data

    def get_extra_context(self, data):
        return {}

    def get_block_context(self, form_template, blocks):
        block_context = BlockContext()

        # Add the block nodes from this node to the block context.
        block_context.add_blocks(blocks)

        # Add the template's nodes too if it is the root template.
        for node in form_template.nodelist:
            # The ExtendsNode has to be the first non-text node.
            if not isinstance(node, template.TextNode):
                if not isinstance(node, ExtendsNode):
                    blocks = dict([(n.name, n) for n in
                                   form_template.nodelist\
                                       .get_nodes_by_type(BlockNode)])
                    block_context.add_blocks(blocks)
                break
        return block_context

    def render(self, context):
        data = self.resolve(context)

        if 'only' in data or self.get_config('only', data, context):
            sub_context = template.Context()
            for key, value in context.keys:
                if key in ('form', CONFIG_KEY):
                    sub_context[key] = value
        else:
            sub_context = context

        extra_context = self.get_extra_context(data)
        extra_context.update(self.get_config('with', data, context) or {})
        if 'with' in data:
            extra_context.update(data['with'])
        # Update (i.e. push) context in preparation for rendering.
        sub_context.update(extra_context)
        context.render_context.push()
        blocks = getattr(self, 'blocks',
            self.get_config('extends_blocks', data, context))
        if blocks:
            context.render_context[BLOCK_CONTEXT_KEY] = \
                self.get_block_context(data['template'], blocks)
        output = data['template']._render(sub_context)
        # Clean up context changes.
        context.render_context.pop()
        sub_context.pop()
        return output


class Form(BaseFormTag):
    forms = ttag.MultiArg(required=False)

    class Meta:
        default_template = 'forms/base.html'

    def render(self, context):
        self.init_config(context)
        return super(Form, self).render(context)

    def get_extra_context(self, data):
        errors = False
        non_field_errors = []
        for form in data['forms']:
            if form.errors:
                errors = True
                break
            non_field_errors.extend(form.non_field_errors())

        return {
            'forms': data['forms'],
            'errors': errors,
            'non_field_errors': non_field_errors,
        }


class FieldsArg(ttag.MultiArg):

    def clean(self, value):
        if len(value) == 1 and isinstance(value[0], (tuple, list)):
            value = value[0]
        return value


class Row(BaseFormTag):
    fields = FieldsArg()

    class Meta:
        default_template = 'forms/rows/base.html'

    def get_fields(self, data):
        return data['fields']

    def get_extra_context(self, data):
        errors = []
        required = 0
        for field in data['fields']:
            errors += field.errors
            if field.field.required:
                required += 1
        return {
            'fields': data['fields'],
            'errors': errors,
            'required': required,
        }


class Field(BaseFormTag):
    field = ttag.Arg()

    class Meta:
        default_template = 'forms/fields/base.html'

    def get_fields(self, data):
        return [data['field']]
    
    def get_extra_context(self, data):
        field = data['field']
        context = {}
        for attr in ('value', 'errors', 'label', 'help_text', 'form', 'field',
            'id_for_label', 'name', 'html_name'):
            context[attr] = getattr(field, attr)
        context['id'] = field.auto_id
        return context


class Formconfig(BaseFormTag):
    context = ttag.BasicArg()
    for_ = ttag.MultiArg(named=True, required=False)
    position = ttag.IntegerArg(named=True, required=False)

    def __init__(self, *args, **kwargs):
        super(Formconfig, self).__init__(*args, **kwargs)
        if self._vars['context'] not in ('field', 'row'):
            raise template.TemplateSyntaxError("First argument must be "
                "'field' or 'row' (found %r)." % self._vars['context'])

    def get_fields(self, data):
        return data.get('for') or []

    def render(self, context):
        data = self.resolve(context)
        self.set_config('%s_template' % data['context'], data, context,
            data.get('template'))
        self.set_config('with', data, context, data.get('with'))
        self.set_config('only', data, context, data.get('only'))
        if data.get('for'):
            self.set_config('position', data, context, data.get('position'))
        if 'extends' in data:
            self.set_config('extends_blocks', data, context, self.blocks)
        return ''


class GetOrderedRows(ttag.helpers.AsTag, ConfigMixin):
    forms_list = ttag.Arg()

    def as_value(self, data, context):
        rows = []
        for form in data['forms_list']:
            for bound_field in form:
                position = self.get_config('position', data, context,
                    fields=[bound_field]) or 0
                # For now, there's nothing to put more than one field in a row.
                rows.append((position, [bound_field]))
        rows.sort(key=lambda bits: bits[0], reverse=True)
        return [bits[1] for bits in rows]


class Ifcontent(ttag.Tag):

    def __init__(self, parser, *args, **kwargs):
        super(Ifcontent, self).__init__(parser, *args, **kwargs)
        self.nodelist_before = parser.parse(['content'])
        parser.delete_first_token()
        self.nodelist_inner = parser.parse(['endcontent'])
        parser.delete_first_token()
        self.nodelist_after = parser.parse([self._meta.end_block])
        parser.delete_first_token()
        self.child_nodelists = ('nodelist_before', 'nodelist_inner',
            'nodelist_after')

    def render(self, context):
        value = self.nodelist_inner.render(context)
        if not value.strip():
            return ''
        return ''.join((
            self.nodelist_before.render(context),
            value,
            self.nodelist_after.render(context)
        ))


register.tag(Form)
register.tag(Row)
register.tag(Field)
register.tag(Formconfig)
register.tag(GetOrderedRows)
register.tag(Ifcontent)
