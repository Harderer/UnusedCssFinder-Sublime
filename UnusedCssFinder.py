import sublime, sublime_plugin, os, re, string, time
from os import listdir

UCF_IS_ACTIVE = {}
ALLOWED_EXTENSIONS = ["php", "html", "xhtml", "js"]

class UnusedCssFinderCommand(sublime_plugin.TextCommand):
	
	def run(self, edit):
		sublime.set_timeout_async(self.async_search, 1)

	def load_plugin_setting(self, setting_name):

		# get plugin settings
		settings_plugin = sublime.load_settings('UnusedCssFinder.sublime-settings')
		setting_value_plugin = settings_plugin.get(setting_name)
		if setting_value_plugin != None and setting_value_plugin != "":
			return setting_value_plugin

		return None

	def async_search(self):
		global UCF_IS_ACTIVE
		
		view = self.view
		regions = [sublime.Region(0, view.size())]

		filename = self.view.file_name()
		ignoreFolders = []
		scanOnlyFolders = False

		project_rootpath = self.get_active_project_path(filename)
		setting_identifier = re.sub('[\W_]', '', project_rootpath)

		# initialize project plugin status if necessary
		if(project_rootpath not in UCF_IS_ACTIVE):
			UCF_IS_ACTIVE[project_rootpath] = False

		# get settings
		st_rootFolder = self.load_plugin_setting('unused_css_root_folder')
		st_ignoreFolders = self.load_plugin_setting('unused_css_ignore_folders')
		st_scanOnlyFolders = self.load_plugin_setting('unused_css_scan_only_folders')

		if st_rootFolder != None and st_rootFolder != "":
			project_rootpath = st_rootFolder
		if st_ignoreFolders != None and st_ignoreFolders != "":
			ignoreFolders = st_ignoreFolders
		if st_scanOnlyFolders != None and st_scanOnlyFolders != "":
			scanOnlyFolders = st_scanOnlyFolders

		highlight_size = int(view.settings().get('highlight_size_'+setting_identifier, 0))
		ufIsActive = False

		if not UCF_IS_ACTIVE[project_rootpath] or highlight_size <= 0:
			self.search_areas(setting_identifier, filename, project_rootpath, ignoreFolders, scanOnlyFolders)
			ufIsActive = True
		else:
			tests = self.remove_highlighting(view, setting_identifier, highlight_size)
			ufIsActive = False

		UCF_IS_ACTIVE[project_rootpath] = ufIsActive

	def remove_highlighting(self, view, setting_identifier, highlight_size):
		for i in range(highlight_size):
			if len(view.get_regions('highlight_word_%d'%i)) > 0:
				view.erase_regions('highlight_word_%d'%i)

		view.settings().set('highlight_size_'+setting_identifier, 0)

	def search_areas(self, setting_identifier, filename, project_rootpath, ignoreFolders, scanOnlyFolders):
		# get all class and ids from file
		fileContent = open(filename).read().lstrip().replace('\r', ' ').replace('\n', ' ')
		fileContent = re.sub('{[^}]*}', '', fileContent)	# remove all content between brackets

		fileExtension = os.path.splitext(filename)[1][1:]

		word_count = 0
		unusedHits = 0

		if fileExtension == "css":
			words = fileContent.split(" ")	# determine all words in file
			word_length = len(words)

			unusedHits += self.search_words(setting_identifier, filename, project_rootpath, ignoreFolders, scanOnlyFolders, words, word_count, word_length, unusedHits, False)
		else:
			# css inside file, search only in current file
			cssContents = re.findall('<style[^>]*>([^(<)]*)', fileContent)	# determine all contents between style tags
			words = []
			for (index, content) in enumerate(cssContents):
				words.extend(content.split(" "))		# determine all words in contents
			word_length = len(words)

			unusedHits += self.search_words(setting_identifier, filename, project_rootpath, ignoreFolders, scanOnlyFolders, words, word_count, word_length, unusedHits, True)
			
		self.view.settings().set('highlight_size_'+setting_identifier, unusedHits)
		sublime.status_message("{:6.2f}%".format(100)+": "+str(unusedHits)+" unused css names found")

	def search_words(self, setting_identifier, filename, project_rootpath, ignoreFolders, scanOnlyFolders, words, word_count, word_length, unusedHits, css_inside_file):
		
		for word in words:
			word = word.strip(' \t\n\r')
			if(word != ""):
				if (word.startswith(".") or word.startswith("#")):	# get only class and id definitions

					# remove all css attribut testers and subclasses like [type=text] or :hover or .inactive and split by , for classlists
					classIdNameSplitted = re.sub('[.:[](.)*', '', word[1:]).replace(',', ' ').split(" ")
					for classIdName in classIdNameSplitted:
						classIdName = classIdName.strip(' \t\n\r')
						if classIdName != "":
							# search all files in folder and subfolders for given class or id name
							appearanceFound = self.search_in_folder(project_rootpath, filename, classIdName, ignoreFolders, scanOnlyFolders, css_inside_file)

							# highlight name if appearance was not found
							if not appearanceFound:
								regions = self.view.find_all(word, sublime.IGNORECASE)
								self.view.add_regions('highlight_word_%d'%unusedHits, regions, 'invalid')

								unusedHits+=1

			word_count+=1
			sublime.status_message("{:6.2f}%".format((word_count/word_length)*100)+": "+str(unusedHits)+" unused css names found")

		return unusedHits

	def search_in_folder(self, folderpath, trigger_filename, search_for, ignoreFolders, scanOnlyFolders, css_inside_file):
		appearanceFound = False
		if scanOnlyFolders == False or len(scanOnlyFolders) == 0 or folderpath in scanOnlyFolders:
			for f in listdir(folderpath):
				filepath = os.path.join(folderpath, f)

				if(os.path.isfile(filepath)):
					appearanceFound = self.search_in_file(filepath, trigger_filename, search_for, css_inside_file)
				if(os.path.isdir(filepath) and filepath not in ignoreFolders):
					if scanOnlyFolders != False and len(scanOnlyFolders) > 0 and scanOnlyFolders[folderpath] == True:
						# scan only folder setting says to scan all subfolders aswell
						appearanceFound = self.search_in_folder(filepath, trigger_filename, search_for, ignoreFolders, False, css_inside_file)
					else:
						appearanceFound = self.search_in_folder(filepath, trigger_filename, search_for, ignoreFolders, scanOnlyFolders, css_inside_file)

				if appearanceFound:
					return appearanceFound

		return appearanceFound

	def search_in_file(self, filepath, trigger_filename, search_for, css_inside_file):
		extension = os.path.splitext(filepath)[1][1:]
		if(extension in ALLOWED_EXTENSIONS):
			if (filepath != trigger_filename and not css_inside_file) or (filepath == trigger_filename and css_inside_file):
				try:
					fileContent = open(filepath).read()
					if(css_inside_file):
						fileContent = re.sub(re.compile('<style[^>]*>.*?</style>', re.DOTALL), '', fileContent)
					return (search_for in fileContent)
				except UnicodeDecodeError:
					return False
			return False
	
	def get_active_project_path(self, filename):
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
