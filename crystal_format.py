import sublime_plugin
import sublime
import subprocess
import tempfile
import os
import difflib

class CrystalPluginListener(sublime_plugin.EventListener):
  def on_pre_save(self, view):
    view.run_command('crystal_format')

class CrystalFormatCommand(sublime_plugin.TextCommand):
  def is_enabled(self):
    caret = self.view.sel()[0].a
    syntax_name = self.view.scope_name(caret)
    return "source.crystal" in syntax_name

  def run(self, edit):
    vsize = self.view.size()
    region = sublime.Region(0, vsize)
    src = self.view.substr(region)

    with tempfile.NamedTemporaryFile(mode = 'w+t', delete = False) as tmp:
      tmp.write(src)

    settings = sublime.load_settings('Crystal.sublime-settings')
    subprocess.call([settings.get("crystal_cmd"), "tool", "format", tmp.name])

    with open(tmp.name, 'r') as formatted_file:
      formatted = formatted_file.read()
    os.unlink(tmp.name)

    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, src, formatted).get_opcodes():
      if op == 'insert':
        self.view.insert(edit, j1, formatted[j1:j2])
        next
      if op == 'delete':
        self.view.erase(edit, sublime.Region(j1, j1 + (i2 - i1)))
        next
      if op == 'replace':
        self.view.replace(edit, sublime.Region(j1, j1 + (i2 - i1)), formatted[j1:j2])
