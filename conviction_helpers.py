import networkx as nx
from scipy.stats import expon, gamma
import numpy as np
from bonding_curve_eq import invariant,spot_price
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx

#helper functions
def get_nodes_by_type(g, node_type_selection):
    return [node for node in g.nodes if g.nodes[node]['type']== node_type_selection ]

def get_edges_by_type(g, edge_type_selection):
    return [edge for edge in g.edges if g.edges[edge]['type']== edge_type_selection ]

default_theta = .25
default_initial_price = .1
default_kappa = 2

def conviction_order(network, proposals):

    ordered = sorted(proposals, key=lambda j:network.nodes[j]['conviction'] , reverse=True)

    return ordered


def total_funds_given_total_supply(initial_supply, theta = default_theta, initial_price = default_initial_price):

    total_raise = initial_price*initial_supply

    total_funds = theta*total_raise

    return total_funds

def initialize_bonding_curve(initial_supply, initial_price = default_initial_price, kappa =default_kappa, theta = default_theta):

    S = initial_supply
    total_raise = initial_price*S

    R =  (1-theta)*total_raise

    V0 = invariant(R,S,kappa)

    initial_reserve = R

    hatch_price = spot_price(R, V0, kappa)

    return initial_reserve, V0, hatch_price

#maximum share of funds a proposal can take
default_beta = .2 #later we should set this to be param so we can sweep it
# tuning param for the trigger function
default_rho = .001

def trigger_threshold(requested, funds, supply, beta = default_beta, rho = default_rho):

    share = requested/funds
    if share < beta:
        return rho*supply/(beta-share)**2
    else:
        return np.inf

def initialize_network(n,m, expected_supply = 10**6 ):
    network = nx.DiGraph()
    for i in range(n):
        network.add_node(i)
        network.nodes[i]['type']="participant"

        h_rv = expon.rvs(loc=0.0, scale= expected_supply/n)
        network.nodes[i]['holdings'] = h_rv

        s_rv = np.random.rand()
        network.nodes[i]['sentiment'] = s_rv

    participants = get_nodes_by_type(network, 'participant')
    initial_supply = np.sum([ network.nodes[i]['holdings'] for i in participants])

    #generate initial proposals
    for ind in range(m):
        j = n+ind
        network.add_node(j)
        network.nodes[j]['type']="proposal"
        network.nodes[j]['conviction']=0
        network.nodes[j]['status']='candidate'
        network.nodes[j]['age']=0

        r_rv = gamma.rvs(3,loc=0.001, scale=10000)
        network.nodes[j]['funds_requested'] = r_rv

        for i in range(n):
            network.add_edge(i, j)

            rv = np.random.rand()
            a_rv = 1-4*(1-rv)*rv #polarized distribution
            network.edges[(i, j)]['affinity'] = a_rv
            network.edges[(i, j)]['tokens'] = 0
            network.edges[(i, j)]['conviction'] = 0
            network.edges[(i, j)]['type'] = 'support'

        proposals = get_nodes_by_type(network, 'proposal')
        total_requested = np.sum([ network.nodes[i]['funds_requested'] for i in proposals])

        network = initial_conflict_network(network, rate = .25)
        network = initial_social_network(network, scale = 1)

    return network, initial_supply, total_requested

def initial_social_network(network, scale = 1, sigmas=3):

    participants = get_nodes_by_type(network, 'participant')

    for i in participants:
        for j in participants:
            if not(j==i):
                influence_rv = expon.rvs(loc=0.0, scale=scale)
                if influence_rv > scale+sigmas*scale**2:
                    network.add_edge(i,j)
                    network.edges[(i,j)]['influence'] = influence_rv
                    network.edges[(i,j)]['type'] = 'influence'
    return network

def initial_conflict_network(network, rate = .25):

    proposals = get_nodes_by_type(network, 'proposal')

    for i in proposals:
        for j in proposals:
            if not(j==i):
                conflict_rv = np.random.rand()
                if conflict_rv < rate :
                    network.add_edge(i,j)
                    network.edges[(i,j)]['conflict'] = 1-conflict_rv
                    network.edges[(i,j)]['type'] = 'conflict'
    return network

def social_links(network, participant, scale = 1):

    participants = get_nodes_by_type(network, 'participant')

    i = participant
    for j in participants:
        if not(j==i):
            influence_rv = expon.rvs(loc=0.0, scale=scale)
            if influence_rv > scale+scale**2:
                network.add_edge(i,j)
                network.edges[(i,j)]['influence'] = influence_rv
                network.edges[(i,j)]['type'] = 'influence'
    return network

def conflict_links(network,proposal ,rate = .25):

    proposals = get_nodes_by_type(network, 'proposal')

    i = proposal
    for j in proposals:
        if not(j==i):
            conflict_rv = np.random.rand()
            if conflict_rv < rate :
                network.add_edge(i,j)
                network.edges[(i,j)]['conflict'] = 1-conflict_rv
                network.edges[(i,j)]['type'] = 'conflict'
    return network

def social_affinity_booster(network, proposal, participant):

    participants = get_nodes_by_type(network, 'participant')
    influencers = get_edges_by_type(network, 'influence')

    j=proposal
    i=participant

    i_tokens = network.nodes[i]['holdings']

    influence = np.array([network.edges[(i,node)]['influence'] for node in participants if (i, node) in influencers ])
    #print(influence)
    tokens = np.array([network.edges[(node,j)]['tokens'] for node in participants if (i, node) in influencers ])
    #print(tokens)


    influence_sum = np.sum(influence)

    if influence_sum>0:
        boosts = np.sum(tokens*influence)/(influence_sum*i_tokens)
    else:
        boosts = 0

    return np.sum(boosts)


def trigger_sweep(field, trigger_func,xmax=.2,default_alpha=.5):

    if field == 'token_supply':
        alpha = default_alpha
        share_of_funds = np.arange(.001,xmax,.001)
        total_supply = np.arange(0,10**9, 10**6)
        demo_data_XY = np.outer(share_of_funds,total_supply)

        demo_data_Z0=np.empty(demo_data_XY.shape)
        demo_data_Z1=np.empty(demo_data_XY.shape)
        demo_data_Z2=np.empty(demo_data_XY.shape)
        demo_data_Z3=np.empty(demo_data_XY.shape)
        for sof_ind in range(len(share_of_funds)):
            sof = share_of_funds[sof_ind]
            for ts_ind in range(len(total_supply)):
                ts = total_supply[ts_ind]
                tc = ts /(1-alpha)
                trigger = trigger_func(sof, 1, ts)
                demo_data_Z0[sof_ind,ts_ind] = np.log10(trigger)
                demo_data_Z1[sof_ind,ts_ind] = trigger
                demo_data_Z2[sof_ind,ts_ind] = trigger/tc #share of maximum possible conviction
                demo_data_Z3[sof_ind,ts_ind] = np.log10(trigger/tc)
        return {'log10_trigger':demo_data_Z0,
                'trigger':demo_data_Z1,
                'share_of_max_conv': demo_data_Z2,
                'log10_share_of_max_conv':demo_data_Z3,
                'total_supply':total_supply,
                'share_of_funds':share_of_funds}
    elif field == 'alpha':
        alpha = np.arange(.5,1,.01)
        share_of_funds = np.arange(.001,xmax,.001)
        total_supply = 10**9
        demo_data_XY = np.outer(share_of_funds,alpha)

        demo_data_Z4=np.empty(demo_data_XY.shape)
        demo_data_Z5=np.empty(demo_data_XY.shape)
        demo_data_Z6=np.empty(demo_data_XY.shape)
        demo_data_Z7=np.empty(demo_data_XY.shape)
        for sof_ind in range(len(share_of_funds)):
            sof = share_of_funds[sof_ind]
            for a_ind in range(len(alpha)):
                ts = total_supply
                a = alpha[a_ind]
                tc = ts /(1-a)
                trigger = trigger_func(sof, 1, ts)
                demo_data_Z4[sof_ind,a_ind] = np.log10(trigger)
                demo_data_Z5[sof_ind,a_ind] = trigger
                demo_data_Z6[sof_ind,a_ind] = trigger/tc #share of maximum possible conviction
                demo_data_Z7[sof_ind,a_ind] = np.log10(trigger/tc)

        return {'log10_trigger':demo_data_Z4,
               'trigger':demo_data_Z5,
               'share_of_max_conv': demo_data_Z6,
               'log10_share_of_max_conv':demo_data_Z7,
               'alpha':alpha,
               'share_of_funds':share_of_funds}

    else:
        return "invalid field"

def trigger_plotter(share_of_funds,Z, color_label,y, ylabel,cmap='jet'):
    dims = (10, 5)
    fig, ax = plt.subplots(figsize=dims)

    cf = plt.contourf(share_of_funds, y, Z.T, 100, cmap=cmap)
    cbar=plt.colorbar(cf)
    plt.axis([share_of_funds[0], share_of_funds[-1], y[0], y[-1]])
    #ax.set_xscale('log')
    plt.ylabel(ylabel)
    plt.xlabel('Share of Funds Requested')
    plt.title('Trigger Function Map')

    cbar.ax.set_ylabel(color_label)


def snap_plot(nets, size_scale = 1/500, ani = False, dims = (20,20), savefigs=False):


    last_net = nets[-1]

    last_props=get_nodes_by_type(last_net, 'proposal')
    M = len(last_props)
    last_parts=get_nodes_by_type(last_net, 'participant')
    N = len(last_parts)
    pos = {}

    for ind in range(N):
        i = last_parts[ind]
        pos[i] = np.array([0, 2*ind-N])

    for ind in range(M):
        j = last_props[ind]
        pos[j] = np.array([1, 2*N/M *ind-N])

    if ani:
        figs = []
        fig, ax = plt.subplots(figsize=dims)

    if savefigs:
        counter = 0
        length = 10
        import string
        unique_id = ''.join([np.random.choice(list(string.ascii_letters + string.digits)) for _ in range(length)])
    for net in nets:
        edges = get_edges_by_type(net, 'support')
        max_tok = np.max([net.edges[e]['tokens'] for e in edges])

        E = len(edges)

        net_props = get_nodes_by_type(net, 'proposal')
        net_parts = get_nodes_by_type(net, 'participant')
        net_node_label ={}

        num_nodes = len([node for node in net.nodes])

        node_color = np.empty((num_nodes,4))
        node_size = np.empty(num_nodes)

        edge_color = np.empty((E,4))
        cm = plt.get_cmap('Reds')

        cNorm  = colors.Normalize(vmin=0, vmax=max_tok)
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)

        net_cand = [j for j in net_props if net.nodes[j]['status']=='candidate']

        for j in net_props:
            node_size[j] = net.nodes[j]['funds_requested']*size_scale
            if net.nodes[j]['status']=="candidate":
                node_color[j] = colors.to_rgba('blue')
                trigger = net.nodes[j]['trigger']
                conviction = net.nodes[j]['conviction']
                percent_of_trigger = "          "+str(int(100*conviction/trigger))+'%'
                net_node_label[j] = str(percent_of_trigger)
            elif net.nodes[j]['status']=="active":
                node_color[j] = colors.to_rgba('orange')
                net_node_label[j] = ''
            elif net.nodes[j]['status']=="completed":
                node_color[j] = colors.to_rgba('green')
                net_node_label[j] = ''
            elif net.nodes[j]['status']=="failed":
                node_color[j] = colors.to_rgba('gray')
                net_node_label[j] = ''
            elif net.nodes[j]['status']=="killed":
                node_color[j] = colors.to_rgba('black')
                net_node_label[j] = ''

        for i in net_parts:
            node_size[i] = net.nodes[i]['holdings']*size_scale/10
            node_color[i] = colors.to_rgba('red')
            net_node_label[i] = ''

        included_edges = []
        for ind in range(E):
            e = edges[ind]
            tokens = net.edges[e]['tokens']
            edge_color[ind] = scalarMap.to_rgba(tokens)
            if e[1] in net_cand:
                included_edges.append(e)


        iE = len(included_edges)
        included_edge_color = np.empty((iE,4))
        for ind in range(iE):
            e = included_edges[ind]
            tokens = net.edges[e]['tokens']
            included_edge_color[ind] = scalarMap.to_rgba(tokens)

#        nx.draw(net,
#                pos=pos,
#                node_size = node_size,
#                node_color = node_color,
#                edge_color = included_edge_color,
#                edgelist=included_edges,
#                labels = net_node_label)
#        plt.title('Tokens Staked by Partipants to Proposals')

        if ani:
            nx.draw(net,
                    pos=pos,
                    node_size = node_size,
                    node_color = node_color,
                    edge_color = included_edge_color,
                    edgelist=included_edges,
                    labels = net_node_label, ax=ax)
            figs.append(fig)

        else:
            nx.draw(net,
                pos=pos,
                node_size = node_size,
                node_color = node_color,
                edge_color = included_edge_color,
                edgelist=included_edges,
                labels = net_node_label)
            plt.title('Tokens Staked by Partipants to Proposals')
            if savefigs:
                plt.savefig(unique_id+'_fig'+str(counter)+'.png')
                counter = counter+1
            plt.show()

    if ani:
        False
        #anim = animation.ArtistAnimation(fig, , interval=50, blit=True, repeat_delay=1000)
        #plt.show()

def pad(vec, length,fill=True):

    if fill:
        padded = np.zeros(length,)
    else:
        padded = np.empty(length,)
        padded[:] = np.nan

    for i in range(len(vec)):
        padded[i]= vec[i]

    return padded

def make2D(key, data, fill=False):
    maxL = data[key].apply(len).max()
    newkey = 'padded_'+key
    data[newkey] = data[key].apply(lambda x: pad(x,maxL,fill))
    reshaped = np.array([a for a in data[newkey].values])

    return reshaped
