__author__ = 'sam.royston'
import numpy as np
import math
from progressbar import ProgressBar

def equirectangular_approx(ll1, ll2):
    """
    faster than haversine, ok for short distances
    """
    ll1 = [l * math.pi/ 180 for l in ll1]
    ll2 = [l * math.pi/ 180 for l in ll2]
    earth_radius = 6371 * 1000 # in meters
    x = (ll2[0] - ll1[0]) * math.cos( 0.5*(ll1[1] + ll2[1]) )
    y = ll2[1] - ll1[1]
    return earth_radius * math.sqrt((x*x) + (y*y))

def avg_loc(cluster):
    c = np.array(cluster)
    return np.average(c, axis=0)

def test_array_lens(plaster_obj):
    num_traces = len(plaster_obj.traces)
    num_times = len(plaster_obj.times)
    num_labels = len(plaster_obj.labels)
    num_place_locs = sum(len(x) for x in plaster_obj.sig_places)
    num_sig_places = len(plaster_obj.sig_places)
    num_centroids = len(plaster_obj.centroids)
    assert num_traces == num_times
    assert num_times == num_labels
    assert num_sig_places == num_centroids
    print "Array length tests passed with {0} labels/traces, and {1} clusters".format(num_labels,num_sig_places)

def test_geodesic(geo = equirectangular_approx):
    ll1 = [ 23.4 , 50.0 ]
    ll2 = [ 23.0 , 50.1 ]
    print "dist: " + str(geo(ll1,ll2))
    assert math.fabs(geo(ll1,ll2) - 31000) < 1000


class PlasterError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class Plaster(object):
    def __init__(self, d = 50, t = 600, cd = 100):
        self.sig_places = []
        self.traces = []
        self.times = []
        self.labels = []
        self.d_thresh = d # in meters
        self.t_thresh = t # in seconds
        self.cd_thresh = cd # in meters
        self.size_thresh = 5
        self.current_start = None
        self.centroids = []
        self.current_cluster = None
        self.pending_location = None
        self.d_metric = lambda ll,cluster: equirectangular_approx(ll, avg_loc(cluster))

    def start_temp_cluster(self,trace,t):
        if self.current_cluster is not None:
            self.current_cluster.append(trace)
        else:
            self.current_cluster = [trace]
        self.pending_location = None
        self.current_start = t

    def subsume_cluster(self, cluster):
        """
        Add a set of new locations (current cluster) to the list of significant places, while checking for overlap
        with existing places
        """
        min_ind = len(self.sig_places)
        min_d = 999999999999999
        for i,place in enumerate(self.sig_places):
            cd = equirectangular_approx(avg_loc(cluster),avg_loc(place))
            if cd < min_d:
                min_d, min_ind = cd, i
        if min_d < self.cd_thresh:
            self.sig_places[min_ind].extend(cluster)
            self.centroids[min_ind] = avg_loc(self.sig_places[min_ind])
        else:
            self.sig_places.append(cluster)
            self.centroids.append(avg_loc(cluster))
        return min_ind

    def cluster_point(self, trace, t):
        """
        Add new lat, lng, pair to clustering model.
        Points must be added in chronological order
        """
        if len(self.times) > 0:
            if t < self.times[-1]:
                raise PlasterError("Data point {0}, at t = {1} not in Chronological Order".format(trace, t))
            if t == self.times[-1] and trace == self.traces[-1]:
                raise PlasterError("Duplicate data point {0}, t = {1}".format(trace, t))
        self.times.append(t)
        self.traces.append(trace)
        self.labels.append(-1)
        if self.current_cluster is None or self.d_metric(trace,self.current_cluster) < self.d_thresh:
            self.start_temp_cluster(trace,t)
        elif self.pending_location is not None:
            if t - self.current_start > self.t_thresh:
                label = self.subsume_cluster(self.current_cluster)
                self.labels[-1*len(self.current_cluster):] = [label] * len(self.current_cluster)

            self.current_cluster = [self.pending_location] # clear current cluster

            if self.d_metric(trace,self.current_cluster) < self.d_thresh:
                self.start_temp_cluster(trace,t)
            else:
                self.pending_location = trace
        else:

            self.pending_location = trace

    def fit(self, X):
        """
        methods to conform to scikit learn format, batch learning
        """
        ts = X[:,2]
        traces = X[:,:2]
        prog = ProgressBar(maxval=len(ts))
        prog.start()
        i = 0
        for trace, t in zip(traces.tolist(),ts.tolist()):
            self.cluster_point(trace,t)
            prog.update(i)
            i += 1

        # for label in self.labels:
        #     if len(self.sig_places[label]) < self.size_thresh:
        #         label = -1


    def fit_predict(self, X):
        """
        we use all data, this is an unsupervised technique
        """
        self.fit(X)
        print "labels len: {0}".format(len(self.labels))
        print set(self.labels)

        return np.array(self.labels)



