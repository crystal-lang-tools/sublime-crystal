import sublime_plugin
import sublime
import subprocess
from .diff_match_patch import diff_match_patch
import json

class CrystalPluginListener(sublime_plugin.EventListener):
  def on_pre_save(self, view):
    settings = sublime.load_settings('Crystal.sublime-settings')
    if settings.get('auto_format'):
      view.run_command('crystal_format')

class CrystalFormatCommand(sublime_plugin.TextCommand):
  def is_enabled(self):
    caret = self.view.sel()[0].a
    syntax_name = self.view.scope_name(caret)
    return "source.crystal" in syntax_name

  def has_redo(self):
    cmd, args, repeat = self.view.command_history(1)
    return cmd != ''

  def run(self, edit):
    vsize = self.view.size()
    region = sublime.Region(0, vsize)
    src = self.view.substr(region)
    window = self.view.window()

    settings = sublime.load_settings('Crystal.sublime-settings')
    with subprocess.Popen([settings.get("crystal_cmd"), "tool", "format", "-", "--format", "json"], stdin = subprocess.PIPE, stdout = subprocess.PIPE) as proc:
      proc.stdin.write(bytes(src, 'UTF-8'))
      proc.stdin.close()
      output = proc.stdout.read().decode('UTF-8')
      exit = proc.wait()

    pos = 0
    if exit == 0:
      if not self.has_redo():
        for op, text in diff_match_patch().diff_main(src, output):
          if op == diff_match_patch.DIFF_DELETE:
            self.view.erase(edit, sublime.Region(pos, pos + len(text)))
          if op == diff_match_patch.DIFF_INSERT:
            self.view.insert(edit, pos, text)
            pos += len(text)
          if op == diff_match_patch.DIFF_EQUAL:
            pos += len(text)

      self.view.erase_regions('crystal_errors')
      window.run_command("hide_panel")

    else:
      error = json.loads(output)
      error_pos = self.view.text_point(error[0]["line"] - 1, error[0]["column"] - 1)
      line_region = self.view.full_line(error_pos)
      self.view.add_regions('crystal_errors', [line_region], 'comment', 'dot')

      error_panel = window.create_output_panel('crystal_errors')
      error_panel.run_command("append", {"characters":
        "Error at line %d, column %d: %s" % (error[0]["line"], error[0]["column"], error[0]['message'])
      })
      window.run_command("show_panel", {"panel": "output.crystal_errors"})
