from flask import Flask, request, render_template
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

app = Flask(__name__, static_url_path='')


def getValue(name, default_value = 0.5):
    value = request.form.get(name)
    if value:
      return float(value)
    else:
      return default_value

@app.route('/', methods = ['GET', 'POST'])
def chartTest():
  alpha = getValue('alpha')
  beta = getValue('beta', .2)
  rho = getValue('rho', .02)
  plot_name = str(alpha)+str(beta)+str(rho)

  def trigger_threshold(requested, funds, supply, beta=beta , rho=rho):

      share = requested/funds
      if share < beta:
          return rho*supply/(beta-share)**2
      else:
          return np.inf

  dict1 = trigger_sweep('token_supply', trigger_threshold, beta, alpha)

  trigger_plotter(dict1['share_of_funds'],
                  dict1['log10_trigger'],
                  'Log10 Amount of Conviction Required to Pass',
                  dict1['total_supply'],
                  'Token Supply')
  axis = plt.axis()
  plt.text(.2*axis[0]+.8*axis[1],axis[-1]*1.01, 'fixed alpha = '+str(alpha))


  files = glob.glob('static/*')
  for f in files:
    os.remove(f)

  plt.savefig('static/plot1-'+plot_name+'.png')

  dict2 = trigger_sweep('alpha',trigger_threshold, xmax=beta)


  trigger_plotter(dict2['share_of_funds'],
                dict2['log10_share_of_max_conv'],
                'Log10 Share of Conviction Required to Pass',
                dict2['alpha'],
                'alpha')

  plt.savefig('static/plot2-'+plot_name+'.png')
  return render_template('threshold.html', name = 'Threshold', alpha = alpha, beta = beta, rho = rho, url1 ='plot1-'+plot_name+'.png', url2 ='plot2-'+plot_name+'.png')
