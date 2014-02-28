#!/usr/bin/python

import gv

# define functions
aColor = {"vm":"lightpink", "tap":"lightblue", "veth":"palegreen", 
          "br":"yellow", "ovs":"turquoise", "eth":"moccasin"}

# function: draw_note/1
def draw_note(g):
    global aColor
    gv.graph(g, "cluster_0")
    g1 = gv.findsubg(g, "cluster_0")
    gv.setv(g1, "color", "white")

    aNodes = []
    length = 0
    for key in aColor:
        c = aColor[key]
        n = gv.node(g1, key)
        gv.setv(n, "shape", "box")
        gv.setv(n, "style", "filled")
        gv.setv(n, "color", c)
        gv.setv(n, "label", key)
        aNodes.append(key)
        length =  length +1

    for i in range(0, length-1):
        e = gv.edge(g1, aNodes[i], aNodes[i+1])
        gv.setv(e, "style", "invis")

# function: draw_node/3
def draw_node(g, key, aName, aType):
    global aColor

    n = gv.node(g, aName)
    # set node show name
    gv.setv(n, "label", key)

    gv.setv(n, "style", "filled")
    gv.setv(n, "shape", "box")

   # if aType == "ovs":
   #    gv.setv(n, "fixedsize", "true")
   #    gv.setv(n, "width", "3")
   # elif aType == "br":
   #    gv.setv(n, "fixedsize", "true")
   #    gv.setv(n, "width", "3")
   # elif aType == "eth":
   #     e = gv.edge(n, "swith")
   #     gv.setv(e, "dir", "none")

    #if aType == "eth":
    #   e = gv.edge(n, "swith")
    #   gv.setv(e, "dir", "none")
    #   gv.setv(e, "style", "dashed")

    if key == "br-int":
       gv.setv(n, "width", "10")

    # set color
    if aType in aColor:
       c = aColor[aType]
    else:
       c = "lightgrey"
    gv.setv(n, "color", c)

    return n

# function: draw_edge/4
def draw_edge(g, x1, x2, aDict):
    if x1 in aDict and x2 in aDict:
        n2 = aDict[x2]
        n1 = aDict[x1]
        e = gv.edge(g, n1, n2)
        gv.setv(e, "dir", "none")
        return e

# function: draw_host/4
def draw_host(g, aHost, aNodes, aLinks):
    clusterName = 'cluster_' + aHost

    gv.graph(g, clusterName)
    g1 = gv.findsubg(g, clusterName)
    gv.setv(g1, "label", aHost)
   # gv.setv(g1, "clusterMode", "local")

    #rank = "same"
   # gv.setv(g1, "rank", rank)

    # draw nodes
    aNodes1 = {}
    for key in aNodes:
        aName = aHost + key
        aType = aNodes[key]
        n = draw_node(g1, key, aName, aType)
        aNodes1[aName] = aName

    # draw edges
    #aLinks1 = {}
    for x in aLinks:
        (x1, x2) = x
        n1 = aHost + x1
        n2 = aHost + x2
        e = draw_edge(g1, n1, n2, aNodes1)
        #gv.setv(e, "weight", "100")
        #aLinks1[x] = e

# function: draw_graph/2
def draw_graph(aData):
    g = gv.digraph("G")

    #gv.setv(g, "label", "TEST")
    #gv.setv(g, "rankdir", "LR")

    # Set node style
    #n = gv.protonode(g0)
    #gv.setv(n, "shape", "ellipse")

    # draw notes
    draw_note(g)

    # draw one common node: swith
    #draw_node(g, "swith", "swith", "swith")

    # draw subgraph
    for key in aData:
        (aHost, aNodes, aLinks) = key
        draw_host(g, aHost, aNodes, aLinks)

    # save file
    gv.write(g, "draw.dot")

    #generate graphic
    gv.layout(g, "dot")
    gv.render(g, "png", "l2_topology.png")
    gv.rm(g)

import vm 
draw_graph(vm.get_all_node_relationships())
