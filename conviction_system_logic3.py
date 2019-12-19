import numpy as np
from conviction_helpers import get_nodes_by_type, get_edges_by_type, social_affinity_booster, conviction_order
from bonding_curve_eq import reserve, spot_price
#import networkx as nx
from scipy.stats import expon, gamma


#functions for partial state update block 1

#Driving processes: arrival of participants, proposals and funds
##-----------------------------------------
def gen_new_participant(network, new_participant_holdings):
    
    i = len([node for node in network.nodes])
    
    network.add_node(i)
    network.nodes[i]['type']="participant"
    
    s_rv = np.random.rand() 
    network.nodes[i]['sentiment'] = s_rv
    network.nodes[i]['holdings']=new_participant_holdings
    
    for j in get_nodes_by_type(network, 'proposal'):
        network.add_edge(i, j)
        
        rv = np.random.rand()
        a_rv = 1-4*(1-rv)*rv #polarized distribution
        network.edges[(i, j)]['affinity'] = a_rv
        network.edges[(i,j)]['tokens'] = a_rv*network.nodes[i]['holdings']
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
        
        

def driving_process(params, step, sL, s):
    
    #placeholder plumbing for random processes
    arrival_rate = 10/(1+s['sentiment'])
    rv1 = np.random.rand()
    new_participant = bool(rv1<1/arrival_rate)
    supporters = get_edges_by_type(s['network'], 'support')
    
    len_parts = len(get_nodes_by_type(s['network'], 'participant'))
    supply = s['supply']
    expected_holdings = .1*supply/len_parts
    if new_participant:
        h_rv = expon.rvs(loc=0.0, scale=expected_holdings)
        new_participant_holdings = h_rv
    else:
        new_participant_holdings = 0
    
    network = s['network']
    affinities = [network.edges[e]['affinity'] for e in supporters ]
    median_affinity = np.median(affinities)
    
    proposals = get_nodes_by_type(network, 'proposal')
    fund_requests = [network.nodes[j]['funds_requested'] for j in proposals if network.nodes[j]['status']=='candidate' ]
    
    funds = s['funds']
    total_funds_requested = np.sum(fund_requests)
    
    proposal_rate = 1/median_affinity * (1+total_funds_requested/funds)
    rv2 = np.random.rand()
    new_proposal = bool(rv2<1/proposal_rate)
    
    sentiment = s['sentiment']
    funds = s['funds']
    scale_factor = funds*sentiment**2/10000
    
    if scale_factor <1:
        scale_factor = 1
    
    #this shouldn't happen but expon is throwing domain errors
    if sentiment>.4: 
        funds_arrival = expon.rvs(loc = 0, scale = scale_factor )
    else:
        funds_arrival = 0
    
    return({'new_participant':new_participant,
            'new_participant_holdings':new_participant_holdings,
            'new_proposal':new_proposal, 
            'funds_arrival':funds_arrival})

    
#Mechanisms for updating the state based on driving processes
##---
def update_network(params, step, sL, s, _input):

    network = s['network']
    funds = s['funds']
    supply = s['supply']
    trigger_func = params['trigger_func']
    #print(trigger_func)

    new_participant = _input['new_participant'] #T/F
    new_proposal = _input['new_proposal'] #T/F

    if new_participant:
        new_participant_holdings = _input['new_participant_holdings']
        network = gen_new_participant(network, new_participant_holdings)
    
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

def increment_funds(params, step, sL, s, _input):
    
    funds = s['funds']
    funds_arrival = _input['funds_arrival']

    #increment funds
    funds = funds + funds_arrival
    
    key = 'funds'
    value = funds
    
    return (key, value)

def increment_supply(params, step, sL, s, _input):
    
    supply = s['supply']
    supply_arrival = _input['new_participant_holdings']

    #increment funds
    supply = supply + supply_arrival
    
    key = 'supply'
    value = supply
    
    return (key, value)

def increment_reserve(params, step, sL, s, _input):
    
    supply = s['supply']
    supply_arrival = _input['new_participant_holdings']

    #increment funds
    supply = supply + supply_arrival
    
    kappa = params['kappa']
    V0 = params['invariant']
    
    R = reserve(supply, V0, kappa)
    
    key = 'reserve'
    value = R
    
    return (key, value)

#functions for partial state update block 2

#Driving processes: completion of previously funded proposals
##-----------------------------------------

def check_progress(params, step, sL, s):
    
    network = s['network']
    proposals = get_nodes_by_type(network, 'proposal')
    
    completed = []
    failed = []
    for j in proposals:
        if network.nodes[j]['status'] == 'active':
            grant_size = network.nodes[j]['funds_requested']
            base_completion_rate=params['base_completion_rate']
            likelihood = 1.0/(base_completion_rate+np.log(grant_size))
            
            base_failure_rate = params['base_failure_rate']
            failure_rate = 1.0/(base_failure_rate+np.log(grant_size))
            if np.random.rand() < likelihood:
                completed.append(j)
            elif np.random.rand() < failure_rate:
                failed.append(j)
    
    return({'completed':completed, 'failed':failed})


#Mechanisms for updating the state based on check progress
##---
def complete_proposal(params, step, sL, s, _input):
    
    network = s['network']
    participants = get_nodes_by_type(network, 'participant')
    proposals = get_nodes_by_type(network, 'proposal')
    competitors = get_edges_by_type(network, 'conflict')
    
    completed = _input['completed']
    for j in completed:
        network.nodes[j]['status']='completed'

        for c in proposals:
             if (j,c) in competitors:
                 conflict = network.edges[(j,c)]['conflict']
                 for i in participants:
                     network.edges[(i,c)]['affinity'] = network.edges[(i,c)]['affinity'] *(1-conflict)

        for i in participants:
            force = network.edges[(i,j)]['affinity']
            sentiment = network.nodes[i]['sentiment']
            network.nodes[i]['sentiment'] = get_sentimental(sentiment, force, decay=0)

                
    
    failed = _input['failed']
    for j in failed:
        network.nodes[j]['status']='failed' 
        for i in participants:
            force = -network.edges[(i,j)]['affinity']
            sentiment = network.nodes[i]['sentiment']
            network.nodes[i]['sentiment'] = get_sentimental(sentiment, force, decay=0)
    
    key = 'network'
    value = network
    
    return (key, value)

def update_sentiment_on_completion(params, step, sL, s, _input):
    
    network = s['network']
    proposals = get_nodes_by_type(network, 'proposal')
    completed = _input['completed']
    failed = _input['failed']
    
    grants_outstanding = np.sum([network.nodes[j]['funds_requested'] for j in proposals if network.nodes[j]['status']=='active'])
    
    grants_completed = np.sum([network.nodes[j]['funds_requested'] for j in completed])
    grants_failed = np.sum([network.nodes[j]['funds_requested'] for j in failed])
    
    sentiment = s['sentiment']
    
    if grants_outstanding>0:
        force = (grants_completed-grants_failed)/grants_outstanding
    else:
        force=1
    mu = params['sentiment_decay']
    if (force >=0) and (force <=1):
        sentiment = get_sentimental(sentiment, force, mu)
    else:
        sentiment = get_sentimental(sentiment, 0, mu)
    
    
    key = 'sentiment'
    value = sentiment
    
    return (key, value)

def get_sentimental(sentiment, force, decay=0):
    mu = decay
    sentiment = sentiment*(1-mu) + force
    
    if sentiment > 1:
        sentiment = 1
        
    return sentiment

#functions for partial state update block 3

#Decision processes: trigger function policy
##-----------------------------------------

def trigger_function(params, step, sL, s):
    
    network = s['network']
    funds = s['funds']
    supply = s['supply']
    proposals = get_nodes_by_type(network, 'proposal')
    tmin = params['tmin']
    trigger_func = params['trigger_func']
    
    accepted = []
    triggers = {}
    funds_to_be_released = 0
    for j in proposals:
        if network.nodes[j]['status'] == 'candidate':
            requested = network.nodes[j]['funds_requested']
            age = network.nodes[j]['age']
            threshold = trigger_func(requested, funds, supply)
            if age > tmin:
                conviction = network.nodes[j]['conviction']
                if conviction >threshold:
                    accepted.append(j)
                    funds_to_be_released = funds_to_be_released + requested
        else:
            threshold = np.nan
            
        triggers[j] = threshold
        
        #catch over release and keep the highest conviction results
        if funds_to_be_released > funds:
            #print('funds ='+str(funds))
            #print(accepted)
            ordered = conviction_order(network, accepted)
            #print(ordered)
            accepted = []
            release = 0
            ind = 0
            while release + network.nodes[ordered[ind]]['funds_requested'] < funds:
                accepted.append(ordered[ind])
                release= network.nodes[ordered[ind]]['funds_requested']
                ind=ind+1
                
                    
    return({'accepted':accepted, 'triggers':triggers})
    
#functions for partial state update block 3

#state updates
##---

def decrement_funds(params, step, sL, s, _input):
    
    funds = s['funds']
    network = s['network']
    accepted = _input['accepted']

    #decrement funds
    for j in accepted:
        funds = funds - network.nodes[j]['funds_requested']
    
    key = 'funds'
    value = funds
    
    return (key, value)

def update_proposals(params, step, sL, s, _input):
    
    network = s['network']
    accepted = _input['accepted']
    triggers = _input['triggers']
    participants = get_nodes_by_type(network, 'participant')
    proposals = get_nodes_by_type(network, 'proposals')
    sensitivity = params['sensitivity']
    
    for j in proposals:
        network.nodes[j]['trigger'] = triggers[j]
    
    #bookkeeping conviction and participant sentiment
    for j in accepted:
        network.nodes[j]['status']='active'
        network.nodes[j]['conviction']=np.nan
        #change status to active
        for i in participants:
        
            #operating on edge = (i,j)
            #reset tokens assigned to other candidates
            network.edges[(i,j)]['tokens']=0
            network.edges[(i,j)]['conviction'] = np.nan
            
            #update participants sentiments (positive or negative) 
            affinities = [network.edges[(i,p)]['affinity'] for p in proposals if not(p in accepted)]
            if len(affinities)>1:
                max_affinity = np.max(affinities)
                force = network.edges[(i,j)]['affinity']-sensitivity*max_affinity
            else:
                force = 0
            
            #based on what their affinities to the accepted proposals
            network.nodes[i]['sentiment'] = get_sentimental(network.nodes[i]['sentiment'], force, False)
            
    
    key = 'network'
    value = network
    
    return (key, value)

def update_sentiment_on_release(params, step, sL, s, _input):
    
    network = s['network']
    proposals = get_nodes_by_type(network, 'proposal')
    accepted = _input['accepted']
    
    proposals_outstanding = np.sum([network.nodes[j]['funds_requested'] for j in proposals if network.nodes[j]['status']=='candidate'])
    
    proposals_accepted = np.sum([network.nodes[j]['funds_requested'] for j in accepted])
    
    sentiment = s['sentiment']
    force = proposals_accepted/proposals_outstanding
    if (force >=0) and (force <=1):
        sentiment = get_sentimental(sentiment, force, False)
    else:
        sentiment = get_sentimental(sentiment, 0, False)
    
    key = 'sentiment'
    value = sentiment
    
    return (key, value)


#functions for partial state update block 4

#Decision processes: trigger function policy
##---
def participants_decisions(params, step, sL, s):
    
    network = s['network']
    participants = get_nodes_by_type(network, 'participant')
    proposals = get_nodes_by_type(network, 'proposal')
    candidates = [j for j in proposals if network.nodes[j]['status']=='candidate']
    sensitivity = params['sensitivity']
    
    gain = .01
    delta_holdings={}
    proposals_supported ={}
    for i in participants:
        
        engagement_rate = .3*network.nodes[i]['sentiment']
        if np.random.rand()<engagement_rate:
        
            force = network.nodes[i]['sentiment']-sensitivity
            delta_holdings[i] = network.nodes[i]['holdings']*gain*force
            
            support = []
            for j in candidates:
                booster = social_affinity_booster(network, j, i)
                #print(booster)
                affinity = network.edges[(i, j)]['affinity']+booster
                cutoff = sensitivity*np.max([network.edges[(i,p)]['affinity'] for p in candidates])
                if cutoff <.5:
                    cutoff = .5
                
                if affinity > cutoff:
                    support.append(j)
            
            proposals_supported[i] = support
        else:
            delta_holdings[i] = 0
            proposals_supported[i] = [j for j in candidates if network.edges[(i,j)]['tokens']>0 ]
    
    return({'delta_holdings':delta_holdings, 'proposals_supported':proposals_supported})

#functions for partial state update block 4

#state updates
##---

def update_tokens(params, step, sL, s, _input):
    
    network = s['network']
    delta_holdings = _input['delta_holdings']
    proposals = get_nodes_by_type(network, 'proposal')
    candidates = [j for j in proposals if network.nodes[j]['status']=='candidate']
    proposals_supported = _input['proposals_supported']
    participants = get_nodes_by_type(network, 'participant')
    alpha = params['alpha']
    min_support = params['min_supp']
    
    for i in participants:
        network.nodes[i]['holdings'] = network.nodes[i]['holdings']+delta_holdings[i]
        supported = proposals_supported[i]
        total_affinity = np.sum([ network.edges[(i, j)]['affinity'] for j in supported])
        for j in candidates:
            if j in supported:
                normalized_affinity = network.edges[(i, j)]['affinity']/total_affinity
                network.edges[(i, j)]['tokens'] = normalized_affinity*network.nodes[i]['holdings']
            else:
                network.edges[(i, j)]['tokens'] = 0
            
            prior_conviction = network.edges[(i, j)]['conviction']
            current_tokens = network.edges[(i, j)]['tokens']
            network.edges[(i, j)]['conviction'] =current_tokens+alpha*prior_conviction
    
    for j in candidates:
        network.nodes[j]['conviction'] = np.sum([ network.edges[(i, j)]['conviction'] for i in participants])
        total_tokens = np.sum([network.edges[(i, j)]['tokens'] for i in participants ])
        if total_tokens < min_support:
            network.nodes[j]['status'] = 'killed'
    
    key = 'network'
    value = network
    
    return (key, value)

#organizing the bonding curve into a nested state would
    #make this code more efficient, lots of duplicated logic here

def update_supply(params, step, sL, s, _input):
    
    supply = s['supply']
    delta_holdings = _input['delta_holdings']
    delta_supply = np.sum([v for v in delta_holdings.values()])
    
    supply = supply + delta_supply
    
    key = 'supply'
    value = supply
    
    return (key, value)

def update_reserve(params, step, sL, s, _input):
    
    supply = s['supply']
    delta_holdings = _input['delta_holdings']
    delta_supply = np.sum([v for v in delta_holdings.values()])
    supply = supply + delta_supply
    
    kappa = params['kappa']
    V0 = params['invariant']
    
    #print("kappa="+str(kappa))
    R = reserve(supply, V0, kappa)
    
    key = 'reserve'
    value = R
    
    return (key, value)

def update_price(params, step, sL, s, _input):
    
    supply = s['supply']
    delta_holdings = _input['delta_holdings']
    delta_supply = np.sum([v for v in delta_holdings.values()])
    supply = supply + delta_supply
    
    kappa = params['kappa']
    V0 = params['invariant']
    
    R = reserve(supply, V0, kappa)
    price = spot_price(R, V0, kappa)
    
    key = 'spot_price'
    value = price
    
    return (key, value)

def update_funds(params, step, sL, s, _input):
    
    supply = s['supply']
    delta_holdings = _input['delta_holdings']
    minus_supply = np.sum([v for v in delta_holdings.values() if v<0])
    #print(minus_supply)
    min_supply = supply + minus_supply
    
    kappa = params['kappa']
    V0 = params['invariant']
    
    old_R = reserve(supply, V0, kappa)
    min_R = reserve(min_supply, V0, kappa)
    exit_tax = params['tax_rate']
    
    funds = s['funds']+exit_tax*(old_R-min_R)
    

    key = 'funds'
    value = funds
    
    return (key, value)

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