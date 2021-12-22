import numpy as np

from pykalman import KalmanFilter

class KalmanAvg:

    def __init__(self, maxlen):
        self.kf = None
        self.his_state_means = np.zeros((1, 1))
        self.his_state_covs = np.zeros((1,1,1))
        self.maxlen = maxlen

    def initialize(self, x):
        self.kf = KalmanFilter(transition_matrices = [1],
                      observation_matrices = [1],
                      initial_state_mean = 0,
                      initial_state_covariance = 1,
                      observation_covariance=1,
                      transition_covariance=.01)
        self.his_state_means[0], self.his_state_covs[0] = self.kf.filter(x)

    def update(self, x):
        a, b = self.kf.filter_update(self.his_state_means[-1], self.his_state_covs[-1], observation=x)
        self.his_state_means = np.concatenate( (self.his_state_means, np.array([a])))
        self.his_state_covs = np.concatenate( (self.his_state_covs, np.array([b])))

        if len(self.his_state_means) > self.maxlen:
            self.his_state_means = self.his_state_means[-self.maxlen:]
            self.his_state_covs = self.his_state_covs[-self.maxlen:]