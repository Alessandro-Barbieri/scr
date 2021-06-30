#! /usr/bin/env python3

# scr_list_down_nodes.py

import argparse
from time import time
from pyfe import scr_const, scr_hostlist
from pyfe.scr_param import SCR_Param
from pyfe.scr_list_dir import scr_list_dir
from pyfe.scr_common import runproc, pipeproc, scr_prefix
from pyfe import scr_common
from pyfe.scr_env import SCR_Env
from pyfe.resmgr.scr_resourcemgr import SCR_Resourcemgr

'''
 methods used by resource managers to test nodes
 these methods return a hash to track nodes which failed and their reason
 these methods take a list of nodes which would otherwise be used
 failing nodes are deleted from the list argument in each of these methods
'''
class SCR_List_Down_Nodes:
  ping = 'ping'
  bindir = scr_const.X_BINDIR
  pdsh   = scr_const.PDSH_EXE

  # mark the set of nodes the resource manager thinks is down
  @staticmethod
  def list_resmgr_down_nodes(nodes=[],resmgr_nodes=None):
    unavailable = {}
    if resmgr_nodes is not None:
      resmgr_nodes = scr_hostlist.expand(resmgr_nodes)
      for node in resmgr_nodes:
        if node in nodes:
          del nodes[node]
        unavailable[node] = 'Reported down by resource manager'
    return unavailable

  # mark any nodes that fail to respond to (up to 2) ping(s)
  @staticmethod
  def list_nodes_failed_ping(nodes=[]):
    unavailable = {}
    # `$ping -c 1 -w 1 $node 2>&1 || $ping -c 1 -w 1 $node 2>&1`;
    argv=[SCR_List_Down_Nodes.ping,'-c','1','-w','1','']
    for node in nodes:
      argv[5] = node
      returncode = runproc(argv=argv)[1]
      if returncode!=0:
        returncode = runproc(argv=argv)[1]
        if returncode!=0:
          unavailable[node] = 'Failed to ping'
    for node in unavailable:
      if node in nodes:
        del nodes[node]
    return unavailable

  # mark any nodes to explicitly exclude via SCR_EXCLUDE_NODES
  @staticmethod
  def list_param_excluded_nodes(nodes=[],param=None):
    unavailable = {}
    if param is not None:
      exclude = param.get('SCR_EXCLUDE_NODES')
      if exclude is not None:
        exclude_nodes = scr_hostlist.expand($exclude)
        for node in exclude_nodes:
          if node in nodes:
            del nodes[node]
            unavailable[node] = 'User excluded via SCR_EXCLUDE_NODES'
    return unavailable

  # mark any nodes specified on the command line
  @staticmethod
  def remove_argument_excluded_nodes(nodes=[],nodeset_down=''):
    #unavailable = {}
    exclude_nodes = scr_hostlist.expand(nodeset_down)
    for node in exclude_nodes:
      if node in nodes:
        del nodes[node]
        #unavailable[node] = 'Specified on command line'
    #return unavailable

  # mark any nodes that don't respond to pdsh echo up
  @staticmethod
  def list_pdsh_fail_echo(nodes=[]):
    unavailable = {}
    pdsh_assumed_down = nodes.copy()
    if len(nodes)>0:
      # only run this against set of nodes known to be responding
      upnodes = scr_hostlist.compress(nodes)

      # run an "echo UP" on each node to check whether it works
      argv = []
      argv.append([SCR_List_Down_Nodes.pdsh,'-f','256','-w',upnodes,'\"echo UP\"'])
      argv.append([SCR_List_Down_Nodes.dshbak,'-c'])
      output = pipeproc(argvs=argv,getstdout=True)[0]
      position=0
      for result in output.split('\n'):
        if len(result)==0:
          continue
        if position==0:
          if result.startswith('---'):
            position=1
        elif position==1:
          nodeset = result
          position = 2
        elif position==2:
          line=result
          position=3
        elif position==3:
          position=0
          if 'UP' in result:
            exclude_nodes = scr_hostlist.expand(nodeset)
            for excludenode in exclude_nodes:
              # this node responded, so remove it from the down list
              if excludenode in pdsh_assumed_down:
                del pdsh_assumed_down[excludenode]

    # if we still have any nodes assumed down, update our available/unavailable lists
    for node in pdsh_assumed_down:
      del nodes[node]
      unavailable[node] = 'Failed to pdsh echo UP'

    return unavailable

  #### Each resource manager other than LSF had this section
  #### Their difference was in the scr_check_node_argv
  #### Only the SLURM had the line size = param.abtoull(size)
  #### The abtoull will just return the int of the string if it isn't in the ab format
  @staticmethod
  def check_dir_capacity(nodes=[],free=False,scr_env=None,scr_check_node_argv=[]):
    if scr_check_node_argv == [] or nodes==[]:
      return {}
    unavailable = {}
    if scr_env is None:
      scr_env = SCR_Env()
    if scr_env.param is None:
      scr_env.param = SCR_Param()
    param = scr_env.param
    # specify whether to check total or free capacity in directories
    #if free: free_flag = '--free'

    # check that control and cache directories on each node work and are of proper size
    # get the control directory the job will use
    cntldir_vals = []
    cntldir_string = scr_list_dir(base=True,runcmd='control',scr_env=scr_env)
    # cntldir_string = `$bindir/scr_list_dir --base control`;
    if cntldir_string != 1:
      dirs = cntldir_string.split(' ')
      cntldirs = param.get_hash('CNTLDIR')
      for base in dirs:
        if len(base)<1:
          continue
        val = base
        if cntldirs is not None and base in cntldirs and 'BYTES' in cntldirs[base]:
          if len(cntldirs[base]['BYTES'].keys())>0:
            size = list(cntldirs[base]['BYTES'].keys())[0] #(keys %{$$cntldirs{$base}{"BYTES"}})[0];
            #if (defined $size) {
            size = param.abtoull(size)
            #  $size = $param->abtoull($size);
            val += ':'+str(size)
            #  $val = "$base:$size";
        cntldir_vals.append(val)

    cntldir_flag = []
    if len(cntldir_vals)>0:
      cntldir_flag = ['--cntl ', ','.join(cntldir_vals)]

    # get the cache directory the job will use
    cachedir_vals = []
    cachedir_string = scr_list_dir(base=True,runcmd='cache',scr_env=scr_env)
    #`$bindir/scr_list_dir --base cache`;
    if type(cachedir_string) is str and len(cachedir_string) != 0:
      dirs = cachedir_string.split(' ')
      cachedirs = param.get_hash('CACHEDIR')
      for base in dirs:
        if len(base)<1:
          continue
        val = base
        if cachedirs is not None and base in cachedirs and 'BYTES' in cachedirs[base]:
          if len(cachedirs[base]['BYTES'].keys())>0:
            size = list(cachedirs[base]['BYTES'].keys())[0]
            #my $size = (keys %{$$cachedirs{$base}{"BYTES"}})[0];
            #if (defined $size) {
            size = param.abtoull(size)
            #  $size = $param->abtoull($size);
            val += ':'+str(size)
            #  $val = "$base:$size";
        cachedir_vals.append(val)

    cachedir_flag = []
    if len(cachedir_vals) > 0:
      cachedir_flag = ['--cache ', ','.join(cachedir_vals)]

    # only run this against set of nodes known to be responding
    upnodes = scr_hostlist.compress(nodes)

    # run scr_check_node on each node specifying control and cache directories to check
    ################### This is calling a script, scr_check_node, from pdsh.
    ###################### think this is going to need the python pdsh equivalent
    #cray
    # [ $pdsh -Rexec -f 256 -w $upnodes aprun -n 1 -L %h ]
    #slurm [ $pdsh -Rexec -f 256 -w $upnodes srun -n 1 -N 1 -w %h ]
    #### the pmix should have from the scr_checknode to the end as a single argument (... ?)
    #pmix [ $pdsh -f 256 -w $upnodes ]
    # we need to replace the $vars with their actual values and complete the argv
    # full argv:
    # argv = []
    # argv.append( [ $pdsh $upnodes $scr_check_node $free_flag $cntldir_flag $cachedir_flag ] )
    # argv.append( [ $dshbak -c ] )
    # output = pipeproc(argv)
    argv = [ [] ]
    for arg in scr_check_node_argv:
      if arg=='$pdsh':
        argv[0].append(SCR_List_Down_Nodes.pdsh)
      elif arg=='$upnodes':
        argv[0].append(upnodes)
      else:
        argv[0].append(arg)
    argv[0].extend(['python3', SCR_List_Down_Nodes.bindir+'/scr_check_node.py'])
    if free:
      argv[0].append('--free')
    argv[0].extend(cntldir_flag)
    argv[0].extend(cachedir_flag)
    argv.append([SCR_List_Down_Nodes.dshbak,'-c'])
    output = pipeproc(argvs=argv,getstdout=True)[0]
    action=0 # tracking action to use range iterator and follow original line <- shift flow
    nodeset = ''
    line = ''
    for result in output.split('\n'):
      if len(result)<1:
        pass
      elif action==0:
        if result.startswith('---'):
          action=1
      elif action==1:
        nodeset = result
        action=2
      elif action==2:
        line = result
        action=3
      elif action==3:
        action=0
        if 'PASS' not in result:
          exclude_nodes = scr_hostlist.expand(nodeset);
          for node in exclude_nodes:
            if node in nodes:
              del nodes[node]
              unavailable[node] = result
    return unavailable


# The main scr_list_down_nodes method.
# this method takes an scr_env, the contained resource manager will determine which methods above to use
def scr_list_down_nodes(reason=False, free=False, nodeset_down='', log_nodes=False, runtime_secs=None, nodeset=None, scr_env=None):
  bindir = scr_const.X_BINDIR
  pdsh   = scr_const.PDSH_EXE

  start_time = str(int(time())) # epoch seconds as int to remove decimal, as string to be a parameter

  # check that we have a nodeset before going any further
  if scr_env is None:
    scr_env = SCR_Env()
  if scr_env.resmgr is None:
    scr_env.resmgr = SCR_Resourcemgr()
  resourcemgr = scr_env.resmgr
  if nodeset is None or len(nodeset)==0:
    nodeset = resourcemgr.conf['nodes']
    if nodeset is None or len(nodeset)==0:
      print('scr_list_down_nodes: ERROR: Nodeset must be specified or script must be run from within a job allocation.')
      return 1
  if type(nodeset) is not str:
    nodeset = ','.join(nodeset)

  if scr_env.param is None:
    scr_env.param = SCR_Param()
  param = scr_env.param

  # get list of nodes from nodeset
  nodes = scr_hostlist.expand(nodeset)

  # get prefix directory
  prefix = scr_env.conf['prefix']

  # get jobid
  jobid = resourcemgr.conf['jobid']
  #if jobid == 'defjobid': # job id could not be determined
  #  print('Could not determine the job id') # the only place this is used here is in the logging below

  ### In each of the scr_list_down_nodes.in
  ### these nodes are marked as unavailable, and also removed from the list to log
  ### There is no use to keep track of them in the unavailable dictionary
  #unavailable = list_argument_excluded_nodes(nodes=nodes,nodeset_down=nodeset_down)
  remove_argument_excluded_nodes(nodes=nodes,nodeset_down=nodeset_down)

  # get a hash of all unavailable (down or excluded) nodes and reason
  # keys are nodes and the values are the reasons
  unavailable = resourcemgr.list_down_nodes_with_reason(nodes=nodes, scr_env=scr_env, nodeset_down=nodeset_down, free=free)

  # TODO: read exclude list from a file, as well?

  # print any failed nodes to stdout and exit with non-zero
  if len(unavailable)>0:
    # log each newly failed node, along with the reason
    if log_nodes:
      # scr_common.log calls the external program: scr_log_event
      # the method will also accept a dictionary (instead of a string)
      # for the event_note argument, this moves the loop closer to the runproc call
      scr_common.log(bindir=bindir, prefix=prefix, jobid=jobid, event_type='NODE_FAIL', event_note=unavailable, event_start=start_time, event_secs=runtime_secs)
    # now output info to the user
    ret=''
    if reason:
      # list each node and the reason each is down
      for node in unavailable:
        ret += node+': '+unavailable[node]+'\n'
      ret = ret[:-1] ### take off the final trailing newline (?)
    else:
      # simply print the list of down node in range syntax
      ret = scr_hostlist.compress(list(unavailable))
    return ret
  # otherwise, don't print anything and exit with 0
  return 0

if __name__=='__main__':
  parser = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS, prog='scr_list_down_nodes')
  parser.add_argument('--help', action='store_true', help='Show this help message and exit.')
  parser.add_argument('-r','--reason', action='store_true', default=False, help='Print reason node is down.')
  parser.add_argument('-f','--free', action='store_true', default=False, help='Test required drive space based on free amount, rather than capacity.')
  parser.add_argument('-d','--down', metavar='<nodeset>', type=str, default=None, help='Force nodes to be down without testing.')
  parser.add_argument('-l','--log', action='store_true', default=False, help='Add entry to SCR log for each down node.')
  parser.add_argument('-s','--secs', metavar='N', type=str, default=None, help='Specify the job\'s runtime seconds for SCR log.')
  parser.add_argument('[nodeset]', nargs='*', default=None, help='Specify the complete set of nodes to check within.')
  args = vars(parser.parse_args())
  if 'help' in args:
    parser.print_help()
  else:
    ret = scr_list_down_nodes(reason=args['reason'], free=args['free'], nodeset_down=args['down'], log_nodes=args['log'], runtime_secs=args['secs'], nodeset=args['[nodeset]'])
    print(str(ret),end='')

