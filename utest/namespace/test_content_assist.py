#  Copyright 2008 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import sys
import unittest
from robot.utils.asserts import assert_true, assert_none, assert_false, \
        assert_equals

from robotide.namespace import Namespace
from robotide.robotapi import TestSuiteData
from robotide.model.files import _TestSuiteFactory
from robotide.application import DataModel
from robotide import context
from resources import COMPLEX_SUITE_PATH, PATH_RESOURCE_NAME


SUITEDATA = TestSuiteData(COMPLEX_SUITE_PATH)


class APPMock(object):

    def import_new_resource(self, datafile, path):
        self.datafile = datafile
        self.path = path

APP_MOCK = APPMock()
context.APP = APP_MOCK


class _ContentAssistBaseTest(unittest.TestCase):

    def _content_assist_should_not_contain(self, name, value=''):
        for item in self.ns.content_assist_values(self.suite, value):
            if item.name == name:
                raise AssertionError("Item '%s' found from content assist"
                                     % (name))

    def _content_assist_should_contain(self, name, source, value=''):
        self._should_contain(self.ns.content_assist_values(self.suite, value),
                             name, source)

    def _should_contain(self, items, name, source):
        for item in items:
            if item.name == name and item.source == source:
                return
        raise AssertionError('Item "%s" not found from %s' % (name, source))


class TestResolvingKeywordAndVariables(_ContentAssistBaseTest):
    exp_kws = [ ('Should Be Equal', 'BuiltIn'),
                ('File Should Exist', 'OperatingSystem'),
                ('Resource UK', 'resource.html'),
                ('Resource2 UK', 'resource2.html'),
                ('Resource3 UK', 'resource3.html'),
                ('UK From Text Resource', 'resource.txt'),
                ('Path Resource UK', PATH_RESOURCE_NAME),
                ('Attributeless Keyword', 'LibSpecLibrary'),
                #('Attributeless Keyword', 'Spec Resource'),
                ('Testlib Keyword', 'TestLib'),
                ('List Should Contain Value', 'Collections'),
                ('Open Connection', 'Telnet'),
                ('Get Mandatory', 'ArgLib'),
                ('Longest', 'AnotherArgLib') ]

    exp_vars = [ ('${SCALAR}', '<this file>'),
                 ('${RESOURCE var}', 'resource.html'),
                 ('${var_from_file}', 'varz.py'),
                 ('${var_from_resource_var_file}', 'res_var_file.py'),
                 ('${value}', 'dynamic_varz.py') ]

    def setUp(self):
        self.ns = Namespace()
        self.suite = _TestSuiteFactory(SUITEDATA, self.ns)

    def test_content_assist(self):
        data = [('My Test Setup', '<this file>')] + self.exp_kws + self.exp_vars
        for name, source in data:
            self._content_assist_should_contain(name, source)

    def test_content_assist_for_none(self):
        assert_equals(self.ns.content_assist_values(None), [])

    def test_filtering_on_value(self):
        for name, source in [('Read Process Output', 'OperatingSystem'),
                             ('Regexp Escape', 'BuiltIn'),
                             ('Resource UK', 'resource.html')]:
            self._content_assist_should_contain(name, source, 're')
        for name in ['No Operation', 'Testlib Keyword']:
            self._content_assist_should_not_contain(name, 're')

    def test_filtering_with_variable_start_in_end(self):
        values = self.ns.content_assist_values(self.suite, 'start${')
        self._should_contain(values, 'start${SCALAR}', '<this file>')

    def test_get_keywords(self):
        data = [('My Test Setup', self.suite.name)] + self.exp_kws
        for name, source in data:
            self._should_contain(self.ns.get_keywords(self.suite), name, source)

    def test_get_all_keywords(self):
        data = [('My Test Setup', self.suite.name)] + self.exp_kws
        model = DataModel(self.ns)
        model.suite = self.suite
        for name, source in data:
            self._should_contain(self.ns.get_all_keywords(model), name, source)

    def test_items_should_be_in_alphabetical_order(self):
        kws = self.ns.content_assist_values(self.suite)
        assert_true(kws[10].name < kws[11].name < kws[12].name)

    def test_content_assist_values_should_not_have_duplicates(self):
        kws = [ kw for kw in self.ns.content_assist_values(self.suite) if
                kw.name == 'Should Be Equal' ]
        assert_true(len(kws) == 1)

    def test_get_keyword_details(self):
        data = [('Convert To Integer',
                 'Converts the given item to an integer number.'),
                ('BuiltIn.Convert To Integer',
                 'Converts the given item to an integer number.'),
                ('Resource UK',
                 'This is a user keyword from resource file')]
        for name, details in data:
            assert_true(details in self.ns.get_keyword_details(self.suite,
                                                                 name))
        assert_none(self.suite.get_keyword_details('Invalid KW name'))

    def test_get_user_keyword(self):
        for name in ['My Suite Teardown', 'Resource UK',
                     'resource2.Resource2 UK']:
            kw = self.ns.get_user_keyword(self.suite, name)
            assert_equals(kw.name, name.split('.')[-1])

    def test_is_library_keyword(self):
        for name in ['Should Be Equal', 'Copy Directory',
                     'Telnet.Open Connection']:
            assert_true(self.suite.is_library_keyword(name))
        for name in ['Resource UK', 'Invalid']:
            assert_false(self.suite.is_library_keyword(name))

    def test_variables_for_user_keyword_contain_arguments(self):
        kw = self.suite.keywords[1]
        self._should_contain(self.ns.content_assist_values(kw),
                             '${scalar arg}', '<argument>')

    def test_default_values_are_remove_from_uk_arguments(self):
        kw = self.suite.keywords[1]
        self._should_contain(self.ns.content_assist_values(kw),
                             '${default arg}', '<argument>')



class TestModifyingDataAffectsContentAssist(_ContentAssistBaseTest):
    _more_varz = '../resources/more_resources/even_more_varz.py'
    _new_var = ('${var_in_resource2}', 'even_more_varz.py')

    def setUp(self):
        self.ns = Namespace()
        self.suite = _TestSuiteFactory(SUITEDATA, self.ns)

    def test_changing_keywords_in_suite(self):
        self.suite.keywords.new_keyword('New Keyword')
        self._content_assist_should_contain('New Keyword', '<this file>')

    def test_changing_keywords_in_resource(self):
        res = self.suite.get_resources()[0]
        res.keywords.new_keyword('New UK')
        self._should_contain(res.get_keywords(), 'New UK', res.name)
        self._content_assist_should_contain('New UK', res.name)

    def test_adding_variable_file(self):
        self._add_variable_import(self._more_varz)
        self._content_assist_should_contain(*self._new_var)

    def test_updating_variable_file(self):
        self._add_variable_import('invalid.py')
        self._content_assist_should_not_contain('${var_in_resource2}')
        self.suite.settings.imports[-1].set_str_value(self._more_varz)
        self._content_assist_should_contain(*self._new_var)

    def test_deleting_variable_file(self):
        self._add_variable_import(self._more_varz)
        self._content_assist_should_contain(*self._new_var)
        self.suite.settings.imports.pop(-1)
        self._content_assist_should_not_contain('${var_in_resource2}')

    def test_adding_variable_file_in_pythonpath(self):
        path = os.path.join(os.path.dirname(__file__), '..', 'resources',
                            'robotdata', 'resources', 'resources2')
        sys.path.append(path)
        self._add_variable_import('even_more_varz.py')
        self._content_assist_should_contain(*self._new_var)

    def _add_variable_import(self, name):
        self.suite.settings.imports.new_variables(name)


if __name__ == '__main__':
    unittest.main()

