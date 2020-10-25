from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import os
import glob

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as sts
import seaborn as sns

import simulation

from networkx.readwrite import json_graph

app = Flask(__name__, static_url_path='')
CORS(app)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


def jsonifyNetwork(network):
    obj = json_graph.node_link_data(network)
    return obj


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/api/cadcad', methods=['POST'])
def cadcad():
    try:
        params = request.get_json()

        hatchers = int(params['hatchers'])
        proposals = int(params['proposals'])
        hatch_tribute = float(params['hatch_tribute'])
        vesting_80p_unlocked = int(params['vesting_80p_unlocked'])
        exit_tribute = float(params['exit_tribute'])
        kappa = float(params['kappa'])
        days_to_80p_of_max_voting_weight = int(
            params['days_to_80p_of_max_voting_weight'])
        max_proposal_request = float(params['max_proposal_request'])

    except Exception as err:
        return str(err), 422

    c = simulation.simulation.CommonsSimulationConfiguration(hatchers=hatchers, proposals=proposals, days_to_80p_of_max_voting_weight=days_to_80p_of_max_voting_weight,
                                                             max_proposal_request=max_proposal_request, exit_tribute=exit_tribute)

    result, df = simulation.simrunner.run_simulation(c)

    for ind in range(len(df)):
        r = results[ind]['result']
        # print(results[ind]['simulation_parameters'])
        r.plot(x='timestep', y='funds')
        plt.savefig('static/plot8-'+str(ind)+'.png')
        plt.clf()

        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        df = r
        rdf = df[df.substep == 4].copy()

        rdf.plot(x='timestep', y=['funds', 'reserve', 'supply'], ax=ax1)
        rdf.plot(x='timestep', y='spot_price', style='--',
                 color='red', ax=ax2, legend=False)
        ax2.set_ylabel('Price in xDAI per Token', color='red')
        ax1.set_ylabel('Quantity of Assets')
        ax2.tick_params(axis='y', labelcolor='red')
        plt.title('Summary of Local Economy')
        plt.savefig('static/plot9-'+str(ind)+'.png')
        plt.clf()

    return jsonify({
        'results': ['plot8-0.png', 'plot9-0.png']
    })
