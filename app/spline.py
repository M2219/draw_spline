from datetime import datetime
from pathlib import Path
import json
import math
import numpy as np
from scipy import interpolate
import cv2 
import config
import os

class SplineManager:
    def __init__(self, spline_dir: str, landmark_name: str):
        self.spline_dir = Path(spline_dir)
        self.spline_dir.mkdir(exist_ok=True, parents=True)

        self.landmark_filename = landmark_name 
        self.num_spline_written = 0
        self.num_points = 5
        self.k_deg = 2 
        self.smooth = 20

        self._spline_started = datetime.now()

    def spline_exists(self, image: str):
        return self._get_spline_path(image).exists()

    def write_coordinates(self, image: str, x: int, y: int):
        data = {"coordinates": {"x": x, "y": y}, "status": "ok"}
        self._write_spline(image, data)

    def _get_spline_path(self, image_name: str):
        image_add = self.landmark_filename + "_" +os.path.splitext(image_name)[0]
        return self.spline_dir / image_add

    def _write_spline(self, image, data):
        outfile = self._get_spline_path(image)

        # might already exist if user pressed the back button, don't count as new spline in this case
        if not self.spline_exists(image):
            self.num_spline_written += 1

        xc = np.array(data["coordinates"]["x"])
        yc = np.array(data["coordinates"]["y"])
        sort_ind_xc = np.argsort(xc)

        xc_sorted = np.take_along_axis(xc, sort_ind_xc, axis=0)
        yc_sorted = np.take_along_axis(yc, sort_ind_xc, axis=0)
        tck = interpolate.splrep(xc_sorted, yc_sorted, s=self.smooth, k=self.k_deg)

        xnew = np.linspace(xc_sorted.min(), xc_sorted.max())
        ynew = interpolate.splev(xnew, tck, der=0)
        pts = np.stack((xnew, ynew), axis=-1)
        im = cv2.imread(str(config.IMAGE_DIR +  "/" + image))
        
        for point1, point2 in zip(pts, pts[1:]): 
            cv2.line(im, np.int32(point1), np.int32(point2), [0, 255, 0], 2) 

        #cv2.polylines(im, np.int32([pts]), True, (0,255,255))        
        cv2.imwrite(str(outfile) + ".jpg", im)

        with open(str(outfile) + ".json", 'w') as f:
            json.dump(data, f)
