import sublime, sublime_plugin, os, re, string, time, json
from os import listdir

UCF_IS_ACTIVE = {}
ALLOWED_EXTENSIONS = ["php", "html", "xhtml", "js"]

class UnusedCssFinderCommand(sublime_plugin.TextCommand):

	def run(self, edit, **args):
		self.debug = args['debug'] if 'debug' in args else False
		sublime.set_timeout_async(self.async_search, 1)

	def load_plugin_setting(self, setting_name):

		plugin_setting_value = None

		# get plugin settings
		plugin_settings = sublime.load_settings('UnusedCssFinder.sublime-settings')
		setting_value = plugin_settings.get(setting_name)
		if setting_value != None and setting_value != "":
			plugin_setting_value = setting_value

		# get settings from plugin configuration file in folder
		if self.project_settings is not False:
			if setting_name in self.project_settings:
				if(isinstance(self.project_settings[setting_name], list) and isinstance(plugin_setting_value, list)):
					for value in self.project_settings[setting_name]:
						plugin_setting_value.append(value)
				elif(isinstance(self.project_settings[setting_name], dict) and isinstance(plugin_setting_value, dict)):
					for (key, value) in self.project_settings[setting_name].items():
						plugin_setting_value[key] = value
				else:
					plugin_setting_value = self.project_settings[setting_name]

		return plugin_setting_value

	def async_search(self):
		global UCF_IS_ACTIVE

		regions = [sublime.Region(0, self.view.size())]

		filename = self.view.file_name()

		self.project_rootpath = unused_css_get_active_project_path(filename)
		self.ignoreFolders = []
		self.scanOnlyFolders = False
		self.ignoreSelectors = []
		self.autoDelete = False
		self.hightlightUnusedSelectors = False

		setting_identifier = re.sub('[\W_]', '', self.project_rootpath)

		# initialize project plugin status if necessary
		if(self.project_rootpath not in UCF_IS_ACTIVE):
			UCF_IS_ACTIVE[self.project_rootpath] = False

		self.project_settings = False
		project_settings_filename = os.path.join(self.project_rootpath, "unused_css.cfg")
		if os.path.isfile(project_settings_filename):
			try:
				self.project_settings = json.loads(open(project_settings_filename).read())
			except ValueError:
				self.view.show_popup("Info: JSON data couldn't be loaded from "+project_settings_filename)

		# get settings
		st_rootFolder = self.load_plugin_setting('unused_css_root_folder')
		st_ignoreFolders = self.load_plugin_setting('unused_css_ignore_folders')
		st_scanOnlyFolders = self.load_plugin_setting('unused_css_scan_only_folders')
		st_ignoreSelectors = self.load_plugin_setting('unused_css_ignore_selectors')
		st_autoDelete = self.load_plugin_setting('unused_css_delete_on_search')
		st_hightlightUnusedSelectors = self.load_plugin_setting('unused_css_highlight_selectors')

		if st_rootFolder != None and st_rootFolder != "":
			self.project_rootpath = st_rootFolder
		if st_ignoreFolders != None and st_ignoreFolders != "":
			self.ignoreFolders = st_ignoreFolders
		if st_scanOnlyFolders != None and st_scanOnlyFolders != "":
			self.scanOnlyFolders = st_scanOnlyFolders
		if st_ignoreSelectors != None and st_ignoreSelectors != "":
			self.ignoreSelectors = st_ignoreSelectors
		if st_autoDelete != None:
			self.autoDelete = st_autoDelete
		if st_hightlightUnusedSelectors != None:
			self.hightlightUnusedSelectors = st_hightlightUnusedSelectors

		highlight_size = int(self.view.settings().get('highlight_size_'+setting_identifier, 0))
		ufIsActive = False

		self.remove_highlighting(self.view, setting_identifier, highlight_size)

		if not UCF_IS_ACTIVE[self.project_rootpath] or highlight_size <= 0 or self.hightlightUnusedSelectors is False:
			self.view.sel().clear()

			self.search_areas(setting_identifier, filename)
			ufIsActive = True

			if self.autoDelete:
				self.view.run_command("left_delete")
		else:
			ufIsActive = False

		# workaround for viewport bug
		vpos = self.view.viewport_position()
		self.view.set_viewport_position((vpos[0], vpos[1]+1))
		self.view.set_viewport_position((vpos[0], vpos[1]-1))
		####

		UCF_IS_ACTIVE[self.project_rootpath] = ufIsActive

	def remove_highlighting(self, view, setting_identifier, highlight_size):
		for i in range(highlight_size):
			if len(view.get_regions('highlight_word_%d'%i)) > 0:
				view.erase_regions('highlight_word_%d'%i)

		view.settings().set('highlight_size_'+setting_identifier, 0)

	def search_areas(self, setting_identifier, filename):
		# get all class and ids from file
		self.file_content = self.view.substr(sublime.Region(0, self.view.size()))
		file_content_stripped = re.sub('{[^}]*}', '', self.file_content.lstrip().replace('\r', ' ').replace('\n', ' '))	# remove all content between brackets

		fileExtension = os.path.splitext(filename)[1][1:]

		word_count = 0
		unusedHits = 0

		if fileExtension == "css":
			words = file_content_stripped.split(" ")	# determine all words in file
			word_length = len(words)

			unusedHits += self.search_words(setting_identifier, filename, words, word_count, word_length, unusedHits, False)
		else:
			# css inside file, search only in current file
			cssContents = re.findall('<style[^>]*>([^(<)]*)', file_content_stripped)	# determine all contents between style tags
			words = []
			for (index, content) in enumerate(cssContents):
				words.extend(content.split(" "))		# determine all words in contents
			word_length = len(words)

			unusedHits += self.search_words(setting_identifier, filename, words, word_count, word_length, unusedHits, True)
			
		self.view.settings().set('highlight_size_'+setting_identifier, unusedHits)
		sublime.status_message("{:6.2f}%".format(100)+": "+str(unusedHits)+" unused css names found")

	def search_words(self, setting_identifier, filename, words, word_count, word_length, unusedHits, css_inside_file):

		searched_selectors = []
		
		for word in words:
			word = word.strip(' \t\n\r')
			if(word != ""):
				if (word.startswith(".") or word.startswith("#")):	# get only class and id definitions

					# remove all css attribut testers and subclasses like [type=text] or :hover or .inactive and split by , for classlists
					classIdNameSplitted = re.sub('[.:[](.)*', '', word[1:]).replace(',', ' ').split(" ")
					for classIdName in classIdNameSplitted:
						classIdName = classIdName.strip(' \t\n\r')
						if classIdName != "" and classIdName not in searched_selectors:

							searched_selectors.append(classIdName)

							if ((word[0:1]+classIdName) not in self.ignoreSelectors and classIdName not in self.ignoreSelectors):
								if(self.debug):
									print("search for '"+classIdName+"' in")
								# search all files in folder and subfolders for given class or id name
								appearanceFound = self.search_in_folder(self.project_rootpath, filename, classIdName, css_inside_file)

								# highlight name if appearance was not found
								if not appearanceFound:
									if(self.debug):
										print(">> no match found")

									# regions = self.view.find_all('(?<!\w)('+word+')(?!\w).*(?<=\{).*(?<=\})', sublime.IGNORECASE)
									matches = re.finditer(re.compile('(?<!\w)('+word+')(?!\w)[^{]*{[^}]*}', re.DOTALL), self.file_content)

									if self.hightlightUnusedSelectors:
										self.view.add_regions('highlight_word_%d'%unusedHits, self.view.find_all('(?<!\w)('+word+')(?!\w)', sublime.IGNORECASE), 'invalid')
									
									if not self.hightlightUnusedSelectors or self.autoDelete:
										for match in matches:
											region = sublime.Region(match.start(0), match.end(0))
											self.view.sel().add(region)

									unusedHits+=1

								if(self.debug):
									print("-----------")

			word_count+=1
			sublime.status_message("{:6.2f}%".format((word_count/word_length)*100)+": "+str(unusedHits)+" unused css names found")

		return unusedHits

	def search_in_folder(self, folderpath, trigger_filename, search_for, css_inside_file):
		appearanceFound = False
		if self.scanOnlyFolders == False or len(self.scanOnlyFolders) == 0 or folderpath in self.scanOnlyFolders:
			for f in listdir(folderpath):
				filepath = os.path.join(folderpath, f)

				if(os.path.isfile(filepath)):
					appearanceFound = self.search_in_file(filepath, trigger_filename, search_for, css_inside_file)
				if(os.path.isdir(filepath) and filepath not in self.ignoreFolders):
					if self.scanOnlyFolders != False and len(self.scanOnlyFolders) > 0 and self.scanOnlyFolders[folderpath] == True:
						# scan only folder setting says to scan all subfolders aswell
						appearanceFound = self.search_in_folder(filepath, trigger_filename, search_for, self.ignoreFolders, False, css_inside_file)
					else:
						appearanceFound = self.search_in_folder(filepath, trigger_filename, search_for, css_inside_file)

				if appearanceFound:
					if(self.debug):
						print(">> match")
					return appearanceFound

		return appearanceFound

	def search_in_file(self, filepath, trigger_filename, search_for, css_inside_file):
		extension = os.path.splitext(filepath)[1][1:]
		if(extension in ALLOWED_EXTENSIONS):
			if (filepath != trigger_filename and not css_inside_file) or (filepath == trigger_filename and css_inside_file):
				try:
					if(self.debug):
						print(">> "+filepath)
					fileContent = open(filepath).read()
					if(css_inside_file):
						fileContent = re.sub(re.compile('<style[^>]*>.*?</style>', re.DOTALL), '', fileContent)

					return (re.search('(?<!\w)('+search_for+')(?!\w)', fileContent) is not None)
				except UnicodeDecodeError:
					return False
			return False
	
def unused_css_get_active_project_path(filename):
	window = sublime.active_window()
	folders = window.folders()
	if len(folders) == 1:
		return folders[0]
	else:
		active_view = window.active_view()
		active_file_name = active_view.file_name() if active_view else None
		
		if not active_file_name:
			return folders[0] if len(folders) else os.path.dirname(filename)
		for folder in folders:
			if active_file_name.startswith(folder):
				return folder
	return os.path.dirname(active_file_name)


class addToIgnoreListCommand(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		selected_region = self.view.sel()[0]
		if selected_region.begin() != selected_region.end():
			add_to_ignore = self.view.substr(sublime.Region(selected_region.begin(), selected_region.end()))
			if add_to_ignore != "":
				plugin_settings = sublime.load_settings('UnusedCssFinder.sublime-settings')
				ignoreSelectors = plugin_settings.get('unused_css_ignore_selectors')
				if add_to_ignore not in ignoreSelectors:
					ignoreSelectors.append(add_to_ignore)
					plugin_settings.set('unused_css_ignore_selectors', ignoreSelectors)
					sublime.save_settings('UnusedCssFinder.sublime-settings')
	def is_enabled(self):
		selected_region = self.view.sel()[0]
		if selected_region.begin() != selected_region.end():
			add_to_ignore = self.view.substr(sublime.Region(selected_region.begin(), selected_region.end()))
			if add_to_ignore != "":
				return True

		return False
		
class checkHighlightSelectors(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		plugin_settings = sublime.load_settings('UnusedCssFinder.sublime-settings')
		plugin_settings.set('unused_css_highlight_selectors', True)
		sublime.save_settings('UnusedCssFinder.sublime-settings')

		filename = self.view.file_name()
		project_rootpath = unused_css_get_active_project_path(filename)
		UCF_IS_ACTIVE[project_rootpath] = False

	def is_checked(self):
		plugin_settings = sublime.load_settings('UnusedCssFinder.sublime-settings')
		return (plugin_settings.get('unused_css_highlight_selectors') is True)
		

class uncheckHighlightSelectors(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		plugin_settings = sublime.load_settings('UnusedCssFinder.sublime-settings')
		plugin_settings.set('unused_css_highlight_selectors', False)
		sublime.save_settings('UnusedCssFinder.sublime-settings')
	def is_checked(self):
		plugin_settings = sublime.load_settings('UnusedCssFinder.sublime-settings')
		return (plugin_settings.get('unused_css_highlight_selectors') is not True)
		
class checkAutoDelete(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		plugin_settings = sublime.load_settings('UnusedCssFinder.sublime-settings')
		plugin_settings.set('unused_css_delete_on_search', True)
		sublime.save_settings('UnusedCssFinder.sublime-settings')
	def is_checked(self):
		plugin_settings = sublime.load_settings('UnusedCssFinder.sublime-settings')
		return (plugin_settings.get('unused_css_delete_on_search') is True)

class uncheckAutoDelete(sublime_plugin.TextCommand):
	def run(self, edit, **args):
		plugin_settings = sublime.load_settings('UnusedCssFinder.sublime-settings')
		plugin_settings.set('unused_css_delete_on_search', False)
		sublime.save_settings('UnusedCssFinder.sublime-settings')
	def is_checked(self):
		plugin_settings = sublime.load_settings('UnusedCssFinder.sublime-settings')
		return (plugin_settings.get('unused_css_delete_on_search') is not True)
