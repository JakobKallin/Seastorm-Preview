"""
<Program Name>
  conflict/__init__.py

<Purpose>
  Module that is used with ut_seash_moduleconflicterror.py.  It should not be
  enabled successfully, as it will conflict with the default 'show' command.

  Other fields are simply defined so that the module importer can import the
  module without problems.
"""

moduledata = {
  'help_text': '',
  'url': None,
  'command_dict': {
    'show': { 'name':'nonexistant', 'help_text': 'bad help text',
              'callback': None, 'children': {}},
  }
}