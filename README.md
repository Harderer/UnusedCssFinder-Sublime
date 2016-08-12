# UnusedCssFinder-Sublime
> Only supports **Sublime Text 3**.

Sublime plugin to find unused css names

Author: Jannis Harder: jannisharder@hotmail.de

Last modified: 12 August 2016

Plugin to find unused css declarations in a project. Searches for all id and class names inside current open project or file directory if no project is currently open. All css names that do not occur once in any other .php, .html, .xhtml or .js file will be selected.

![Default](http://i.giphy.com/l3vR2PVN2FHWrhWow.gif)

Might run slow on big projects, do not hesitate to send me improvement recommendations as this is my first sublime plugin.

### Usage

`Inline CSS`: Open the file and press `ctrl` + `u` + `f` to find css declarations without any occurence in the current file.

`Extern CSS`: Open any *.css file and press `ctrl` + `u` + `f` to find css declarations without any occurence in the current project. If no project is active, the search takes place at the css file location.

### Default Key Bindings

for Mac:
```
{ "keys": ["super+u", "super+f"], "command": "unused_css_finder"}
```

for Windows/Linux:
```
{ "keys": ["ctrl+u", "ctrl+f"], "command": "unused_css_finder"}
```

### Settings

- `unused_css_root_folder`: define a projects root location if ti deviates from the sublime projects root location.
- `unused_css_ignore_folders`: any folder added here will be ignored in the search for occurences of the css names.
- `unused_css_scan_only_folders`: if you want to search explicitly in only some folder, define them here and a search will only happen in a folder, it its name is in this list. **Important**: Add them as object with the folders being the keys and a boolean as value. The boolean defines, if all subfolders in this folder are allowed to be included in the search.
- `unused_css_ignore_selectors`*: define any selectors, that should be ignored in the search. Can be defined with class or id selcetor or as plain selector name. (e.g. "#example", ".example" or "example")
- `unused_css_highlight_selectors`*: if true, the found selectors won't be selected via cursor but highlighted. The highlighting can be removed by running the same command again.

![Highlighting](http://i.giphy.com/3oz8xQX86kktBcYDZu.gif)

- `unused_css_delete_on_search`*: deletes all unused selectors after search if true. Be sure to add composited html classes and ids to the ignored selectors list. e.g. if you have a class declaration like "test_"+true_or_false, add "test_false" and "test_true" to ignore - they would be deleted otherwise.

![AutoDelete](http://i.giphy.com/3oz8xAQ1DoHkfcznqg.gif)

*All these settings can be configured over the context menu on right click also. Clicking "Add To Selectors Ignore List" will add all selected elements to the list.

### Project Settings

You can also define all the above settings in an individual "unused_css.cfg" file for each project, that needs to be located in the projects rootpath. All settings in the file will be appended to the default/user settings or override the settings, if it's a boolean value. 

### Change Log

v.1.3.0

- settings can now be configured over a project specific file "unused_css.cfg" that has to be located in a projects root path
- added 'unused_css_ignore_selectors' setting: Every element in this array will be ignored in the search and never be stated as non occured selector. Can also be defined as id or class selector, e.g. "#example", ".example", "example"
- added 'unused_css_delete_on_search' setting: Every unused css selector that was found during the search will be removed after the search
- switched default behaviour of plugin. Instead of highlighting every unused selector, they will be selected via cursor, to be able to remove them with one backspace press
- added 'unused_css_highlight_selectors' setting: switch to old behaviour, that unused selectors will be highlighted instead of selected via cursor
- added plugin to sublime context menu on right click to be able to configure some settings and also run the command without shortcut
- most of these changes are based on the ideas from NoxNoctis2, thanks for that

v.1.2.2

- optimized the search patterns to only find the exact selector names and no words where they occur as substring

v.1.2.1

- fixed a bug in the plugin default settings file
- added debugging functionality

v.1.2.0

- the plugin now works for inline css as well
- added configuration path into sublime menu: "Preferences/Package Settings/UnusedCssFinder/"
- Added default key bindings to the project

v.1.1.0

- Added settings to define folders, in which the search takes place
- Fixed a bug to truely search asynchronously
