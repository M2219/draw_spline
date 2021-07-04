from flask import Flask, render_template, send_from_directory, request, redirect, url_for

from app.spline import SplineManager
from app.images import ImageManager
from app.coordinates import parse_coordinates, init_scale_coordinates
import config
import cv2
import os

app = Flask(__name__)

splines = SplineManager(config.IMAGE_DIR, config.SPNAME)
images = ImageManager(config.IMAGE_DIR, splines)

scale_coordinates = init_scale_coordinates(config.IMAGE_DIR, config.IMAGE_HEIGHT)

########################################################################
# sending tasks
########################################################################


def select_next_task(current_image=None):
    if current_image is None:
        next_image = images.get_first_image()
    else:
        next_image = images.get_next_image(current_image)

    if next_image is None:
        return redirect(url_for("finished"))
    else:
        return redirect(url_for("send_task", image=next_image, cnt=0))


@app.route('/')
def send_first_task():
    return select_next_task(current_image=None)


@app.route('/tasks/<image>?<cnt>', methods=['GET', 'POST'])
def send_task(image, cnt):

    if request.method == 'POST':
        splines.k_deg = int(request.form["degree"])
        splines.num_points = int(request.form["n_points"])
        splines.smooth = int(request.form["smoothness"])

    previous_image = images.get_previous_image(image)
    if previous_image is None:
        url_back = url_for("send_task", image=image, cnt=cnt)  # can't go back so sending the same image again - improve?
    else:
        url_back = url_for("send_task", image=previous_image, cnt=cnt)



    return render_template("landmark.html", landmark_name=config.SPNAME,
                           image_name=image, image_height=config.IMAGE_HEIGHT, url_back=url_back,
                           done=images.num_previously_splined + splines.num_spline_written,
                           total=images.num_images, cnt_c=cnt, num_p=splines.num_points, num_k=splines.k_deg,
                           smooth_val=splines.smooth )


@app.route('/finished')
def finished():
    # check on the filesystem again to make sure really everything splined
    # (splines can be missing if user skipped images or deleted spline files)
    spline_now = SplineManager(config.IMAGE_DIR, config.SPNAME)
    images_now = ImageManager(config.IMAGE_DIR, spline_now)

    num_not_splined = images_now.num_images - images_now.num_previously_splined

    sp_path = os.listdir(config.INPUT_DIR)
    im_add = []

    for pth in sp_path:
        im_add.append(config.SPNAME + "_" + pth)

    return render_template("finished.html", image_add=im_add, image_height=config.IMAGE_HEIGHT)


########################################################################
# storing results
########################################################################

@app.route('/results/<image>/coordinates')
def store_result(image, req_col=[], x_coo = [], y_coo = []):
    # somehow there seems to be some margin around the image that is still clickable but does not send any coordinates
    # probably was an error that the user clicked there -> send the same image again


    if len(request.args) == 0:
        return redirect(url_for("send_task", image=image, cnt=len(req_col)))

    if len(request.args) == 1 and len(req_col) != splines.num_points:
        x, y = parse_coordinates(request.args)
        x, y = scale_coordinates(image, x, y)
        im = cv2.imread(str(config.IMAGE_DIR +  "/" + image))
        cv2.circle(im, (x, y), 4, (255, 0, 0), -1)
        cv2.imwrite(str(config.IMAGE_DIR + "/" +  image), im)
        cv2.waitKey(0)
        req_col.append(request.args)
        return redirect(url_for("send_task", image=image, cnt=len(req_col)))


    for req in req_col:
        x, y = parse_coordinates(req)
        x, y = scale_coordinates(image, x, y)
        x_coo.append(x)
        y_coo.append(y)
 
    splines.write_coordinates(image, x_coo, y_coo)
    req_col.clear()
    x_coo.clear()
    y_coo.clear()

    return select_next_task(current_image=image)


########################################################################
# images
########################################################################

# also serve the actual image files here, for simplicity
@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(config.IMAGE_DIR, filename)


