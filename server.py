from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
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
CORS(app)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

def getInteger(name, default_value = 1):
    value = request.form.get(name)
    if value:
      return int(value)
    else:
      return default_value

def getFloat(name, default_value = None):
    value = request.form.get(name)
    if value:
        return float(value)
    elif default_value != None:
        return default_value
    else:
        raise Exception(name + ' not defined')

@app.route('/')
def index():
    return '<h1>Conviction Voting demo</h1><form action="step1" method="post"><button>Start</button></form>'

@app.route('/conviction', methods = ['POST'])
def conviction():
  try:
      beta = getFloat('beta')
      rho = getFloat('rho')
  except Exception as err:
      print(err)
      return str(err), 422
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
  return jsonify({'beta': beta, 'rho': rho, 'url1': 'plot1-'+plot_name+'.png', 'url2': 'plot2-'+plot_name+'.png'})

@app.route('/community', methods = ['GET', 'POST'])
def community():
    try:
        beta = getFloat('beta')
        rho = getFloat('rho')

        n = getInteger('participants') #initial participants
        m = getInteger('proposals') #initial proposals

        initial_sentiment = getFloat('initial_sentiment')

        theta = getFloat('theta')
        sale_price = getFloat('sale_price')

    except Exception as err:
        return str(err), 422

    plot_name = str(beta)+str(rho)

    def trigger_threshold(requested, funds, supply, beta=beta , rho=rho):

      share = requested/funds
      if share < beta:
          return rho*supply/(beta-share)**2
      else:
          return np.inf

    def TFGTS(total_supply):
        #wrap initializer params to pass the function correctly
        return total_funds_given_total_supply(total_supply, theta = theta, initial_price = sale_price)

    #initializer
    network, initial_funds, initial_supply, total_requested = initialize_network(n,m,TFGTS,trigger_threshold)

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

    return jsonify({
      # inputs
      'beta': beta,
      'rho': rho,
      'participants': m,
      'proposals': n,
      'initial_sentiment': initial_sentiment,
      'theta': theta,
      'sale_price': sale_price,
      # outputs
      'initial_supply': initial_supply,
      'initial_funds': initial_funds,
      'results': [
        'plot3-'+plot_name+'.png',
        'plot4-'+plot_name+'.png',
        'plot5-'+plot_name+'.png',
        'plot6-'+plot_name+'.png',
        'plot7-'+plot_name+'.png',
      ]
    })

@app.route('/abc', methods = ['GET', 'POST'])
def abc():
    try:
        initial_supply = getFloat('initial_supply')
        initial_price = getFloat('initial_price')
        kappa = getInteger('kappa')
        theta = getFloat('theta')
    except Exception as err:
        return str(err), 422
    initial_reserve, invariant, initial_price= initialize_bonding_curve(initial_supply, initial_price = sale_price, kappa = kappa, theta = theta)
    return jsonify({
        # outputs
        'initial_reserve': initial_reserve,
        'invariant': invariant,
        'initial_price': initial_price
    })

@app.route('/cadcad', methods = ['GET', 'POST'])
def cadcad():

    try:
        alpha = getFloat('alpha')
        exit_fee = getFloat('exit_fee')

        kappa = getFloat('kappa')
        invariant = getFloat('invariant')
        beta = getFloat('beta')
        rho = getFloat('rho')

        initial_conditions = {
          'supply': getFloat('initial_supply'),
          'funds': getFloat('initial_funds'),
          'reserve': getFloat('initial_reserve'),
          'spot_price': getFloat('initial_price'),
          'sentiment': getFloat('initial_sentiment'),
          'network': nx.read_gpickle('static/network.gpickle')
        }

    except Exception as err:
        return str(err), 422

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
    return jsonify({
        'results': ['plot8-0.png']
    })
