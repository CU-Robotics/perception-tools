import bpy
import math
import numpy as np
import json
import argparse
from mathutils import Matrix, Vector, Quaternion

"""
opencv/mrcal (right-handed system):
    X right
    Y down
    Z forward  
blender (right-handed system):
    X right
    Y up
    Z backward
"""
CV_TO_BLENDER = Matrix((
    (+1, 0, 0, 0),
    (0, -1, 0, 0), # flip Y
    (0, 0, -1, 0), # flip Z
    (0, 0, 0, +1),
))

def set_camera_pose(camera, object_frame, R, t):
    T_cam_obj = np.eye(4)
    T_cam_obj[:3, :3] = R
    T_cam_obj[:3, 3] = t
    T_cam_obj = Matrix(T_cam_obj.tolist())
    
    camera.matrix_world = object_frame.matrix_world @ T_cam_obj.inverted() @ CV_TO_BLENDER

def set_camera_properties(scene, camera, width, height, focal_len):
    scene.camera = camera
    
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1
    scene.render.pixel_aspect_y = 1
    
    camera.data.type = "PERSP"
    camera.data.sensor_fit = "HORIZONTAL"
    camera.data.shift_x = 0
    camera.data.shift_y = 0
    camera.data.lens = focal_len * camera.data.sensor_width / width

def main():
    # get all objects
    scene = bpy.context.scene
    camera = bpy.data.objects["robot_camera"]
    object_frame = bpy.data.objects["object_frame"]
    
    width = 1920
    height = 1200
    focal_len = 1050
    
    set_camera_properties(scene, camera, width, height, focal_len)
    set_camera_pose(camera, object_frame, R=np.diag((1, -1, -1)), t=np.array([0, 0, 0.5]))
    
    scene.render.filepath = "/tmp/render.png"
    scene.render.image_settings.file_format = "PNG"
    
    bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    main()