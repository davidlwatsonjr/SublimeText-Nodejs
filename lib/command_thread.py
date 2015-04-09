import os
import sublime
import functools
import threading
import subprocess

def main_thread(callback, *args, **kwargs):
  # sublime.set_timeout gets used to send things onto the main thread
  # most sublime.[something] calls need to be on the main thread
  sublime.set_timeout(functools.partial(callback, *args, **kwargs), 0)

class CommandThread(threading.Thread):
  def __init__(self, command, on_done, working_dir="", fallback_encoding="", env={}):
    threading.Thread.__init__(self)
    self.command = command
    self.on_done = on_done
    self.working_dir = working_dir
    self.fallback_encoding = fallback_encoding
    self.env = env

  def run(self):
    try:
      # Per http://bugs.python.org/issue8557 shell=True is required to
      # get $PATH on Windows. Yay portable code.
      shell = os.name == 'nt'
      if self.working_dir != "":
        os.chdir(self.working_dir)
      proc = subprocess.Popen(self.command,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        shell=shell, universal_newlines=True, env=self.env)
      main_thread(self.on_done, proc.communicate()[0])
    except subprocess.CalledProcessError as e:
      main_thread(self.on_done, e.returncode)
    except OSError as e:
      if e.errno == 2:
        main_thread(sublime.error_message, "Node binary could not be found in PATH\n\nConsider using the node_command setting for the Node plugin\n\nPATH is: %s" % os.environ['PATH'])
      else:
        raise e
