import sublime_plugin
import sublime
import subprocess
import tempfile
import os

SETTINGS = sublime.load_settings('Crystal.sublime-settings')

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

    subprocess.call([SETTINGS.get("crystal_cmd"), "tool", "format", tmp.name])

    with open(tmp.name, 'r') as formatted_file:
      self.view.replace(edit, region, formatted_file.read())

    os.unlink(tmp.name)
