import numpy as np
import trimesh
import shapely.geometry as geom

from split_mesh import split_mesh, get_split_face

# Global variables set at Prusa 0.15 mm preset
NOZZLE_SIZE = 0.4  # mm
LAYER_HEIGHT = 0.15  # mm


def add_3d_dovetail_interlock(
    mesh_left,
    mesh_right,
    taper_angle_z_deg=10,
    taper_angle_y_deg=10,
    beam_width_layers=2,
    beam_height_layers=2,
    beam_depth_layers=2,
    avoidance_dist=NOZZLE_SIZE,
    inverted=False
):
    """
    Adds a 3D dovetail-based interlock between two mesh halves.
    Dovetail tapers independently in X and Y directions.

    Args:
        mesh_left: the left half
        mesh_right: the right half
        taper_angle_z_deg: taper angle in Z direction
        taper_angle_y_deg: taper angle in Y direction
        beam_width_layers: width in Y (layer multiples)
        beam_height_layers: height in Z (layer multiples)
        beam_depth_layers: depth in X (layer multiples)
        avoidance_dist: offset from outer walls
        inverted: which side of dovetail is extruding. Default is false

    Returns:
        mesh_left, mesh_right with interlock
    """

    cut_width, cut_height, bounds = get_split_face(mesh_left)

    min_int_y, max_int_y, min_int_z, max_int_z = (bounds[0] + avoidance_dist,
                                                  bounds[1] - avoidance_dist,
                                                  bounds[2] + avoidance_dist,
                                                  bounds[3] - avoidance_dist)
    
    interlock_width = max_int_y - min_int_y
    interlock_height = max_int_z - min_int_z
    # print(f'int height: {interlock_height}')
    # print(f'int width: {interlock_width}')

    num_int_vertical = np.floor(interlock_height / (beam_height_layers*LAYER_HEIGHT))

    # if the num is within the tolerance of a beam, then go ahead and add it
    if np.ceil(num_int_vertical) - num_int_vertical < 0.25:
        num_int_vertical = np.ceil(num_int_vertical)
    else:
        num_int_vertical = np.floor(num_int_vertical)

    int_vertical_height = np.round(num_int_vertical * (beam_height_layers*LAYER_HEIGHT), 3) # round to get rid of division errors
    # print(f'num interlock beams vertical: {num_int_vertical}')
    # print(f'height of interlock pattern {int_vertical_height} mm')
    
    # calculate start and end point of interlock pattern (lowest z to highest z)
    center_height = (bounds[2] + cut_height/2)
    start_height = center_height - (int_vertical_height/2)
    end_height = center_height + (int_vertical_height/2)

    # print(f'middle height cut: {center_height}')
    # print(f'start height: {start_height}')
    # print(f'end height: {end_height}')

    
    # define interlock beams
    dovetail_depth = beam_depth_layers*NOZZLE_SIZE*2    # multiply by 2 since only have of resulting dovetail goes into the other mesh
    dovetail_width = interlock_width/2        # TODO -- NOT SURE SINCE OTHER END IS BIGGER OR (beam_width_layers*NOZZLE_SIZE)
    dovetail_small_height = beam_height_layers*LAYER_HEIGHT



    # plane to add beams to
    plane_x = mesh_left.bounds[1][0] # max left of mesh (where the cut was)


    # create 3D dovetail
    dovetail, dovetail_z_large_height, dovetail_y_large_width = _create_3D_dovetail_with_taper(
        taper_angle_z_deg, taper_angle_y_deg, dovetail_small_height, dovetail_width, dovetail_depth, inverted)
    
    bounds = dovetail.bounds
    dovetail_width_x = bounds[1][0] - bounds[0][0]
    print(f'width: {dovetail_width}, width_x: {dovetail_width_x}')

    target_min_x = plane_x - dovetail_width_x / 2

    # align with cut plane - half of dovetail (x)
    dovetail.apply_translation([
        target_min_x - bounds[0][0],
        0,
        0
    ])

    # center for width (y)
    bounds = dovetail.bounds
    center_y = bounds[:,1].mean()
    target_y = min_int_y + dovetail_width 
    dovetail.apply_translation([0, target_y - center_y, 0])


    # scene = trimesh.Scene([mesh_left, dovetail])
    # scene.show()


    # CALCULATE START HEIGHTS AND UNION/DIFF    

    for i, h in enumerate(np.arange(start_height, end_height, dovetail_z_large_height)):
        dovetail_copy = dovetail.copy()

        if i % 2 == 0:

            dovetail_copy.apply_translation([0, 0, h])    # move to height and back half of dovetail
            # dovetail_copy.apply_translation([0, 0, h])

            # add dovetail to left mesh
            mesh_left = trimesh.boolean.union([mesh_left, dovetail_copy], engine='manifold')
            # subtract dovetail to right mesh
            mesh_right = trimesh.boolean.difference([mesh_right, dovetail_copy], engine='manifold')

        else:
            dovetail_copy.apply_translation([0, 0, h])    # move to height and back half of dovetail

            # rotate dovetail 180 degrees
            dovetail_copy.apply_transform(
                trimesh.transformations.rotation_matrix(
                    -np.pi,
                    [0, 0, 1],
                    dovetail_copy.centroid
                )
            )
            
            # subtract dovetail to left mesh
            mesh_left = trimesh.boolean.difference([mesh_left, dovetail_copy], engine='manifold')
            # add dovetail to right mesh
            mesh_right = trimesh.boolean.union([mesh_right, dovetail_copy], engine='manifold')

    

    # repair
    mesh_left.fill_holes()
    mesh_left.fix_normals()
    mesh_right.fill_holes()
    mesh_right.fix_normals()

    return mesh_left, mesh_right


    



# helper functions
def _create_trapezoidal_pyramid(top_width, top_length, bottom_width, bottom_length, height):
    """
    Creates a trapezoidal pyramid.
    
    Args:
        top_width: small face width
        top_length: small face legth
        bottom_width: large face width
        bottom_length: large face length
        height: how tall the pyrimad is

    Returns:
        Returns trapezoidal pyrimad as a mesh
    """

    vertices = [
        [-bottom_width/2, -bottom_length/2, 0], [bottom_width/2, -bottom_length/2, 0],
        [bottom_width/2, bottom_length/2, 0], [-bottom_width/2, bottom_length/2, 0],
        [-top_width/2, -top_length/2, height], [top_width/2, -top_length/2, height],
        [top_width/2, top_length/2, height], [-top_width/2, top_length/2, height]
    ]

    # visualize vertices
    # trimesh.points.PointCloud(vertices=vertices)

    # the number correspond the index of the vertice (counter clockwise)
    faces = [
        [0, 1, 5], [0, 5, 4], # Side 1
        [1, 2, 6], [1, 6, 5], # Side 2
        [2, 3, 7], [2, 7, 6], # Side 3
        [3, 0, 4], [3, 4, 7], # Side 4
        [0, 3, 2], [0, 2, 1], # Bottom
        [4, 5, 6], [4, 6, 7]  # Top
    ]

    return trimesh.Trimesh(vertices=vertices, faces=faces)



# MAYBE CALCULATE USING Y_LARGE_WIDTH?
def _create_3D_dovetail_with_taper(taper_angle_z_deg, taper_angle_y_deg, z_small_height, y_small_width, depth, inverted=False):
    """
    Create a dovetail for a given taper angle
    
    Args:
        width: width of bases
        small_height: height of the small connection. Should be at least 2 nozzle width
        taper_angle_deg: angle of table based on bottom angle. In degrees
        depth: depth of dovetail extrude
        inverted: which side of dovetail is extruding. Default is false
    """
    z_angle = np.radians(taper_angle_z_deg)
    z_delta = z_small_height * np.tan(z_angle)  # difference between heights

    y_angle = np.radians(taper_angle_y_deg)
    y_delta = z_small_height * np.tan(y_angle)  # difference between heights

    z_large_height = z_small_height + 2 * z_delta
    y_large_width = y_small_width + 2 * y_delta
    
    # round to nearest layer height
    factor = round(z_large_height / LAYER_HEIGHT)
    z_large_height = round(factor * LAYER_HEIGHT, 2)  # round to 2 decimals since layer height is 0.15

    factor = round(y_large_width / LAYER_HEIGHT)
    y_large_width = round(factor * LAYER_HEIGHT, 2)


    dovetail = _create_trapezoidal_pyramid(z_small_height, y_small_width, z_large_height, y_large_width, depth) 
    
    if inverted:
        # rotate small height face to align with cut plane 
        # large end sticking out
        dovetail.apply_transform(
            trimesh.transformations.rotation_matrix(
                -np.pi / 2,
                [0, 1, 0]
            )
        )
    else:
        # rotate large height face to align with cut plane 
        # small end sticking out
        dovetail.apply_transform(
            trimesh.transformations.rotation_matrix(
                np.pi / 2,
                [0, 1, 0]
            )
        )
    
    return dovetail, z_large_height, y_large_width
    

