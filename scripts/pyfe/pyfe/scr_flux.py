#! /usr/bin/env python3

# scr_flux.py

# calls scr_run specifying to use launcher 'flux'

import os, sys

if 'pyfe' not in sys.path:
  sys.path.insert(0, '/'.join(os.path.realpath(__file__).split('/')[:-2]))

from pyfe.scr_run import scr_run, parseargs, print_usage

if __name__ == '__main__':
  # just printing help, print the help and exit
  if len(sys.argv) < 3 or '-h' in sys.argv[1:] or '--help' in sys.argv[1:]:
    print_usage('flux')
  elif not any(
      arg.startswith('-rc') or arg.startswith('--run-cmd')
      or arg.startswith('-rs') or arg.startswith('--restart-cmd')
      for arg in sys.argv):
    # then we were called with: scr_flux [launcher args]
    scr_run(launcher='flux', launcher_args=sys.argv[1:])
  else:
    launcher, launcher_args, run_cmd, restart_cmd, restart_args = parseargs(
        sys.argv[1:], launcher='flux')
    scr_run(launcher='flux',
            launcher_args=launcher_args,
            run_cmd=run_cmd,
            restart_cmd=restart_cmd,
            restart_args=restart_args)