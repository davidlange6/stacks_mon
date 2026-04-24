#!/usr/bin/env python3

import os
import time
import sys
#import popen2
import subprocess
import datetime

from threading import Thread
import psutil

class testit(Thread):
    def __init__(self,command,logfile):
        Thread.__init__(self)
        self.command=command
        self.status=-1
        self.report=''
        self.pid=-1
        self.subproc=None
        self.f=None
        self.logfile=logfile
    def run(self):

        f=open(self.logfile,'w')
    
        p3=subprocess.Popen(self.command,shell=True,stderr=subprocess.STDOUT,stdout=f, bufsize=1)
        self.pid=p3.pid
        self.subproc=p3
        self.f=f
        exitcode=os.waitpid(p3.pid,0)

def self_callers(info_ptr,fo,selfs={},self_stacks={},parents=[]):
    ndaug_tot=0
    for key,val in info_ptr.items():
        parent2=parents.copy()
        parent2.append(key)
        ndaug=self_callers(info_ptr[key][1],fo,selfs,self_stacks,parent2)
        ndaug_tot+=info_ptr[key][0]
        self_val= info_ptr[key][0]-ndaug
        if self_val>0:
            selfs[key]=selfs.get(key,0)+self_val
            if key not in self_stacks:
                self_stacks[key]={}
            self_stacks[key][';'.join(parents)]=self_stacks[key].get(';'.join(parents),0)+self_val

    if len(parents)==0:
        for key, val in sorted(selfs.items(), key=lambda item: item[1], reverse=True):
            fo.write(f"{val:5d}: {key}\n")
            for key2, val2 in sorted(self_stacks[key].items(), key=lambda item: item[1], reverse=True):
                for i,p in enumerate(key2.split(';')[::-1]):
                    if i==0:
                        fo.write(f"  {val2:5d}  {p}\n")
                    else:
                        fo.write(f"         {p}\n")
                    if i==5: break

                
    return ndaug_tot


def get_children(parent_pid):
    parent = psutil.Process(parent_pid)
    children = parent.children(recursive=True)
    retval=[parent_pid]
    for p in children:
        retval.append(p.pid)
    return retval
        
def run_command(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return proc.returncode, out.decode(), err.decode()

def print_info(info_ptr,fh,prev=''):
    sum=0
    for key,val in info_ptr.items():
        prev_new=prev+key      
        ndaug=print_info(info_ptr[key][1],fh,prev_new+';')
        if ndaug != info_ptr[key][0]:
            fh.write(prev_new+' '+str(info_ptr[key][0]-ndaug)+'\n')
        sum=sum+info_ptr[key][0]
    return sum

def add_infos(infos, pstack_output):
    current_stack=[]
    for l in pstack_output.split('\n'):
        if '#' not in l: continue
        l=l.replace('(anonymous namespace)','')            
        entry=''
        sp=l.split()
        for s in sp[1:]:
            if s=="from" or s=="at":
                break
            if s.startswith('0x'):
                continue
            if s=="in":
                continue
            if '(' in s:
                entry=entry+' '+s.split('(')[0]
                break
            else:
                entry=entry+' '+s
        current_stack.append(entry)

    info_ptr=infos
    for i,s in enumerate(current_stack[::-1]):
        key=s.strip()
        if key not in info_ptr:
            info_ptr[key]=[0,{}]
        info_ptr[key][0]+=1
        info_ptr=info_ptr[key][1]



def main(argv) :

    firstA=0
    iter='0'
    if argv[0]=="-n":
        iter=argv[1]
        firstA=2
    logfile='checkMem_'+iter+'.log'
    print(logfile)    

    rvComm=' '.join(argv[firstA:])

    clist = []

    current = testit(rvComm,logfile)
    current.start()

    interval=0.05
    time.sleep(interval)

    infos={}
    fouts={}
    counter=0

    fout_mem=open("memory_"+iter+".log",'w')
    #fouts_stacks={}
    fouts_selfs={}
    
    import datetime
    
    while(current.is_alive()):
        dtnow=str(datetime.datetime.now())
        if counter%10 == 0:
            cpu_processes=get_children(current.pid)
        counter=counter+1

            
        for process in cpu_processes:
            if process not in fouts:
                fouts[process]=open('callstackinfo_'+iter+"_"+str(process)+'.out','w')
                #fouts_stacks[process]=open('stacks_'+iter+"_"+str(process)+'.out','w')
                fouts_selfs[process]=open('selftimes_'+iter+"_"+str(process)+'.out','w')
                infos[process]={}
            
            comm='/dlange/260209/uniqstack/uniqstack '+str(process)
            o1,o2,o3=run_command(comm)          

            add_infos(infos[process],o2)

#            fouts_stacks[process].write("New Stack -------------------------------------------------\n")
#            fouts_stacks[process].write(o2)
#            fouts_stacks[process].write('\n')
            
            if os.path.exists('/proc/'+str(process)+'/stat'):
                cmd='grep VmRSS /proc/'+str(process)+'/status'
                cmd2='grep VmSize /proc/'+str(process)+'/status'
                mem=os.popen(cmd).readline()
                mem=mem.strip().split()
                if len(mem)>1:
                    mem=mem[1]
                else:
                    continue
                vmem=os.popen(cmd2).readline()
                vmem=vmem.strip().split()
                if len(vmem)>1:
                    vmem=vmem[1]
                else:
                    continue
#                print mems[-1]/(1000.*1024.)
                fout_mem.write(str(process)+' '+dtnow+' '+mem+' '+vmem+' ')

        #find the current event
        cmd="tail -1000 "+logfile+" | grep 'Begin event action' | tail -1 | cut -d' ' -f7"
        last_event=os.popen(cmd).readline().strip()
        if last_event is None or len(last_event)==0: 
            last_event="-1"

        fout_mem.write(last_event+'\n')

            
        time.sleep(interval)
        
#        fout.write(o2) # will write everything

    for key in infos:
        print_info(infos[key],fouts[key]) # writes the summary for flamegraph
        fouts[key].close()

    for key in infos:
        self_callers(infos[key],fouts_selfs[key]) # writes the summary for flamegraph
        fouts_selfs[key].close()

#        fouts_stacks[key].close()
        
    fout_mem.close()
    
if __name__ == '__main__' :
    main(sys.argv[1:])


          
