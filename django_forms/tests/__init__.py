import os
from unittest import TestCase

from django import forms, template
from django.conf import settings


class TestForm(forms.Form):
    """
    A simple test form for use by the django-forms test cases.

    """
    name = forms.CharField()
    email = forms.EmailField()


class BaseFormsTest(TestCase):
    """
    A base test case class for django-forms tests.

    """

    def setUp(self):
        """
        Alter the settings to ensure a reproducible test environment.

        """
        self.old_TEMPLATE_LOADERS = settings.TEMPLATE_LOADERS
        settings.TEMPLATE_LOADERS = (
            'django.template.loaders.filesystem.Loader',
        )
        self.old_TEMPLATE_DIRS = settings.TEMPLATE_DIRS
        test_dir = os.path.dirname(os.path.realpath(__file__))
        settings.TEMPLATE_DIRS = (
            os.path.join(test_dir, 'templates'),
            os.path.join(os.path.dirname(test_dir), 'templates'),
        )

    def tearDown(self):
        """
        Restore the altered project settings to their original values.

        """
        settings.TEMPLATE_DIRS = self.old_TEMPLATE_DIRS
        settings.TEMPLATE_LOADERS = self.old_TEMPLATE_LOADERS


class FormsTest(BaseFormsTest):

    def test_basic(self):
        t = template.Template('{% load forms %}'
                              '{% field form.email %}')
        output = t.render(template.Context({'form': TestForm()}))
        expected = '<label for="id_email">Email</label>'\
            '<input type="text" name="email" value="" id="id_email" />'
        
        self.assertEqual(output.strip().replace('\n', ''), expected)
