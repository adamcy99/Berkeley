#!/opt/anaconda/bin/python
"""
Helper functions for w261 week7 demo: regularized linear regression
"""
# general imports
import sys
import csv
import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib import colors


def OLSLoss(X, y, model):
    """
    Computes mean squared error for a linear model.
    INPUT:  X - numpy array (each row = augmented input point)
            y - numpy array of true outputs
            model  - [w_0, w_1] (coefficient & bias)
    """
    N = len(X)
    W = np.array(model)
    return 1/float(N) * sum((W.dot(X.T) - y)**2)

def OLSGradient(X, y, model):
    """
    Computes the gradient of the OLS loss function for
    the provided data & linear model.
    INPUT:  X - numpy array (each row = augmented input point)
            y - numpy array of true outputs
            model  - [w_0, w_1] (coefficient & bias)
    """
    N = len(X)
    W = np.array(model)
    return 2.0/N *(W.dot(X.T) - y).dot(X)

def RidgeGradient(X, y, model, reg_param):
    """
    Ridge regression gradient.
    INPUT:  X - numpy array (each row = augmented input point)
            y - numpy array of true outputs
            model  - [w_0, w_1] (coefficient & bias)
    """
    w = np.array(model[:-1])
    reg_term = reg_param * 2 * w
    return OLSGradient(X,y,model) + reg_term

def LassoGradient(X, y, model, reg_param):
    """
    Lasso regression gradient.
    INPUT:  X - numpy array (each row = augmented input point)
            y - numpy array of true outputs
            model  - [w_0, w_1] (coefficient & bias)
    """
    w = model[:-1]
    reg_term = reg_param * np.sign(w)
    return OLSGradient(X,y,model) + reg_term

def GDUpdate(X, y, nIter, init_model, learning_rate,
             reg_type = None, reg_param = 0, verbose = True):
    """
    Performs Gradient Descent Updates for linear models using OLS Loss
    or a specified regularization (l1/l2) method.
    INPUT:  X - numpy array (each row = augmented input point)
            y - numpy array of true outputs
            nIter - number of updates to perform
            init_model  - array w/ bias in last term
            learning_rate - step size for the update
            reg_param - regularization parameter
            verbose - (optional) printout each update
    OUTPUT: dict of {'models':[], 'loss':[]}
    """
    # keep track of our progress
    models = [init_model]
    loss = [OLSLoss(X,y,init_model)]

    # initialize gradient function
    if reg_type == 'l2':
        grad = lambda X,y,theta: RidgeGradient(X,y,theta,reg_param)
    elif reg_type == 'l1':
        grad = lambda X,y,theta: LassoGradient(X,y,theta,reg_param)
    else:
        grad = lambda X,y,theta: OLSGradient(X,y,theta)
    # perform updates
    for idx in range(nIter):
        gradient = grad(X, y, models[-1])
        update = np.multiply(gradient,learning_rate)
        new_model = models[-1] - update
        models.append(new_model)
        loss.append(OLSLoss(X,y,new_model))

    # return training history
    return np.array(models), loss

def plotLossContours(ax, X, y, w0_min, w0_max, w1_min, w1_max,
                    loss_func = OLSLoss):
    """
    OLS loss contours in the specified range added to the specified axis.
    This function passes a grid of 2D models to OLSLoss.
    """
    # grid parameters
    w0_step = (w0_max - w0_min)/20
    w1_step = (w1_max - w1_min)/20
    # create loss grid (flat for now)
    grid_w0, grid_w1 = np.mgrid[w0_min:w0_max:w0_step,
                                w1_min:w1_max:w1_step]
    grid_loss = [OLSLoss(X, y, model)
                 for model in zip(grid_w0.flatten(), grid_w1.flatten())]
    # plot loss contours
    topo_levels = np.logspace(min(np.log(min(grid_loss)),0.1),
                              min(np.log(max(grid_loss)),20))
    CS = ax.contour(grid_w0, grid_w1, np.array(grid_loss).reshape(20,20),
                    levels = topo_levels, cmap = 'rainbow',
                    linewidths = 2.0, alpha=0.35)


def compareDescent(X, y, hist1, hist2, labels):
    """
    Compare the two training histories
    Args:
        hist1, hist2 - lists of 2D models
        labels - names for the plot legend
        X, y - data
    """
    # set up axes
    fig, ax = plt.subplots(figsize=(10,6))
    ax.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.set_title("Model Parameter Space", fontsize=18)
    ax.set_xlabel('w_0')
    ax.set_ylabel(f'w_1')

    # plot the two training paths
    ax.plot(hist1.T[0], hist1.T[1], 'k', label=labels[0])
    ax.plot(hist2.T[0], hist2.T[1], 'k--', label=labels[1])

    # add contour plots
    w0_min = min(hist1.T[0].min(), hist2.T[0].min()) - 0.1
    w1_min = min(hist1.T[1].min(), hist2.T[1].min()) - 0.1
    w0_max = max(hist1.T[0].max(), hist2.T[0].max()) + 0.1
    w1_max = max(hist1.T[1].max(), hist2.T[1].max()) + 0.1
    plotLossContours(ax, X, y, w0_min, w0_max, w1_min, w1_max)

    # include legend
    plt.legend()


def plot2D(ax, X, y, xdim, color = 'b'):
    """
    Plot a higher dimensional dataset in 2D by
    electing just one of X's dimension to show.
    """
    # set up axes
    ax.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.set_title(f"2D projection (dimension {xdim})", fontsize=12)
    ax.set_xlabel(f'x_{xdim}')
    ax.set_ylabel('y')
    # plot the data
    ax.plot(X[:,xdim], y, 'o')

def compare2Dprojections(X, y, xdim, models, labels):
    """
    View side by side plots of n-dimensional models + data
    projected into 2D via the xdim.
    Args:
        models - list of sklearn linear models
        labels - same dimension titles
    """
    nmodels = len(models)

    # identify segments for projecting models down to 2D
    vals = X.T[xdim]
    ranges = [(vals[i], vals[i+1]) for i in range(len(vals) - 1)]

    # set up the plots
    fig, axes = plt.subplots(1,nmodels, figsize = (10,4))

    # plot each model
    for ax, lm, name in zip(axes, models, labels):

        # add data & title
        plot2D(ax, X, y, xdim)
        ax.set_title(name, fontsize=18)

        # apply model
        y_pred = lm.predict(X)
        x_vals = list(X.T[xdim])
        points = sorted(zip(x_vals, y_pred), key=lambda pair: pair[0])

        # add projections by segment
        for (x1,y1), (x2,y2) in zip(points[:-1], points[1:]):
            ax.plot([x1,x2],[y1,y2],'r--', alpha=0.5)


def compareLossCurves(X, y, reg_type, reg_param, grid):
    """
    Plot ridge & lasso curves (2D versions) alongside OLS.
    """
    # weights
    w0,w1 = grid

    # compute loss with & without regularization
    loss_no_reg = []
    loss_w_reg = []
    for W in grid.T:
        loss = OLSLoss(X,y,W)
        loss_no_reg.append(loss)
        if reg_type == 'l1':
            loss += np.abs(W[0]) * reg_param
        if reg_type == 'l2':
            loss += W[0]**2 * reg_param
        loss_w_reg.append(loss)

    # create figure
    fig = plt.figure(figsize = (15,12))

    # Lasso
    ax1 = fig.add_subplot(2, 2, 1, projection='3d')
    ax1.grid(color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    ax1.set_title(f"L1 penalty term (lambda = {reg_param})", fontsize=12)
    ax1.set_xlabel('w_0 (coefficient)')
    ax1.set_ylabel(f'w_1 (bias)')
    surf1 = ax1.plot_trisurf(w0, w1, np.abs(w0) * reg_param, cmap=cm.rainbow,
                            linewidths = 2.0, alpha=0.65)

    # Ridge
    ax2 = fig.add_subplot(2, 2, 2, projection='3d')
    #ax2.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
    ax2.set_title(f"L2 penalty term (lambda = {reg_param})", fontsize=12)
    ax2.set_xlabel('w_0 (coefficient)')
    ax2.set_ylabel(f'w_1 (bias)')
    surf2 = ax2.plot_trisurf(w0, w1, w0**2 * reg_param, cmap=cm.rainbow,
                            linewidths = 2.0, alpha=0.65)

    # OLS
    ax3 = fig.add_subplot(2, 2, 3, projection='3d')
    #ax3.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
    ax3.set_title(f"OLS with no penalty", fontsize=12)
    ax3.set_xlabel('w_0 (coefficient)')
    ax3.set_ylabel(f'w_1 (bias)')
    surf3 = ax3.plot_trisurf(w0, w1, loss_no_reg, cmap=cm.rainbow,
                            linewidths = 2.0, alpha=0.65)

    # OLS w/ reg
    ax4 = fig.add_subplot(2, 2, 4, projection='3d')
    #ax4.grid(color='grey', linestyle='-', linewidth=0.5, alpha=0.5)
    ax4.set_title(f"OLS with {reg_type} penalty (lambda = {reg_param})", fontsize=12)
    ax4.set_xlabel('w_0 (coefficient)')
    ax4.set_ylabel(f'w_1 (bias)')
    surf4 = ax4.plot_trisurf(w0, w1, loss_w_reg, cmap=cm.rainbow,
                            linewidths = 2.0, alpha=0.65)


