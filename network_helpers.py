from scipy.stats import expon, gamma
import numpy as np
import networkx as nx
from hatch import TokenBatch
from convictionvoting import trigger_threshold
from IPython.core.debugger import set_trace

def get_nodes_by_type(g, node_type_selection):
    return [node for node in g.nodes if g.nodes[node]['type']== node_type_selection ]

def get_edges_by_type(g, edge_type_selection):
    return [edge for edge in g.edges if g.edges[edge]['type']== edge_type_selection ]

def get_proposals(network):
    return get_nodes_by_type(network, "proposal")

def get_participants(network):
    return get_nodes_by_type(network, "participant")

def initial_social_network(network: nx.DiGraph, scale = 1, sigmas=3) -> nx.DiGraph:
    participants = get_participants(network)
    
    for i in participants:
        for j in participants:
            if not(j==i):
                influence_rv = expon.rvs(loc=0.0, scale=scale)
                if influence_rv > scale+sigmas*scale**2:
                    network.add_edge(i,j)
                    network.edges[(i,j)]['influence'] = influence_rv
                    network.edges[(i,j)]['type'] = 'influence'
    return network

def initial_conflict_network(network: nx.DiGraph, rate = .25) -> nx.DiGraph:
    proposals = get_proposals(network)
    
    for i in proposals:
        for j in proposals:
            if not(j==i):
                conflict_rv = np.random.rand()
                if conflict_rv < rate :
                    network.add_edge(i,j)
                    network.edges[(i,j)]['conflict'] = 1-conflict_rv
                    network.edges[(i,j)]['type'] = 'conflict'
    return network

def add_proposals_and_relationships_to_network(n: nx.DiGraph, proposals: int, funding_pool: float, token_supply: float) -> nx.DiGraph:
    participant_count = len(n)
    for i in range(proposals):
        j = participant_count + i
        n.add_node(j, type="proposal", conviction=0, status="candidate", age=0)

        r_rv = gamma.rvs(3,loc=0.001, scale=10000)
        n.nodes[j]['funds_requested'] = r_rv
        n.nodes[j]['trigger']= trigger_threshold(r_rv, funding_pool, token_supply)

        for i in range(participant_count):
            n.add_edge(i, j)
            rv = np.random.rand()
            a_rv = 1-4*(1-rv)*rv #polarized distribution
            n.edges[(i, j)]['affinity'] = a_rv
            n.edges[(i, j)]['tokens'] = 0
            n.edges[(i, j)]['conviction'] = 0
            n.edges[(i, j)]['type'] = 'support'
        
        n = initial_conflict_network(n, rate = .25)
        n = initial_social_network(n, scale = 1)
    return n
# =========================================================================================================
def gen_new_participant(network, new_participant_tokens):
    i = len([node for node in network.nodes])
    
    network.add_node(i)
    network.nodes[i]['type']="participant"
    
    s_rv = np.random.rand() 
    network.nodes[i]['sentiment'] = s_rv
    network.nodes[i]['holdings_vesting']=None
    network.nodes[i]['holdings_nonvesting']=TokenBatch(new_participant_tokens, 5, 5)
    
    # Connect this new participant to existing proposals.
    for j in get_nodes_by_type(network, 'proposal'):
        network.add_edge(i, j)
        
        rv = np.random.rand()
        a_rv = 1-4*(1-rv)*rv #polarized distribution
        network.edges[(i, j)]['affinity'] = a_rv
        network.edges[(i,j)]['tokens'] = a_rv*network.nodes[i]['holdings_nonvesting'].value
        network.edges[(i, j)]['conviction'] = 0
        network.edges[(i,j)]['type'] = 'support'
    
    return network

def gen_new_proposal(network, funds, supply, trigger_func, scale_factor = 1.0/100):
    j = len([node for node in network.nodes])
    network.add_node(j)
    network.nodes[j]['type']="proposal"
    
    network.nodes[j]['conviction']=0
    network.nodes[j]['status']='candidate'
    network.nodes[j]['age']=0
    
    rescale = funds*scale_factor
    r_rv = gamma.rvs(3,loc=0.001, scale=rescale)
    network.nodes[j]['funds_requested'] = r_rv
    
    network.nodes[j]['trigger']= trigger_func(r_rv, funds, supply)
    
    participants = get_nodes_by_type(network, 'participant')
    proposing_participant = np.random.choice(participants)
    
    for i in participants:
        network.add_edge(i, j)
        if i==proposing_participant:
            network.edges[(i, j)]['affinity']=1
        else:
            rv = np.random.rand()
            a_rv = 1-4*(1-rv)*rv #polarized distribution
            network.edges[(i, j)]['affinity'] = a_rv
            
        network.edges[(i, j)]['conviction'] = 0
        network.edges[(i,j)]['tokens'] = 0
        network.edges[(i,j)]['type'] = 'support'
        
    return network

def calc_total_funds_requested(network):
    proposals = get_proposals(network)
    fund_requests = [network.nodes[j]['funds_requested'] for j in proposals if network.nodes[j]['status']=='candidate' ]
    total_funds_requested = np.sum(fund_requests)
    return total_funds_requested

def calc_median_affinity(network):
    supporters = get_edges_by_type(network, 'support')
    affinities = [network.edges[e]['affinity'] for e in supporters ]
    median_affinity = np.median(affinities)
    return median_affinity

def driving_process(params, step, sL, s):
    network = s['network']
    commons = s['commons']
    funds = s['funding_pool']
    sentiment = s['sentiment']

    def randomly_gen_new_participant(participant_count, sentiment, current_token_supply, commons):
        arrival_rate = 10/(1+sentiment)
        rv1 = np.random.rand()
        new_participant = bool(rv1<1/arrival_rate)
    
        if new_participant:
            # Below line is quite different from Zargham's original, which gave
            # tokens instead. Here we randomly generate each participant's
            # post-Hatch investment, in DAI/USD. Here the settings for
            # expon.rvs() should generate investments of ~0-500 DAI.
            new_participant_investment = expon.rvs(loc=0.0, scale=100)
            new_participant_tokens = commons.dai_to_tokens(new_participant_investment)
            return new_participant, new_participant_investment, new_participant_tokens
        else:
            return new_participant, 0, 0

    def randomly_gen_new_proposal(total_funds_requested, median_affinity, funding_pool):
        proposal_rate = 1/median_affinity * (1+total_funds_requested/funding_pool)
        rv2 = np.random.rand()
        new_proposal = bool(rv2<1/proposal_rate)
        return new_proposal

    def randomly_gen_new_funding(funds, sentiment):
        """
        Each step, more funding comes to the Commons through the exit tribute,
        because after the hatching phase, all incoming money goes to the
        collateral reserve, not to the funding pool.
        """
        scale_factor = funds*sentiment**2/10000
        if scale_factor <1:
            scale_factor = 1

        #this shouldn't happen but expon is throwing domain errors
        if sentiment>.4: 
            funds_arrival = expon.rvs(loc = 0, scale = scale_factor )
        else:
            funds_arrival = 0
        return funds_arrival
    
    new_participant, new_participant_investment, new_participant_tokens = randomly_gen_new_participant(len(get_participants(network)), sentiment, s['token_supply'], commons)
    
    new_proposal = randomly_gen_new_proposal(calc_total_funds_requested(network), calc_median_affinity(network), funds)
    
    funds_arrival = randomly_gen_new_funding(funds, sentiment)
    
    return({'new_participant':new_participant,
            'new_participant_investment':new_participant_investment,
            'new_participant_tokens': new_participant_tokens,
            'new_proposal':new_proposal, 
            'funds_arrival':funds_arrival})

def add_participants_proposals_to_network(params, step, sL, s, _input):
    network = s['network']
    funds = s['funding_pool']
    supply = s['token_supply']

    trigger_func = params[0]["trigger_threshold"][0]

    new_participant = _input['new_participant'] #T/F
    new_proposal = _input['new_proposal'] #T/F

    if new_participant:
        network = gen_new_participant(network, _input['new_participant_tokens'])
    
    if new_proposal:
        network= gen_new_proposal(network,funds,supply,trigger_func )
    
    #update age of the existing proposals
    proposals = get_nodes_by_type(network, 'proposal')
    
    for j in proposals:
        network.nodes[j]['age'] =  network.nodes[j]['age']+1
        if network.nodes[j]['status'] == 'candidate':
            requested = network.nodes[j]['funds_requested']
            network.nodes[j]['trigger'] = trigger_func(requested, funds, supply)
        else:
            network.nodes[j]['trigger'] = np.nan
            
    key = 'network'
    value = network
    
    return (key, value)