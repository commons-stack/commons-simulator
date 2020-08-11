from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import os
import glob

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as sts
import seaborn as sns

#import conviction files
from conviction_helpers import *
from conviction_system_logic3 import *
from bonding_curve_eq import *
from networkx.readwrite import json_graph

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

def jsonifyNetwork(network):
    obj = json_graph.node_link_data(network)
    return obj

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/cadcad', methods = ['GET', 'POST'])
def cadcad():
    try:
        n = getInteger('participants') #initial participants
        m = getInteger('proposals') #initial proposals

        alpha = getFloat('alpha')
        beta = getFloat('beta')

        exit_tribute = getFloat('exit_tribute')
        theta = getFloat('theta')

        initial_sentiment = 0.1 # getFloat('initial_sentiment')
        hatch_price = 0.1 # getFloat('hatch_price')
        kappa = 6 # getFloat('kappa')
        rho = 0.05 # getFloat('rho')

    except Exception as err:
        return str(err), 422

    #initializer
    network, initial_supply, total_requested = initialize_network(n,m)

    initial_funds = total_funds_given_total_supply(initial_supply, theta, hatch_price)

    initial_reserve, invariant, starting_price = initialize_bonding_curve(initial_supply, initial_price = hatch_price, kappa = kappa, theta = theta)

    initial_conditions = {
        'supply': initial_supply,
        'funds': initial_funds,
        'reserve': initial_reserve,
        'spot_price': starting_price,
        'sentiment': initial_sentiment,
        'network': network
    }

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
        'tax_rate': [exit_tribute]
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

        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        df = r
        rdf = df[df.substep==4].copy()

        rdf.plot(x='timestep', y=['funds', 'reserve','supply'], ax=ax1)
        rdf.plot(x='timestep', y='spot_price',style='--',color = 'red', ax=ax2, legend = False)
        ax2.set_ylabel('Price in xDAI per Token', color='red')
        ax1.set_ylabel('Quantity of Assets')
        ax2.tick_params(axis='y', labelcolor='red')
        plt.title('Summary of Local Economy')
        plt.savefig('static/plot9-'+str(ind)+'.png')
        plt.clf()

    return jsonify({
        'results': ['plot8-0.png', 'plot9-0.png']
    })
