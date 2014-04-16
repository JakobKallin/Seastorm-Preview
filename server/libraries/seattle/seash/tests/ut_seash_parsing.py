"""
Passes a series of commands to the parser in seash_dictionary and make sures
the parser returns the correct input dictionary.

Make sure to update this if the following command's dictionaries changes:
browse
show ownerinfo
set autosave
upload
"""
import seash_dictionary
import command_callbacks


resulting_dictionary = seash_dictionary.parse_command("browse")

expected_dictionary = {'browse':{'name':'browse', 'summary': 'Find vessels I can control', 'callback':command_callbacks.browse, 'help_text':"""
browse [advertisetype]

This command will use the default identity to search for vessels that can
be controlled.   Any vessel with the advertise flag set will be advertised
in at least one advertise service.   browse will look into these services
and add any vessels it can contact.

Setting advertisetype will restrict the advertise lookup to only use that 
service.   Some permitted values for advertisetype are central, DHT, and DOR.

Example:
exampleuser@ !> show targets
%all (empty)
exampleuser@ !> browse
['192.x.x.2:1224', '193.x.x.42:1224', '219.x.x.62:1224']
Added targets: %2(193.x.x.42:1224:v18), %3(219.x.x.62:1224:v4), %1(192.x.x.2:1224:v3)
Added group 'browsegood' with 3 targets
exampleuser@ !> show targets
browsegood ['192.x.x.2:1224:v3', '193.x.x.42:1224:v18', '219.x.x.62:1224:v4']
%3 ['219.x.x.62:1224:v4']
%all ['192.x.x.2:1224:v3', '193.x.x.42:1224:v18', '219.x.x.62:1224:v4']
%1 ['192.x.x.2:1224:v3']
%2 ['193.x.x.42:1224:v18']

""", 'children':{}}}

if not resulting_dictionary == expected_dictionary:
  print "Incorrect values in command dictionary returned from parser: browse"




resulting_dictionary = seash_dictionary.parse_command("show ownerinfo")

expected_dictionary = {'show':{
    'name':'show', 
    'callback':command_callbacks.show, 
    'summary':"Displays the shell state (see 'help show')",
    'help_text':"""
Displays information regarding the current state of Seattle, depending on
the additional keywords that are passed in.

  (*) No need to update prior, the command contacts the nodes anew

""", 'children':{
    'ownerinfo':{
      'name':'ownerinfo', 
      'callback':command_callbacks.show_ownerinfo, 
      'summary': 'Display owner information for the vessels',
      'help_text':"""
show ownerinfo

This lists the ownerinfo strings for vessels in the default group.   See
'set ownerinfo' for more details
""", 'children':{}}}}}

if not resulting_dictionary == expected_dictionary:
  print "Incorrect values in command dictionary returned from parser: show ownerinfo"



resulting_dictionary = seash_dictionary.parse_command("set autosave off")

expected_dictionary = {'set':{'name':'set', 'callback':command_callbacks.set, 'summary': "Changes the shell or vessels (see 'help set')", 'help_text':"""
Changes the shell or vessels.
""", 'children':{
      'autosave':{
        'name':'autosave', 
        'callback':None, 
        'example':'[ on | off ]',
        'summary': "Sets whether to save the state after every command. Set to 'off' by default. The state is saved to a file called 'autosave_keyname', where keyname is the name of the current key you're using.",
        'help_text':"""
set autosave [on/off]

When turned on, the shell settings such as keys, targets, timeout value, etc.
will all be persisted to disk after every operation.   These are saved in a
file called 'autosave_(user's keyname)', which is encrypted with the default identity.   The user
can then restore the shell's state by typing 'loadstate identity'.

Example:
exampleuser@%1 !> set autosave on
exampleuser@%1 !> exit
(restart seash.py)
 !> loadkeys exampleuser
 !> as exampleuser
exampleuser@ !> loadstate autosave_exampleuser
exampleuser@%1 !>

""", 'children':{
          'off':{'name':'args', 'callback':command_callbacks.set_autosave_arg, 'help_text':'', 'children':{}},
      }},
  }}}

if not resulting_dictionary == expected_dictionary:
  print "Incorrect values in command dictionary returned from parser for command: set autosave off"



resulting_dictionary = seash_dictionary.parse_command("upload files.txt")

expected_dictionary = {
  'upload':{
    'name':'upload', 
    'callback':None, 
    'example':'localfn (remotefn)',
    'summary': 'Upload a file',
    'help_text':"""
upload srcfilename [destfilename]

Uploads a file into all vessels in the default group.   The file name that is
created in those vessels is destfilename (or srcfilename by default).

Example:
exampleuser@%1 !> show files
Files on '192.x.x.2:1224:v3': ''
exampleuser@%1 !> upload example.1.1.repy
exampleuser@%1 !> show files
Files on '192.x.x.2:1224:v3': 'example.1.1.repy'

""", 'children':{
      'files.txt':{'name':'filename', 'callback':command_callbacks.upload_filename, 'help_text':'', 'children':{}}}}}

if not resulting_dictionary == expected_dictionary:
  print "Incorrect values in command dictionary returned from parser: upload files.txt"




resulting_dictionary = seash_dictionary.parse_command("upload files.txt apples and oranges")

expected_dictionary = {
  'upload':{
    'name':'upload', 
    'callback':None, 
    'example': 'localfn (remotefn)',
    'summary': 'Upload a file',
    'help_text':"""
upload srcfilename [destfilename]

Uploads a file into all vessels in the default group.   The file name that is
created in those vessels is destfilename (or srcfilename by default).

Example:
exampleuser@%1 !> show files
Files on '192.x.x.2:1224:v3': ''
exampleuser@%1 !> upload example.1.1.repy
exampleuser@%1 !> show files
Files on '192.x.x.2:1224:v3': 'example.1.1.repy'

""", 'children':{
      'files.txt':{'name':'filename', 'callback':command_callbacks.upload_filename, 'help_text':'', 'children':{
          'apples and oranges':{'name':'args', 'callback':command_callbacks.upload_filename_remotefn, 'help_text':'', 'children':{}}
      }},
  }}}

if not resulting_dictionary == expected_dictionary:
  print "Incorrect values in command dictionary returned from parser: upload files.txt apples and oranges"
