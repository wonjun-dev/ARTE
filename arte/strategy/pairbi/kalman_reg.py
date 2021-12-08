import numpy as np

from pykalman import KalmanFilter

class KalmanReg:

    def __init__(self, maxlen):
        self.kf = None
        self.his_state_means = np.zeros((1,2))
        self.his_state_covs = np.zeros((1,2,2))
        self.maxlen = maxlen

        self.delta = 1e-3
        self.trans_cov = self.delta / (1 - self.delta) * np.eye(2)

    def initialize(self, x, y):

        obs_mat = [x, 1]

        self.kf = KalmanFilter(n_dim_obs=1, n_dim_state=2, # y is 1-dimensional, (alpha, beta) is 2-dimensional
                      initial_state_mean=[0,0],
                      initial_state_covariance=np.ones((2, 2)),
                      transition_matrices=np.eye(2),
                      observation_matrices=obs_mat,
                      observation_covariance=2,
                      transition_covariance=self.trans_cov)

        self.his_state_means[0], self.his_state_covs[0] = self.kf.filter(y)

    def update(self, x,y):
        obs_mat = np.asarray([[x, 1]])

        a, b = self.kf.filter_update( self.his_state_means[-1], self.his_state_covs[-1], observation=y, observation_matrix= obs_mat )
        self.his_state_means = np.concatenate( (self.his_state_means, np.array([a])))
        self.his_state_covs = np.concatenate( (self.his_state_covs, np.array([b])))

        if len(self.his_state_means) > self.maxlen:
            self.his_state_means = self.his_state_means[-self.maxlen:]
            self.his_state_covs = self.his_state_covs[-self.maxlen:]