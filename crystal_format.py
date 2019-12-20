import json
import subprocess
import sys
import re
import os

import sublime_plugin
import sublime
from .diff_match_patch import diff_match_patch

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
    #command = [settings.get("crystal_cmd"), "tool", "format", "-", "--format", "json"]
    command = [settings.get("crystal_cmd"), "tool", "format", "-", "--no-color"]

    # for Windows Subsystem for Linux
    if os.name == "nt": command.insert(0, "wsl")

    popen_args = dict(args=command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Prevent flashing terminal windows
    if sys.platform.startswith('win'):
      popen_args['startupinfo'] = subprocess.STARTUPINFO()
      popen_args['startupinfo'].dwFlags |= subprocess.STARTF_USESHOWWINDOW

    proc = subprocess.Popen(**popen_args)
    stdout, stderr = proc.communicate(src.encode('utf-8'))
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    exit = proc.returncode

    pos = 0
    if exit == 0:
      if not self.has_redo():
        for op, text in diff_match_patch().diff_main(src, stdout):
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
      error_line = None
      error_column = None
      pattern = r"syntax error in '.+?:(\d+):(\d+)': (.+)"
      match = re.match(pattern, stderr)
      if match:
        error_line = int(match.group(1))
        error_column = int(match.group(2))
        error = match.group(3)
      else:
        error_line = None
        error_column = None
        error = stderr

      if error_line and error_column:
        error_pos = self.view.text_point(error_line - 1, error_column - 1)
        line_region = self.view.full_line(error_pos)
        self.view.add_regions('crystal_errors', [line_region], 'comment', 'dot', sublime.DRAW_NO_FILL)

      error_panel = window.create_output_panel('crystal_errors')

      if error_line and error_column:
        error_panel.run_command("append", {"characters":
          "Error at line %d, column %d: %s" % (error_line, error_column, error)
        })
      else:
        error_panel.run_command("append", {"characters": error})

      window.run_command("show_panel", {"panel": "output.crystal_errors"})
