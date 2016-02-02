# TODO Test out different types of polynomial chaos methods

# TODO Test correlation

# TODO find a better way to store tmp files

# TODO, only use evaluateNodeFunction if it is a neuron model,
# withouth a neuronmodel we will not have problems with neuron and chaospy

# TODO Do a regression analysis to figure out which variables are dependent on
# each other

# TODO Use a recursive neural network to do something?

# TODO have the option of saving the exploration by parameters instead of by distribution

# Figures are always saved on the format:
# output_dir_figures/distribution_interval/parameter_value-that-is-plotted.figure-extension

# TODO use sumatra when starting runs

# TODO save the entire class to file

# TODO Add suport for canceling a simulation when it is above a certain memory theeshold

# TODO incorporate singleNeuronRun into a class of file

# TODO problems with new neuron models, and their path

# TODO make it so setup.py install all requirements

# TODO make it so rosenblatt transform code looks pretier and easier

# TODO Rewrite model.py so it use kwargs to send options back and forth instead of argparse

# TODO find out where to save parameter distributions and parameter objects. In
# the least remove the problems with parameters and setParameters beeing two
# different things

# TODO Reimplement MC method, and implement a method for comparing the results

# TODO implement a feature description in features

# TODO Reimplement sensitivity ranking, but for all features and not only the diirect_comparison

# TODO placement of feature bar plots

# TODO Decide if the HH model should return Vm - 65 or just Vm

# TODO Make sending of model keywords simpler than it currently is. Use a
# dictionary similar to kwargs?

# TODO create a progressbar using tqdm

# TODO recreate the save function to only save one parameter run in each hdf5
# file. Consider saving into seperate .npy files

# TODO Rename direct_comparison to directComparison so that it is named the
# same as other features

# TODO Make the PC code handle other 2d features than only direct_comparison

# TODO Make 3d plots of 2d features and 2d plots of 1d features

# TODO calculate sensitivity in MC method

# TODO Shoud single parameter results be stored?

# TODO rewrite plotting code to be a series of functions?

# TODO combine save_data and save_data_dir into the save variable?

# TODO use _ before hidden variables

# TODO make suport for This type of feature, with a new t
#      def testUt(self):
#           return self.t, self.U

# TODO Add a option for models with variable timesteps

import time
import os
import h5py
import sys

import numpy as np
import chaospy as cp
import multiprocessing as mp

from xvfbwrapper import Xvfb

# Imported from my own files
from uncertainpy.features import ImplementedNeuronFeatures
from uncertainpy.evaluateNodeFunction import evaluateNodeFunction
from uncertainpy.plotting.plotUncertainty import PlotUncertainty

class UncertaintyEstimation():
    def __init__(self, model,
                 features=None,
                 feature_list=None,
                 save_figures=False,
                 output_dir_figures="figures/",
                 figureformat=".png",
                 save_data=True,
                 output_dir_data="data/",
                 output_dir_gif="gif/",
                 output_data_filename=None,
                 supress_model_graphics=True,
                 supress_model_output=True,
                 CPUs=mp.cpu_count(),
                 interpolate_union=False,
                 rosenblatt=False,
                 nr_mc_samples=10**3,
                 nr_pc_mc_samples=10**5,
                 **kwargs):
        """
Uncertainty Estimation object

Parameters
----------
Required arguments

model : Model Object
    The model on which to quantify uncertaintes.

Optional arguments

features : Feature Object
    Default is ImplementedNeuronFeatures
feature_list : list
    A list of all features to be calculated.
    Default is None, where no features will be calculated.
save_figures : bool
    If figures should be created and saved.
    This is deprecated code from before many changes
    and might therefore not work. Recommend using
    PlotUncertainty and plotting from saved files
    instead.
    Default is False
output_dir_figures : str
    Folder where figures is saved.
    Default is figures/.
figureformat : ".png"
    The format figures are saved in.
    Matplotlib is used to plot, and most matplotlib backends support
    png, pdf, ps, eps and svg.
    Default is .png
save_data : bool
    If data should be saved to a hdf5 file.
    Default is True.
output_dir_data : str
    Folder where the data is saved.
    Default is "data/".
output_data_filename : str
    The name of the output file.
    Default is the name of the model.
supress_model_graphics : bool
    If the graphical output from the model
    should be supressed, such as GUI.
    Escpecially usefull for the Neuron simulator models.
    Default is True.
supress_model_output : True
    Supress terminal output from the model.
    Note: set this to false when debugging your model,
    otherwise print statements will be supressed.
    Defualt is True.
CPUs : int
    The bumber of CPUs to perform
    calculations on.
    Defualt is mp.cpu_count() - the number of CPUs on your computer
interpolate_union : bool
    If a unionf of all times from the model should be be used.
    If not, the highest amount of time values is used, and the results are interpolated.
    This is only necessary if your model returns has variable timesteps.
    Default is False.
rosenblatt : False
    If a rosenblatt transformation should be used.
    Use this if you have dependent uncertain
    parameters.
    Note: not been tested on dependent uncertain
    parameters.
    Defualt is False.
nr_mc_samples : int
    The number of samples usend when performing a Monte Carlo
    Method.
    Defualt is 10**3.
nr_pc_mc_samples : int
    The number of samples when using the polynomal chaos
    polynomial as a surrogate model for a Monte Carlo method.
    Default is 10**5.

**kwargs : dict
    Optional arguments to be sent to other classes.
    Currently only features support recieving optional
    arguments.

Methods
-------

resetValues
evaluateNodeFunctionList
createPCExpansion
evaluateNodes
singleParameterPCAnalysis
PCAnalysis
MC
timePassed
singleParameters
allParameters
singleParametersMC
allParametersMC
sensitivityRanking
save

Returns
-------

Examples
--------
For example on use see:
    hodgkin-huxley_uncertainty_estimation.py
    izhikevich_uncertainty_estimation.py
    lgn_uncertainty_estimation.py
    coffe_uncertainty_estimation.py
        """


        # TODO there is something weird with features here. the Default should
        # probably not be NeuronFeatures
        if features is None:
            self.features = ImplementedNeuronFeatures()
        else:
            self.features = features

        if feature_list == "all":
            self.feature_list = self.features.implementedFeatures()
        elif feature_list is None:
            self.feature_list = []
        else:
            self.feature_list = feature_list

        self.save_figures = save_figures
        self.figureformat = figureformat
        self.save_data = save_data
        self.output_dir_data = output_dir_data

        self.supress_model_graphics = supress_model_graphics
        self.supress_model_output = supress_model_output
        self.CPUs = CPUs

        self.model = model

        self.interpolate_union = interpolate_union
        self.rosenblatt = rosenblatt

        self.kwargs = kwargs

        self.M = 3
        self.nr_mc_samples = nr_mc_samples
        self.nr_pc_mc_samples = nr_pc_mc_samples

        self.resetValues()

        self.plot = PlotUncertainty(data_dir=self.output_dir_data,
                                    output_dir_figures=output_dir_figures,
                                    output_dir_gif=output_dir_gif,
                                    figureformat=figureformat)


        if output_data_filename is None:
            self.output_data_filename = self.model.__class__.__name__
        else:
            self.output_data_filename = output_data_filename

        self.t_start = time.time()


    def __del__(self):
        pass


    # def __getstate__(self):
    #     self_dict = self.__dict__.copy()
    #     del self_dict['pool']
    #     return self_dict
    #
    #
    # def __setstate__(self, state):
    #     self.__dict__.update(state)


    def resetValues(self):
        self.parameter_names = None
        self.parameter_space = None

        self.U = {}
        self.U_hat = {}
        self.distribution = None
        self.solves = None
        self.t = {}
        self.E = {}
        self.Var = {}
        self.U_mc = {}  # TODO Is this needed to save?
        self.p_05 = {}
        self.p_95 = {}
        self.sensitivity = {}
        self.P = None



    def evaluateNodeFunctionList(self, nodes):
        data = []
        for node in nodes:
            data.append((self.model.cmd(),
                         self.supress_model_output,
                         node,
                         self.uncertain_parameters,
                         self.feature_list,
                         self.features.cmd(),
                         self.kwargs))
        return data


    def createPCExpansion(self, parameter_name=None, nr_pc_samples=None):

        # TODO find a good way to solve the parameter_name poblem
        if parameter_name is None:
            parameter_space = self.model.parameters.getUncertain("parameter_space")
            self.uncertain_parameters = self.model.parameters.getUncertain()
        else:
            parameter_space = [self.model.parameters.get(parameter_name).parameter_space]
            self.uncertain_parameters = [parameter_name]



        if self.rosenblatt:
            # Create the Multivariat normal distribution
            dist_MvNormal = []
            for parameter in self.model.parameters.getUncertain("value"):
                dist_MvNormal.append(cp.Normal())

            dist_MvNormal = cp.J(*dist_MvNormal)


            self.distribution = cp.J(*parameter_space)
            # self.P = cp.orth_ttr(self.M, self.distribution)
            self.P = cp.orth_ttr(self.M, dist_MvNormal)

            if nr_pc_samples is None:
                nr_pc_samples = 2*len(self.P) + 1

            nodes_MvNormal = dist_MvNormal.sample(nr_pc_samples, "M")
            # nodes_MvNormal, weights_MvNormal = cp.generate_quadrature(3, dist_MvNormal,
            #                                                           rule="J", sparse=True)

            nodes = self.distribution.inv(dist_MvNormal.fwd(nodes_MvNormal))
            # weights = weights_MvNormal*\
            #    self.distribution.pdf(nodes)/dist_MvNormal.pdf(nodes_MvNormal)

            self.distribution = dist_MvNormal

        else:
            self.distribution = cp.J(*parameter_space)
            self.P = cp.orth_ttr(self.M, self.distribution)

            if nr_pc_samples is None:
                nr_pc_samples = 2*len(self.P) + 1

            nodes = self.distribution.sample(nr_pc_samples, "M")
            # nodes, weights = cp.generate_quadrature(3, self.distribution, rule="J", sparse=True)





        solves = self.evaluateNodes(nodes)

        self.features_2d = []
        self.features_1d = []

        for feature in solves[0]:
            if hasattr(solves[0][feature][1], "__iter__"):
                self.features_2d.append(feature)
            else:
                self.features_1d.append(feature)


        for feature in self.features_2d:
            if solves[0][feature][0] is None:
                self.t[feature] = None
                self.U[feature] = solves[0][feature][1]
            elif hasattr(solves[0][feature][0], "__iter__"):
                ts = []
                interpolation = []
                for solved in solves:
                    ts.append(solved[feature][0])
                    interpolation.append(solved[feature][2])

                self.t[feature], self.U[feature] = self.performInterpolation(ts, interpolation)
            else:
                print "Return from feature %s does not fit the given format (t, U, interpolation)" % feature

        for feature in self.features_1d:
            for solved in solves:
                self.t[feature] = None
                self.U[feature] = solved[feature][1]

        return -1

        solved_features = solves[:, 3]

        # Use union to work on all time values when interpolation.
        # If not use the t maximum amount of t values
        if self.interpolate_union:
            i = 0
            tmp_t = solves[0, 0]
            while i < len(solves) - 1:
                tmp_t = np.union1d(tmp_t, solves[i+1, 0])
                i += 1

            self.t = tmp_t
        else:
            lengths = []
            for s in solves[:, 0]:
                lengths.append(len(s))

            index_max_len = np.argmax(lengths)
            self.t = solves[index_max_len, 0]


        interpolated_solves = []
        for inter in solves[:, 2]:
            interpolated_solves.append(inter(self.t))



        # Calculate PC for each feature
        for feature_name in self.feature_list:
            i = 0
            mask = np.ones(len(solved_features), dtype=bool)
            tmp_results = []

            for feature in solved_features:
                if feature[feature_name] is None:
                    mask[i] = False

                tmp_results.append(feature[feature_name])

                i += 1


            if len(nodes.shape) > 1:
                if self.rosenblatt:
                    tmp_nodes = nodes_MvNormal[:, mask]
                else:
                    tmp_nodes = nodes[:, mask]
            else:
                if self.rosenblatt:
                    tmp_nodes = nodes_MvNormal[mask]
                else:
                    tmp_nodes = nodes[mask]

            if not np.all(mask):
                print "Warning: feature %s does not yield results for all parameter combinations" \
                    % (feature_name)



            tmp_results = np.array(tmp_results)


            # self.U_hat = cp.fit_quadrature(self.P, tmp_nodes, weights, tmp_results[mask])
            self.U_hat[feature_name] = cp.fit_regression(self.P, tmp_nodes,
                                                         tmp_results[mask], rule="T")


        if self.rosenblatt:
            # self.U_hat = cp.fit_quadrature(self.P, nodes_MvNormal, weights, interpolated_solves)
            self.U_hat["direct_comparison"] = cp.fit_regression(self.P, nodes_MvNormal,
                                                                interpolated_solves, rule="T")
        else:
            # self.U_hat = cp.fit_quadrature(self.P, nodes, weights, interpolated_solves)
            self.U_hat["direct_comparison"] = cp.fit_regression(self.P, nodes,
                                                                interpolated_solves, rule="T")



    def performInterpolation(self, ts, interpolation):
        if self.interpolate_union:
            i = 0
            tmp_t = ts[0]
            while i < len(ts) - 1:
                tmp_t = np.union1d(tmp_t, ts[i+1])
                i += 1

            t = tmp_t
        else:
            lengths = []
            for s in ts:
                lengths.append(len(s))

            index_max_len = np.argmax(lengths)
            t = ts[index_max_len]


        interpolated_solves = []
        for inter in interpolation:
            interpolated_solves.append(inter(t))

        return t, interpolated_solves


    def evaluateNodes(self, nodes):
        if self.supress_model_graphics:
            vdisplay = Xvfb()
            vdisplay.start()

        solves = []
        try:
            if self.CPUs > 1:
                pool = mp.Pool(processes=self.CPUs)
                solves = pool.map(evaluateNodeFunction,
                                  self.evaluateNodeFunctionList(self.uncertain_parameters,
                                                                nodes.T))
                pool.close()
            else:
                for node in nodes.T:
                    solves.append(evaluateNodeFunction([self.model.cmd(),
                                                        self.supress_model_output,
                                                        node,
                                                        self.uncertain_parameters,
                                                        self.feature_list,
                                                        self.features.cmd(),
                                                        self.kwargs]))
        except MemoryError:
            return -1

        if self.supress_model_graphics:
            vdisplay.stop()

        return np.array(solves)



    def singleParameterPCAnalysis(self):
        for feature_name in self.feature_list:
            self.E[feature_name] = cp.E(self.U_hat[feature_name], self.distribution)
            self.Var[feature_name] = cp.Var(self.U_hat[feature_name], self.distribution)

            samples = self.distribution.sample(self.nr_pc_mc_samples, "M")
            self.U_mc[feature_name] = self.U_hat[feature_name](samples)

            self.p_05[feature_name] = np.percentile(self.U_mc[feature_name], 5)
            self.p_95[feature_name] = np.percentile(self.U_mc[feature_name], 95)

        # self.p_05["test2D"] = np.percentile(self.U_mc["test2D"], 5, 1)
        self.E["direct_comparison"] = cp.E(self.U_hat["direct_comparison"], self.distribution)
        self.Var["direct_comparison"] = cp.Var(self.U_hat["direct_comparison"], self.distribution)

        samples = self.distribution.sample(self.nr_pc_mc_samples, "M")
        self.U_mc["direct_comparison"] = self.U_hat["direct_comparison"](samples)

        self.p_05["direct_comparison"] = np.percentile(self.U_mc["direct_comparison"], 5, 1)
        self.p_95["direct_comparison"] = np.percentile(self.U_mc["direct_comparison"], 95, 1)



    def PCAnalysis(self):
        if len(self.model.parameters.getUncertain()) == 1:
            self.singleParameterPCAnalysis()
            return

        for feature_name in self.feature_list:
            self.E[feature_name] = cp.E(self.U_hat[feature_name], self.distribution)
            self.Var[feature_name] = cp.Var(self.U_hat[feature_name], self.distribution)

            self.sensitivity[feature_name] = cp.Sens_t(self.U_hat[feature_name], self.distribution)

            samples = self.distribution.sample(self.nr_pc_mc_samples, "M")
            self.U_mc[feature_name] = self.U_hat[feature_name](*samples)

            self.p_05[feature_name] = np.percentile(self.U_mc[feature_name], 5)
            self.p_95[feature_name] = np.percentile(self.U_mc[feature_name], 95)


        self.E["direct_comparison"] = cp.E(self.U_hat["direct_comparison"], self.distribution)
        self.Var["direct_comparison"] = cp.Var(self.U_hat["direct_comparison"], self.distribution)

        self.sensitivity["direct_comparison"] = cp.Sens_t(self.U_hat["direct_comparison"],
                                                          self.distribution)
        # self.sensitivityRanking()

        samples = self.distribution.sample(self.nr_pc_mc_samples, "M")
        self.U_mc["direct_comparison"] = self.U_hat["direct_comparison"](*samples)

        self.p_05["direct_comparison"] = np.percentile(self.U_mc["direct_comparison"], 5, 1)
        self.p_95["direct_comparison"] = np.percentile(self.U_mc["direct_comparison"], 95, 1)




    def MC(self, parameter_name=None):
        if parameter_name is None:
            parameter_space = self.model.parameters.getUncertain("parameter_space")
            self.uncertain_parameters = self.model.parameters.getUncertain()
        else:
            parameter_space = [self.model.parameters.get(parameter_name).parameter_space]
            self.uncertain_parameters = [parameter_name]

        self.distribution = cp.J(*parameter_space)
        nodes = self.distribution.sample(self.nr_mc_samples, "M")



        solves = self.evaluateNodes(nodes)
        solved_features = solves[:, 3]

        # Use union to work on all time values when interpolation.
        # If not use the t maximum amount of t values
        if self.interpolate_union:
            i = 0
            tmp_t = solves[0, 0]
            while i < len(solves) - 1:
                tmp_t = np.union1d(tmp_t, solves[i+1, 0])
                i += 1

            self.t = tmp_t
        else:
            lengths = []
            for s in solves[:, 0]:
                lengths.append(len(s))

            index_max_len = np.argmax(lengths)
            self.t = solves[index_max_len, 0]


        interpolated_solves = []
        for inter in solves[:, 2]:
            interpolated_solves.append(inter(self.t))

        self.U_mc["direct_comparison"] = interpolated_solves

        # Calculate PC for each feature
        self.mask = {}
        for feature_name in self.feature_list:
            i = 0
            self.mask[feature_name] = np.ones(len(solved_features), dtype=bool)
            self.U_mc[feature_name] = np.zeros(len(solved_features))


            for feature in solved_features:
                if feature[feature_name] is None:
                    self.mask[feature_name][i] = False

                self.U_mc[feature_name][i] = feature[feature_name]
                i += 1

            if not np.all(self.mask):
                print "Warning: feature %s does not yield results for all parameter combinations" \
                    % (feature_name)

            tmp_U_masked = self.U_mc[feature_name][self.mask[feature_name]]

            self.E[feature_name] = (np.sum(tmp_U_masked, 0).T/len(tmp_U_masked)).T
            self.Var[feature_name] = \
                (np.sum((tmp_U_masked - self.E[feature_name])**2, 0).T/len(tmp_U_masked)).T
            self.p_05[feature_name] = np.percentile(tmp_U_masked, 5)
            self.p_95[feature_name] = np.percentile(tmp_U_masked, 95)


        self.E["direct_comparison"] = (np.sum(interpolated_solves, 0).T/self.nr_mc_samples).T
        self.Var["direct_comparison"] = \
            (np.sum((interpolated_solves - self.E[feature_name])**2, 0).T/self.nr_mc_samples).T
        self.p_95["direct_comparison"] = np.percentile(interpolated_solves, 95, 0)
        self.p_05["direct_comparison"] = np.percentile(interpolated_solves, 5, 0)



    def timePassed(self):
        return time.time() - self.t_start


    def singleParameters(self):
        for uncertain_parameter in self.model.parameters.getUncertain():
            print "\rRunning for " + uncertain_parameter + "                     "

            self.resetValues()

            if self.createPCExpansion(uncertain_parameter) == -1:
                print "Calculations aborted for " + uncertain_parameter
                return -1


            self.singleParameterPCAnalysis()

            if self.save_data:
                self.save("%s_single-parameter-%s"
                          % (self.output_data_filename, uncertain_parameter))

            if self.save_figures:
                self.plotAll("%s_single-parameter-%s"
                             % (self.output_data_filename, uncertain_parameter))




    def allParameters(self):
        # if len(self.model.parameters.uncertain_parameters) <= 1:
        #     print "Only 1 uncertain parameter"
        #     return

        self.resetValues()

        print "\rRunning for all                     "
        if self.createPCExpansion() == -1:
            print "Calculations aborted for all"
            return -1

        self.PCAnalysis()

        if self.save_data:
            self.save(self.output_data_filename)


        if self.save_figures:
            self.plotAll(self.output_data_filename)


    def singleParametersMC(self):
        for uncertain_parameter in self.model.parameters.getUncertain():
            print "\rRunning for " + uncertain_parameter + "                     "

            self.resetValues()

            self.MC(uncertain_parameter)

            if self.save_data:
                self.save("%s_single-parameter-%s"
                          % (self.output_data_filename, uncertain_parameter))

            if self.save_figures:
                self.plotAll("%s_single-parameter-%s"
                             % (self.output_data_filename, uncertain_parameter))


    def allParametersMC(self):
        # if len(self.model.parameters.uncertain_parameters) <= 1:
        #     print "Only 1 uncertain parameter"
        #     return

        self.resetValues()

        self.MC()

        if self.save_data:
            self.save(self.output_data_filename)


        if self.save_figures:
            self.plotAll(self.output_data_filename)


    def sensitivityRanking(self):
        self.sensitivity_ranking = {}
        i = 0
        for parameter in self.model.parameters.getUncertain("name"):
            self.sensitivity_ranking[parameter] = sum(self.sensitivity["direct_comparison"][i])
            i += 1

        total_sensitivity = 0
        for parameter in self.sensitivity_ranking:
            total_sensitivity += self.sensitivity_ranking[parameter]
        for parameter in self.sensitivity_ranking:
            self.sensitivity_ranking[parameter] /= total_sensitivity


    def save(self, filename):
        if not os.path.isdir(self.output_dir_data):
            os.makedirs(self.output_dir_data)

        ### TODO expand the save funcition to also save parameters and model information

        f = h5py.File(os.path.join(self.output_dir_data, filename), 'w')

        # f.attrs["name"] = self.output_file.split("/")[-1]
        f.attrs["uncertain parameters"] = self.model.parameters.getUncertain("name")
        f.attrs["features"] = self.feature_list

        for feature in self.E:
            group = f.create_group(feature)

            if feature in self.t:
                group.create_dataset("t", data=self.t)
            if feature in self.E:
                group.create_dataset("E", data=self.E[feature])
            if feature in self.Var:
                group.create_dataset("Var", data=self.Var[feature])
            if feature in self.p_05:
                group.create_dataset("p_05", data=self.p_05[feature])
            if feature in self.p_95:
                group.create_dataset("p_95", data=self.p_95[feature])
            if feature in self.sensitivity:
                group.create_dataset("sensitivity", data=self.sensitivity[feature])
            # if feature == "direct_comparison":
            #    group.create_dataset("total sensitivity", data=self.sensitivity_ranking[parameter])

        f.close()



    def plotAll(self, foldername, combined_features=True):
        self.plot.setData(foldername=foldername,
                          t=self.t,
                          E=self.E,
                          Var=self.Var,
                          p_05=self.p_05,
                          p_95=self.p_95,
                          uncertain_parameters=self.uncertain_parameters,
                          sensitivity=self.sensitivity)

        self.plot.plotAllData(combined_features=combined_features)
