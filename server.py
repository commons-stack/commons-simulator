from flask import Flask, request, render_template
import os
import glob

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as sts
import seaborn as sns

import yaml

#import conviction files
from conviction_helpers import *
from conviction_system_logic3 import *
from bonding_curve_eq import *

app = Flask(__name__, static_url_path='')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

def getInteger(name, default_value = 1):
    value = request.form.get(name)
    if value:
      return int(value)
    else:
      return default_value

def getFloat(name, default_value = 0.5):
    value = request.form.get(name)
    if value:
      return float(value)
    else:
      return default_value

@app.route('/')
def index():
    return '<h1>Conviction Voting demo</h1><form action="step1" method="post"><button>Start</button></form>'

@app.route('/step1', methods = ['POST'])
def demoStep1():
  beta = getFloat('beta', .2)
  rho = getFloat('rho', .02)
  plot_name = str(beta)+str(rho)

  def trigger_threshold(requested, funds, supply, beta=beta , rho=rho):

      share = requested/funds
      if share < beta:
          return rho*supply/(beta-share)**2
      else:
          return np.inf

  dict1 = trigger_sweep('token_supply', trigger_threshold, beta)

  trigger_plotter(dict1['share_of_funds'],
                  dict1['log10_trigger'],
                  'Log10 Amount of Conviction Required to Pass',
                  dict1['total_supply'],
                  'Token Supply')
  axis = plt.axis()
  #plt.text(.2*axis[0]+.8*axis[1],axis[-1]*1.01, 'fixed alpha = '+str(alpha))


  # files = glob.glob('static/*')
  # for f in files:
  #   os.remove(f)

  plt.savefig('static/plot1-'+plot_name+'.png')
  plt.clf()

  dict2 = trigger_sweep('alpha',trigger_threshold, xmax=beta)


  trigger_plotter(dict2['share_of_funds'],
                dict2['log10_share_of_max_conv'],
                'Log10 Share of Conviction Required to Pass',
                dict2['alpha'],
                'alpha')

  plt.savefig('static/plot2-'+plot_name+'.png')
  plt.clf()
  return render_template('threshold.html', name = 'Threshold', beta = beta, rho = rho, url1 ='plot1-'+plot_name+'.png', url2 ='plot2-'+plot_name+'.png')

@app.route('/step2', methods = ['GET', 'POST'])
def demoStep2():

    beta = getFloat('beta', .2)
    rho = getFloat('rho', .02)
    plot_name = str(beta)+str(rho)

    def trigger_threshold(requested, funds, supply, beta=beta , rho=rho):

      share = requested/funds
      if share < beta:
          return rho*supply/(beta-share)**2
      else:
          return np.inf

    n= getInteger('n', 60) #initial participants
    m= getInteger('m', 3) #initial proposals

    initial_sentiment = getFloat('initial_sentiment', .6)

    theta =getFloat('theta', .35)
    kappa = getInteger('kappa', 6)
    sale_price = getFloat('sale_price', .1)

    def TFGTS(total_supply):
        #wrap initializer params to pass the function correctly
        return total_funds_given_total_supply(total_supply, theta = theta, initial_price = sale_price)

    #initializers
    network, initial_funds, initial_supply, total_requested = initialize_network(n,m,TFGTS,trigger_threshold)
    initial_reserve, invariant, initial_price= initialize_bonding_curve(initial_supply, initial_price = sale_price, kappa =kappa, theta = theta)

    proposals = get_nodes_by_type(network, 'proposal')
    participants = get_nodes_by_type(network, 'participant')
    supporters = get_edges_by_type(network, 'support')
    influencers = get_edges_by_type(network, 'influence')
    competitors = get_edges_by_type(network, 'conflict')

    nx.draw_kamada_kawai(network, nodelist = participants, edgelist=influencers)
    plt.title('Participants Social Network')
    plt.savefig('static/plot3-'+plot_name+'.png')
    plt.clf()

    nx.draw_kamada_kawai(network, nodelist = proposals, edgelist=competitors, node_color='b')
    plt.title('Proposals Conflict Network')
    plt.savefig('static/plot4-'+plot_name+'.png')
    plt.clf()

    plt.hist([ network.nodes[i]['holdings'] for i in participants])
    plt.title('Histogram of Participants Token Holdings')
    plt.savefig('static/plot5-'+plot_name+'.png')
    plt.clf()

    plt.hist([ network.nodes[i]['funds_requested'] for i in proposals])
    plt.title('Histogram of Proposals Funds Requested')
    plt.savefig('static/plot6-'+plot_name+'.png')
    plt.clf()

    affinities = np.empty((n,m))
    for i_ind in range(n):
        for j_ind in range(m):
            i = participants[i_ind]
            j = proposals[j_ind]
            affinities[i_ind][j_ind] = network.edges[(i,j)]['affinity']

    dims = (20, 5)
    fig, ax = plt.subplots(figsize=dims)

    sns.heatmap(affinities.T,
                xticklabels=participants,
                yticklabels=proposals,
                square=True,
                cbar=True,
                ax=ax)

    plt.title('affinities between participants and proposals')
    plt.ylabel('proposal_id')
    plt.xlabel('participant_id')
    plt.savefig('static/plot7-'+plot_name+'.png')
    plt.clf()

    nx.write_gpickle(network, 'static/network.gpickle')
    initial_conditions = {
      'supply': float(initial_supply),
      'funds': float(initial_funds),
      'reserve': float(initial_reserve),
      'spot_price': float(initial_price),
      'sentiment': float(initial_sentiment),
    }
    params = {
        'beta': float(beta),
        'rho': float(rho),
        'invariant': float(invariant),
        'kappa': float(kappa)
    }
    with open(r'static/conditions.yaml', 'w') as file:
      yaml.dump(initial_conditions, file)
    with open(r'static/params.yaml', 'w') as file:
      yaml.dump(params, file)

    return render_template(
      'network.html',
      name = 'Network',
      plot_name=plot_name,
      # inputs
      beta=beta,
      rho=rho,
      m=m,
      n=n,
      initial_sentiment=initial_sentiment,
      theta=theta,
      kappa=kappa,
      sale_price=sale_price,
      # outputs
      invariant=invariant,
      initial_supply=initial_supply,
      initial_funds=initial_funds,
      initial_reserve=initial_reserve,
      initial_price=initial_price
    )


@app.route('/step3', methods = ['GET', 'POST'])
def demoStep3():

    alpha = getFloat('alpha', 0.9)
    exit_fee = getFloat('exit_fee', .02)

    with open(r'static/conditions.yaml') as file:
        initial_conditions = yaml.load(file, Loader=yaml.FullLoader)
        initial_conditions['network'] = nx.read_gpickle('static/network.gpickle')

    with open(r'static/params.yaml') as file:
        params = yaml.load(file, Loader=yaml.FullLoader)
    kappa = params['kappa']
    invariant = params['invariant']
    beta = params['beta']
    rho = params['rho']

    def trigger_threshold(requested, funds, supply, beta=beta, rho=rho):

      share = requested/funds
      if share < beta:
          return rho*supply/(beta-share)**2
      else:
          return np.inf

    params= {
        'sensitivity': [.75],
        'tmin': [7], #unit days; minimum periods passed before a proposal can pass
        'min_supp':[50], #number of tokens that must be stake for a proposal to be a candidate
        'sentiment_decay': [.01], #termed mu in the state update function
        'alpha': [alpha],
        'base_completion_rate': [100],
        'base_failure_rate': [200],
        'trigger_func': [trigger_threshold],
        'kappa': [kappa], #bonding curve curvature
        'invariant': [invariant], #set by bonding curve choices
        'tax_rate': [exit_fee]
        }

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Settings of general simulation parameters, unrelated to the system itself
    # `T` is a range with the number of discrete units of time the simulation will run for;
    # `N` is the number of times the simulation will be run (Monte Carlo runs)
    time_periods_per_run = 100
    monte_carlo_runs = 1

    from cadCAD.configuration.utils import config_sim
    simulation_parameters = config_sim({
        'T': range(time_periods_per_run),
        'N': monte_carlo_runs,
        'M': params
    })




    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # The Partial State Update Blocks
    partial_state_update_blocks = [
        {
            'policies': {
                #new proposals or new participants
                'random': driving_process
            },
            'variables': {
                'network': update_network,
                'funds':increment_funds,
                'supply':increment_supply,
                'reserve': increment_reserve
            }
        },
        {
          'policies': {
              'completion': check_progress #see if any of the funded proposals completes
            },
            'variables': { # The following state variables will be updated simultaneously
                'sentiment': update_sentiment_on_completion, #note completing decays sentiment, completing bumps it
                'network': complete_proposal #book-keeping
            }
        },
            {
          'policies': {
              'release': trigger_function #check each proposal to see if it passes
            },
            'variables': { # The following state variables will be updated simultaneously
                'funds': decrement_funds, #funds expended
                'sentiment': update_sentiment_on_release, #releasing funds can bump sentiment
                'network': update_proposals #reset convictions, and participants sentiments
                                            #update based on affinities
            }
        },
        {
            'policies': {
                #currently naive decisions; future: strategic
                'participants_act': participants_decisions, #high sentiment, high affinity =>buy
                                                            #low sentiment, low affinities => burn
                                                            #assign tokens to top affinities
            },
            'variables': {
                'supply': update_supply, #book-keeping from participants decisions
                'reserve': update_reserve, #funds under the bonding curve
                'spot_price': update_price, #new bonding curve spot price
                'funds': update_funds, #capture taxes
                'network': update_tokens #update everyones holdings
                                        #and their conviction for each proposal
            }
        }
    ]

    from cadCAD import configs
    configs.clear()

    from cadCAD.configuration import append_configs
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # The configurations above are then packaged into a `Configuration` object
    append_configs(
        initial_state=initial_conditions, #dict containing variable names and initial values
        partial_state_update_blocks=partial_state_update_blocks, #dict containing state update functions
        sim_configs=simulation_parameters #dict containing simulation parameters
    )

    from tabulate import tabulate
    from cadCAD.engine import ExecutionMode, ExecutionContext, Executor
    from cadCAD import configs
    import pandas as pd

    exec_mode = ExecutionMode()
    multi_proc_ctx = ExecutionContext(context=exec_mode.multi_proc)
    run = Executor(exec_context=multi_proc_ctx, configs=configs)


    i = 0
    verbose = False
    results = {}
    for raw_result, tensor_field in run.execute():
        result = pd.DataFrame(raw_result)
        if verbose:
            print()
            print(f"Tensor Field: {type(tensor_field)}")
            print(tabulate(tensor_field, headers='keys', tablefmt='psql'))
            print(f"Output: {type(result)}")
            print(tabulate(result, headers='keys', tablefmt='psql'))
            print()
        results[i] = {}
        results[i]['result'] = result
        results[i]['simulation_parameters'] = simulation_parameters[i]
        i += 1


    for ind in range(len(results)):
        r=results[ind]['result']
        #print(results[ind]['simulation_parameters'])
        r.plot(x='timestep', y='funds')
        plt.savefig('static/plot8-'+str(ind)+'.png')
        plt.clf()
    return render_template(
      'cadcad.html',
      name = 'cadCAD simulation', alpha=alpha, exit_fee=exit_fee, n_results=len(results))
