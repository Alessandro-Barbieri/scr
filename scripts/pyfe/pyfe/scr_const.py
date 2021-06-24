#! /usr/bin/env python3

# vars can be set in this file to serve as compile time constants
# other scripts can just reference scr_const.SCR_CNTL_BASE (etc) without modification

SCR_CNTL_BASE = '@SCR_CNTL_BASE@'
SCR_CACHE_BASE = '@SCR_CACHE_BASE@'
SCR_CACHE_SIZE = '1' # '@SCR_CACHE_SIZE@'
SCR_CONFIG_FILE = '@SCR_CONFIG_FILE@'
X_BINDIR = '@X_BINDIR@'
X_LIBDIR = '@X_LIBDIR@'
PDSH_EXE = '@PDSH_EXE@'
DSHBAK_EXE = '@DSHBAK_EXE@'
SCR_RESOURCE_MANAGER = '@SCR_RESOURCE_MANAGER@'
SCR_LAUNCHER = '@LAUNCHER@'

if __name__=='__main__':
  print('SCR_CNTL_BASE = \"'+SCR_CNTL_BASE+'\"')
  print('SCR_CACHE_BASE = \"'+SCR_CACHE_BASE+'\"')
  print('SCR_CACHE_SIZE = \"'+SCR_CACHE_SIZE+'\"')
  print('SCR_CONFIG_FILE = \"'+SCR_CONFIG_FILE+'\"')
  print('X_BINDIR = \"'+X_BINDIR+'\"')
  print('X_LIBDIR = \"'+X_LIBDIR+'\"')
  print('PDSH_EXE = \"'+PDSH_EXE+'\"')
  print('DSHBAK_EXE = \"'+DSHBAK_EXE+'\"')
  print('SCR_RESOURCE_MANAGER = \"'+SCR_RESOURCE_MANAGER+'\"')
  print('SCR_LAUNCHER = \"'+SCR_LAUNCHER+'\"')
