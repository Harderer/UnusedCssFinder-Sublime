import sublime, sublime_plugin, os, re
from os import listdir

# add to 'Key Bindings - User' as shortcut:
# { "keys": ["ctrl+u", "ctrl+f"], "command": "find_unused_css"}

UU_IS_ACTIVE = False
ALLOWED_EXTENSIONS = ["php", "html", "xhtml", "js"]

class FindUnusedCssCommand(sublime_plugin.TextCommand):
	
	def run(self, edit):
		sublime.set_timeout_async(self.async_search(edit), 0)

	def async_search(self, edit):
		global UU_IS_ACTIVE
		
		view = self.view
		regions = [sublime.Region(0, view.size())]

		filename = self.view.file_name()
		ignoreFolders = []

		project_rootpath = self.get_active_project_path(filename)

		# get plugin settings
		settings = sublime.load_settings('Preferences.sublime-settings')
		st_rootFolder = settings.get('unused_css_root_folder')
		st_ignoreFolders = settings.get('unused_css_ignore_folders')
		if st_rootFolder != None and st_rootFolder != "":
			# use root path from settings if set
			project_rootpath = st_rootFolder
		if st_ignoreFolders != None:
			# get list of folders to ignore from plugin settings
			ignoreFolders = st_ignoreFolders

		if UU_IS_ACTIVE:
			self.search_words(edit, filename, project_rootpath, ignoreFolders)
		else:
			self.remove_highlighting(view)

		UU_IS_ACTIVE = not UU_IS_ACTIVE

	def remove_highlighting(self, view):
		size = view.settings().get('highlight_size', 0)
		for i in range(size):
			view.erase_regions('highlight_word_%d'%i)

		view.settings().set('highlight_size', 0)

	def search_words(self, edit, filename, project_rootpath, ignoreFolders):
		# get all class and ids from file
		fileContent = open(filename).read().lstrip().replace('\r', ' ').replace('\n', ' ')
		fileContent = re.sub('{[^}]*}', '', fileContent)	# remove all content between brackets

		view = self.view

		unusedHits = 0
		words = fileContent.split(" ")	# determine all words in file
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
							appearanceFound = self.search_in_folder(project_rootpath, filename, classIdName, ignoreFolders)

							# print name if appearance was not found
							if not appearanceFound:
								regions = view.find_all(word, sublime.IGNORECASE)
								view.add_regions('highlight_word_%d'%unusedHits, regions, 'invalid')

								unusedHits+=1
		
		view.settings().set('highlight_size', unusedHits)
		print(str(unusedHits)+" unused css names found")

	def search_in_folder(self, folderpath, trigger_filename, search_for, ignoreFolders):
		appearanceFound = False
		for f in listdir(folderpath):
			filepath = folderpath+"\\"+f

			if(os.path.isfile(filepath)):
				appearanceFound = self.search_in_file(filepath, trigger_filename, search_for)
			if(os.path.isdir(filepath) and filepath not in ignoreFolders):
				appearanceFound = self.search_in_folder(filepath, trigger_filename, search_for, ignoreFolders)

			if appearanceFound:
				return appearanceFound

		return appearanceFound

	def search_in_file(self, filepath, trigger_filename, search_for):
		extension = os.path.splitext(filepath)[1][1:]
		if(extension in ALLOWED_EXTENSIONS):
			if(filepath != trigger_filename):
				try:
					return (search_for in open(filepath).read())
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
