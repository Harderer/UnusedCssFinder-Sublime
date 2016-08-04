# UnusedCssFinder-Sublime
> Only supports **Sublime Text 3**.

Sublime plugin to find unused css names

Author: Jannis Harder: jannisharder@hotmail.de

Last modified: 04 August 2016

Plugin to find unused css declarations in a project. Searches for all id and class names inside current open project or file directory if no project is currently open. All css names that do not occur once in any other .php, .html, .xhtml or .js file is highlighted.

Might run slow on big projects, do not hesitate to send me improvement recommendations as this is my first sublime plugin.

### Usage

`Inline CSS`: Open the file and press `ctrl` + `u` + `f` to find css declarations without any occurence in the current file.

`Extern CSS`: Open any *.css file and press `ctrl` + `u` + `f` to find css declarations without any occurence in the current project. If no project is active, the search takes place at the css file location.
All unused css names will be highlighted in the search. To remove the highlighting with press the same key-shortcut again.

### Key Bindings

Default Key Bindings for Mac:
```
{ "keys": ["super+u", "super+f"], "command": "unused_css_finder"}
```

Default Key Bindings for Windows/Linux:
```
{ "keys": ["ctrl+u", "ctrl+f"], "command": "unused_css_finder"}
```

### Settings

`unused_css_ignore_folders`: any folder added here will be ignored in the search for occurences of the css names
`unused_css_scan_only_folders`: if you want to search explicitly in only some folder, define them here and a search will only happen in a folder, it its name is in this list. **Important**: Add them as object with the folders being the keys and a boolean as value. The boolean defines, if all subfolders in this folder are allowed to be included in the search.
