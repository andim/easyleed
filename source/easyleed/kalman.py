"""
easyleed.kalman
----------------

Kalman filters for tracking the spots

"""

import numpy as np

class AbstractKalmanFilter(object):
    """ Abstract implementation of a Kalman filter.
    
    Matrices and Vectors can be given in any input format np.matrix() understands.
    Vectors are internally transposed and should therefore be given as column vectors.
    """

    def __init__(self, x, P, H):
        """ Initialize Kalman filter.

        x: start state vector
        P: start state covariance matrix
        H: measurement matrix
        """
        
        super(AbstractKalmanFilter, self).__init__()
        self.x = np.asmatrix(x).T
        self.P = np.asmatrix(P)
        self.H = np.asmatrix(H)
        # identity matrix of state vector size
        self._1 = np.asmatrix(np.identity(max(self.x.shape)))

    def predict(self, F, Q=np.zeros((4, 4))):
        """ Predict next state.

        F: state transition matrix
        Q: process covariance matrix
        """
        
        F = np.asmatrix(F)
        Q = np.asmatrix(Q)
        self.x = F * self.x
        self.P = F * self.P * F.T  + Q

    def predict_measurement_covariance(self, R=None):
        """ Returns the covariance matrix of a predicted measurement. """
        if not R is None:
            return self.H * self.P * self.H.T + R
        else:
            return self.H * self.P * self.H.T

    def predict_measurement(self):
        """ Returns the predicted measurement. """
        return self.H * self.x

    def update(self, z, R):
        """ Update state estimate.

        z: measurement vector
        R: measurement covariance matrix
        """
        z = np.asmatrix(z).T
        R = np.asmatrix(R)
        K = self.P * self.H.T * self.predict_measurement_covariance(R).I
#        print np.sum((np.asarray(z).flatten() - np.asarray(self.predict_measurement()).flatten())**2), \
#            np.sum(np.diag(self.predict_measurement_covariance(R)))
        self.x = self.x  +  K * (z - self.predict_measurement())
        self.P = (self._1 - K * self.H) * self.P

    def measurement_distance(self, z, R=None):
        """ Returns the squared Mahalanobis distance of the given measurement.
        
        z: measurement vector
        """
        z = np.asmatrix(z).T
        R = np.diag([0, 0]) if R is None else np.asarray(R)
        z_predicted = self.predict_measurement()
        # calculate the measurement residual
        residual =  z - z_predicted
        return residual.T * self.predict_measurement_covariance(R).I * residual

class AbstractPVKalmanFilter(AbstractKalmanFilter):
    """ Kalman filter for 2d-tracking using position and velocity as state variables."""
    def __init__(self, x_in, y_in, P, time, vx_in=0, vy_in=0):
        self.old_time = time
        x = [x_in, y_in, vx_in, vy_in]
        H = [[1, 0, 0, 0], [0, 1, 0, 0]]
        super(AbstractPVKalmanFilter, self).__init__(x, P, H)

    def get_position(self):
        return float(self.x[0]), float(self.x[1])

    def get_position_err(self):
        return float(self.P[0, 0])**0.5, float(self.P[1, 1])**0.5

class PVKalmanFilter0(AbstractPVKalmanFilter):
    def predict(self, time, *args, **kwargs):
        dt = time - self.old_time
        F = [[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]]
        super(PVKalmanFilter0, self).predict(F, *args, **kwargs)
        self.old_time = time

class PVKalmanFilter1(AbstractPVKalmanFilter):
    def predict(self, time, *args, **kwargs):
        dt = time - self.old_time
        a = - 1.5 / self.old_time
        v_up = 1 + a * dt
        pos_up = dt + 0.5 * a * dt**2
        F = [[1, 0, pos_up, 0], [0, 1, 0, pos_up], [0, 0, v_up, 0], [0, 0, 0, v_up]]
        super(PVKalmanFilter1, self).predict(F, *args, **kwargs)
        self.old_time = time

class PVKalmanFilter2(AbstractPVKalmanFilter):
    def predict(self, time, *args, **kwargs):
        dt = time - self.old_time
        a = - 1.5 / self.old_time
        a_dot = 1.875 / self.old_time**2
        v_up = 1 + a * dt + a_dot * dt**2
        pos_up = dt + 0.5 * a * dt**2 + (1.0 / 3.0) * a_dot * dt**3
        F = [[1, 0, pos_up, 0], [0, 1, 0, pos_up], [0, 0, v_up, 0], [0, 0, 0, v_up]]
        super(PVKalmanFilter2, self).predict(F, *args, **kwargs)
        self.old_time = time

class PVKalmanFilter3(AbstractPVKalmanFilter):
    def predict(self, time, *args, **kwargs):
        dt = time - self.old_time
        a = - 1.5 / self.old_time
        a_dot = 1.875 / self.old_time**2
        a_ddot = - 2.1875 / self.old_time**3
        v_up = 1 + a * dt + a_dot * dt**2 + a_ddot * dt**3
        pos_up = dt + 0.5 * a * dt**2 + (1.0 / 3.0) * a_dot * dt**3 + (1.0 / 4.0) * a_ddot * dt**4
        F = [[1, 0, pos_up, 0], [0, 1, 0, pos_up], [0, 0, v_up, 0], [0, 0, 0, v_up]]
        super(PVKalmanFilter3, self).predict(F, *args, **kwargs)
        self.old_time = time
