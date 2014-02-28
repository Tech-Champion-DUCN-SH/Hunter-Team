'''
Created on 2014-2-27

@author: ezonghu
'''
import re
import subprocess

password = "abc123\n"
mysql_user = "root"
mysql_password = "3r1cs50n"

def parse_mysql_nodes(nodes):
    node_names = []
    bound_flag = 0
    for line in nodes.split('\n'):
        m = line.split()
        if len(m) == 1:
            if m[0] == 'node':
                bound_flag += 1
                continue
            if bound_flag == 1:
                node_names.append(m[0])
                
    return list(set(node_names))
def parse_mysql_node_infos(nodes):
    node_infos = dict()
    bound_flag = 0
    for line in nodes.split('\n'):
        m = line.split()
        if len(m) == 4:
            if m[0] == "uuid" and m[1] == "node":
                bound_flag += 1
                continue
                
            if bound_flag == 1:
                node_infos[m[0]] = {"node":m[1], "name":m[2], "status":m[3]}

                
    return node_infos

def parse_mysql_port_infos(ports):
    port_infos = dict()

    bound_flag = 0
    for line in ports.split('\n'):
        m = line.split()
        if len(m) == 3:
            if m[0] == "id" and m[1] == "device_id":
                bound_flag += 1
                continue
                
            if bound_flag == 1:
                port_infos[m[0]]=  {"device_id":m[1], "device_owner":m[2]}

                
    return port_infos    
def parse_nova_nodes(nova_list):
    nova_computes=dict()

    bound = re.compile("^\+-+\+-+\+-+\+-+\+$")
    seperate = re.compile("^\|(.*)\|(.*)\|(.*)\|(.*)\|$")
    bound_flag = 0
    for line in nova_list.split('\n'):
        m = bound.match(line)
        if m is not None:
            bound_flag += 1

        if bound_flag == 2:
            s = seperate.match(line)
            if s is not None:
                nova_computes[s.group(1).strip()]={"name":s.group(2).strip(), 
                                                   "status":s.group(3).strip(), 
                                                   "networks":s.group(4).strip()} 
    return nova_computes
                    
def parse_quantum_ports_id(ports_string):
    ports=[]
    
    bound = re.compile("^\+-+\+-+\+-+\+-+\+$")
    seperate = re.compile("^\|(.*)\|(.*)\|(.*)\|(.*)\|$")
    bound_flag = 0
    for line in ports_string.split('\n'):
        m = bound.match(line)
        if m is not None:
            bound_flag += 1

        if bound_flag == 2:
            s = seperate.match(line)
            if s is not None:
                ports.append(s.group(1).strip())
    return ports



def parse_quantum_port(port_res):
    port = {}
    bound = re.compile("^\+-+\+-+\+$")
    seperate = re.compile("^\|(.*)\|(.*)\|$")
    bound_flag = 0
    for line in port_res.split('\n'):
        m = bound.match(line)
        if m is not None:
            bound_flag += 1

        if bound_flag == 2:
            s = seperate.match(line)
            if s is not None:
                port[s.group(1).strip().lower()]=s.group(2).strip()
    return port



def parse_brctl_show(br_res):
    bridges = {}
    curr_br_name = ""
    for line in br_res.split("\n")[1:]:
        br_infos = line.split()
        if len(br_infos) == 4:
            curr_br_name=br_infos[0]
            bridges[curr_br_name]= [br_infos[3]]
            
        elif len(br_infos)==1:
            bridges[curr_br_name].append(br_infos[0])
            
    return bridges


def parse_ifconfig(ifcfg_res):
    intfs = []
    for line in ifcfg_res.split("\n")[1:]:
        if len(line.split()) > 1:
            intfs.append(line.split()[0])
            
    return intfs


def parse_ovs_vsctl_show(ovs_res):
    Ovs_Br = {}
    curr_br = ""
    for line in ovs_res.split("\n"):
        infos = line.split()
        if infos == []:
            continue
        
        if "Bridge" == infos[0]:
            curr_br = infos[1]
            Ovs_Br[curr_br] = []
            continue
            
        if "Port" == infos[0]:
            Ovs_Br[curr_br].append(infos[1].replace('"', ''))
            continue
        
            
            
    return Ovs_Br


def run_cmd(cmd, password=None):
    print cmd
    proc = subprocess.Popen([cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return proc.communicate(password)

def get_openstack_l2_by_mysql(HostName, pre_cmd=""):
    global mysql_user, mysql_password
    

    cmd = 'mysql -u %s --password=%s -D nova -e "select uuid, node, display_name,  vm_state from instances where deleted=0 and node=\'%s\';"' % (mysql_user, mysql_password,HostName)
    res, _err = run_cmd(cmd)
    node_infos = parse_mysql_node_infos(res)
    
    cmd = 'mysql -u %s --password=%s -D quantum -e "select id, device_id, device_owner from ports;"' % (mysql_user, mysql_password)
    res, _err = run_cmd(cmd)
    port_infos = parse_mysql_port_infos(res)
    
    vm_ports_tab={}
    for vm_id in node_infos:
        if vm_id not in vm_ports_tab:
            vm_ports_tab[vm_id]=[]
            
        for port, info in port_infos.iteritems():
            if info['device_id'] == vm_id:
                vm_ports_tab[vm_id].append(port)
        
    #get interface list
    cmd = pre_cmd + " ifconfig -s"
    res, _err = run_cmd(cmd)
    intf_list = parse_ifconfig(res)
    
    vm_tap_tab = {}
    for vm, ports in vm_ports_tab.iteritems():
        taps = []
        for port in ports:
            tap = "tap%s" % port[:11]
            if tap in intf_list:
                taps.append(tap)
        
        vm_tap_tab[vm+"("+node_infos[vm]["name"]+")"]=taps
    #get ovs br info
    cmd =  pre_cmd + ' sudo -S ovs-vsctl show'
    print cmd        
    proc=subprocess.Popen([cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    global password
    res, _err = proc.communicate(password)
    ovs_br_ports_tab =  parse_ovs_vsctl_show(res)
    
    #get linux br info
    cmd = pre_cmd + " brctl show"
    res, _err = run_cmd(cmd)
    lbr_br_ports_tab = parse_brctl_show(res)
    
    return HostName, vm_tap_tab, ovs_br_ports_tab, lbr_br_ports_tab, intf_list
def get_openstack_l2():
    #get nova compute list
    cmd = "nova list"
    res, _err = run_cmd(cmd)
    nova_nodes = parse_nova_nodes(res)

    new_nova_nodes={}
    for k, v in nova_nodes.iteritems():
        if v['status'] == 'ACTIVE':
            new_nova_nodes[k]=v
            
    #get quantum port list
    cmd = "quantum port-list"
    res, _err = run_cmd(cmd)
    ports_id = parse_quantum_ports_id(res)

    vm_ports_tab = {}
    #get detail port info
    cmd = "quantum port-show %s"
    for port_id in ports_id:
        res, _err = run_cmd(cmd % port_id)
        port_info = parse_quantum_port(res)

        dev_id = port_info['device_id']        
        if dev_id in new_nova_nodes:
            if not vm_ports_tab.has_key(dev_id):
                vm_ports_tab[dev_id]=[port_id]
            else:
                vm_ports_tab[dev_id].append(port_id)
                
    #get interface list
    cmd = "ifconfig -s"
    res, _err = run_cmd(cmd)
    intf_list = parse_ifconfig(res)

    
    vm_tap_tab = {}
    for vm, ports in vm_ports_tab.iteritems():
        taps = []
        for port in ports:
            tap = "tap%s" % port[:11]
            if tap in intf_list:
                taps.append(tap)
        vm_tap_tab[vm]=taps
    
    #get ovs br info
    cmd = 'sudo -S ovs-vsctl show'
    print cmd        
    proc=subprocess.Popen(['sudo -S ovs-vsctl show'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    global password
    res, _err = proc.communicate(password)
    ovs_br_ports_tab =  parse_ovs_vsctl_show(res)
    
    #get linux br info
    cmd = "brctl show"
    res, _err = run_cmd(cmd)
    lbr_br_ports_tab = parse_brctl_show(res)
    
    return new_nova_nodes, vm_tap_tab, ovs_br_ports_tab, lbr_br_ports_tab, intf_list

def get_node_relationships(HostName, vm_tap_tab, ovs_br_ports_tab, lbr_br_ports_tab, intf_list): 
    Nodes = {}
    Links = []
    for vm, taps in vm_tap_tab.iteritems():
        Nodes[vm]="vm"
        for tap in taps:
            Links.append((vm, tap))
    
    def get_br_port_links(br_port_tab):
        for br, ports in br_port_tab.iteritems():
            for p in ports:
                if p[:3] in ("tap", "qvo","phy"):
                    Links.append((p,br))
                elif p[:3] in ("qvb", "int", "eth") :
                    Links.append((br,p))
                
    get_br_port_links(ovs_br_ports_tab)   
    get_br_port_links(lbr_br_ports_tab)               
    
    
    def get_veth_links(interfaces):
        for intf in interfaces:
            if intf[:3] in ('qvb','int'):
                qvo = "qvo"+intf[3:]
                phy = "phy"+intf[3:]
                if  qvo in interfaces:
                    Links.append((intf, qvo))
                elif phy in interfaces:
                    Links.append((intf, phy))
                    
    get_veth_links(intf_list)
    
    def get_intf_type(interfaces):
        for intf in interfaces:
            if intf[:2] == "br":
                Nodes[intf]="ovs"
            elif intf[:3] in ("qvb", "qvo", "int", "phy"):
                Nodes[intf]="veth"
            elif intf[:3] == 'qbr':
                Nodes[intf]="br"
            elif intf[:3] == "tap":
                Nodes[intf] = "tap"
            elif intf[:3] == "eth":
                Nodes[intf] = "eth"
                
    get_intf_type(intf_list)
    return HostName, Nodes, list(set(Links))
            
import socket
def get_local_node_relationships():
    
    return get_node_relationships(*get_openstack_l2_by_mysql(socket.gethostname()))


def get_remote_node_relationships():
    cmd = 'mysql -u %s --password=%s -D nova -e "select node from instances where deleted=0 and node!=\'%s\';"' % (mysql_user, mysql_password, socket.gethostname())
    res, _err = run_cmd(cmd)
    remote_nodes = parse_mysql_nodes(res)
    return [get_node_relationships(*get_openstack_l2_by_mysql(rn, 'ssh %s ' % rn)) for rn in remote_nodes ]

def get_all_node_relationships():
    res = get_remote_node_relationships()
    res.append(get_local_node_relationships())
    return res

#print get_all_node_relationships()
