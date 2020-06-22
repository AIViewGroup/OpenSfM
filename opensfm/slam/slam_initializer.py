import numpy as np
from opensfm import pyslam
from opensfm import reconstruction
from opensfm import pysfm
import logging
logger = logging.getLogger(__name__)


class SlamInitializer(object):

    def __init__(self, data, camera, matcher, reconstruction):
        self.init_shot = None
        self.prev_pts = None
        self.data = data
        self.camera = camera
        self.matcher = matcher
        self.system_initialized = False
        self.map = reconstruction

    def initialize(self, curr_shot):
        if self.init_shot is None:
            self.init_shot = curr_shot
            self.prev_pts =\
                pyslam.SlamUtilities.undist_keypts_from_shot(curr_shot)[:, 0:2]
            return False, None
        else:
            return self.initialize_openvslam(curr_shot)

    def initialize_openvslam(self, curr_shot):
        """Initialize similar to ORB-SLAM and Openvslam"""
        # We should have two frames: the current one and the init frame
        # TODO: think about prev_matches!
        matches = self.matcher.match_shot_to_shot(self.init_shot, curr_shot, self.prev_pts, 100)
        matches = np.array(matches)
        print("matches: ", curr_shot.id, len(matches), matches.shape)
        print("self.init_shot", self.init_shot.id, len(self.init_shot.get_keypoints()))
        print("curr_shot", curr_shot.id, len(curr_shot.get_keypoints()))
        if len(matches) < 100:
            return False, None

        # Update pts
        self.prev_pts[matches[0, :], :] =\
            pyslam.SlamUtilities.undist_keypts_from_shot(curr_shot)[matches[1, :], 0:2]

        f1_points = pyslam.SlamUtilities.keypts_from_shot(self.init_shot)
        f2_points = pyslam.SlamUtilities.keypts_from_shot(curr_shot)

        # test reconstructability
        threshold = 4 * self.data.config['five_point_algo_threshold']
        args = []
        im1 = self.init_shot.id
        im2 = curr_shot.id
        norm_p1 = f1_points[matches[:, 0], 0:2]
        norm_p2 = f2_points[matches[:, 1], 0:2]
        args.append((im1, im2, norm_p1, norm_p2,
                     self.camera, self.camera, threshold))
        i1, i2, r = reconstruction._compute_pair_reconstructability(args[0])
        if r == 0:
            return False, None

        # create the graph with the new tracks manager
        tracks_graph = pysfm.TracksManager()
        for (track_id, (f1_id, f2_id)) in enumerate(matches):
            tracks_graph.add_observation(
                im1, str(track_id), self.init_shot.get_observation(f1_id))
            tracks_graph.add_observation(
                im2, str(track_id), curr_shot.get_observation(f2_id))

        rec_report = {}
        rec_init, rec_report['bootstrap'] = \
            reconstruction.bootstrap_reconstruction(self.data, tracks_graph, self.data.load_camera_models(),
                                                    im1, im2, norm_p1, norm_p2)
        success = reconstruction is not None
        if success:
            logger.info("Created init rec from {}<->{} with {} points from {} matches"
                        .format(im1, im2, len(rec_init.points), len(matches)))
        return success, rec_init
