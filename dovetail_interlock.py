import numpy as np
import trimesh
import shapely.geometry as geom

from split_mesh import split_mesh, get_split_face

# Global variables set at Prusa 0.15 mm preset
NOZZLE_SIZE = 0.4 # mm
LAYER_HEIGHT = 0.15 # mm


def add_dovetail_interlock_in_z(mesh_left, mesh_right, taper_angle_deg=10, beam_width_layers=2, beam_height_layers=2, beam_depth_layers=2, avoidance_dist=NOZZLE_SIZE):
    """
    Adds a dovetail-based interlock between two mesh halves. Centered along seam.
    
    Args:
        mesh_left: The mesh to have interlock union
        mesh_right: The mesh to have interlock difference
        taper_andgle_deg: Angle of taper in degrees. Default is 10
        beam_width_layers: How many layers wide the interlock is. Defaults to 2
        beam_height_layers: How many layers tall the interlock is. Default is 2
        beam_depth_layers: How many layer interlock goes into other mesh. Default is 2
        avoidance_dist: How far interlock is from outer surfaces. Default is the nozzle size

    Returns:
        Two mesh objects with dovetail interlock
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
    dovetail_depth = beam_depth_layers*NOZZLE_SIZE*2
    dovetail_width = interlock_width        # TODO -- OR (beam_width_layers*NOZZLE_SIZE)
    dovetail_small_height = beam_height_layers*LAYER_HEIGHT



    # plane to add beams to
    plane_x = mesh_left.bounds[1][0] # max left of mesh (where the cut was)

    # width is in y
    # height is in z
    # depth is in x

    # dovetail = _create_dovetail(bottom_w, top_w, height, beam_d)
    dovetail, dovetail_large_height = _create_dovetail_from_taper(dovetail_width, dovetail_small_height, taper_angle_deg, dovetail_depth)
    # need to know large height since total height of two dovetails is small_height + large_height
    print('small trap height: ', dovetail_small_height)
    print('large trap height: ', dovetail_large_height)

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
    target_y = min_int_y + dovetail_width / 2
    dovetail.apply_translation([0, target_y - center_y, 0])

    # hold the beam starting heights to be added/subtracted
    # pattern_start_heights = []

    # # calculate start heights using alternating large and small side heights
    # h = start_height
    # i = 1
    # while h < end_height:
    #     if i % 2 == 0:
    #         pattern_start_heights.append(h)
    #         h += dovetail_small_height

    #     else:
    #         # start with large height
    #         pattern_start_heights.append(h)
    #         h += dovetail_large_height
        
    #     i += 1


    # calculate start heights using alternating large and small side heights
    # TODO -------- MESS WITH THIS TO SEE IF GET RID OF GAP)???
    # h = start_height
    # i = 1
    # while h < end_height:
    #     if i % 2 == 0:
    #         pattern_start_heights.append(h)
    #         h += dovetail_large_height

    #     else:
    #         # start with large height
    #         pattern_start_heights.append(h)
    #         h += dovetail_large_height
        
    #     i += 1

    # add/subtract dovetails from meshes
    # for i, h in enumerate(pattern_start_heights):
    for i, h in enumerate(np.arange(start_height, end_height, dovetail_large_height)):
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


    # # add/subtract dovetails from meshes
    # for i, h in enumerate(pattern_start_heights):
    #     dovetail_copy = dovetail.copy()
        
    #     # alternate union and diff + translate
    #     if i % 2 == 0:
    #         dovetail_copy.apply_translation([0, 0, h])
    #          # add dovetail to left mesh
    #         mesh_left = trimesh.boolean.union([mesh_left, dovetail_copy], engine='manifold')
    #         # subtract dovetail to right mesh
    #         mesh_right = trimesh.boolean.difference([mesh_right, dovetail_copy], engine='manifold')
    #     else:
    #         dovetail_copy.apply_translation([0, 0, h])
    #         # subtract dovetail to left mesh
    #         mesh_left = trimesh.boolean.difference([mesh_left, dovetail_copy], engine='manifold')
    #         # add dovetail to right mesh
    #         mesh_right = trimesh.boolean.union([mesh_right, dovetail_copy], engine='manifold')

    # repair
    mesh_left.fill_holes()
    mesh_left.fix_normals()
    mesh_right.fill_holes()
    mesh_right.fix_normals()

    return mesh_left, mesh_right






# helper functions
def _create_trapezoid(bottom_w, top_w, height):

    vertices = [
        (-bottom_w/2, 0),
        (bottom_w/2, 0),
        (top_w/2, height),
        (-top_w/2, height)
    ]

    return geom.Polygon(vertices)


def _create_dovetail_from_taper(width, small_height, taper_angle_deg, depth):
    """
    Docstring for _create_dovetail_from_taper
    
    Args:
        width: width of bases
        small_height: height of the small connection. Should be at least 2 nozzle width
        taper_angle_degrees: angle of table based on bottom angle. In degrees
        depth: depth of dovetail extrude
    """

    angle = np.radians(taper_angle_deg)

    delta = small_height * np.tan(angle)  # difference between heights

    large_height = small_height + 2 * delta
    # round to nearest layer height
    factor = round(large_height / LAYER_HEIGHT)
    large_height = round(factor * LAYER_HEIGHT, 2)  # round to 2 decimals since layer height is 0.15

    trapezoid = _create_trapezoid(small_height, large_height, depth)
    dovetail = trimesh.creation.extrude_polygon(trapezoid, height=width)

    # rotate small height face to a side (pos angle faces right mesh, neg angle faces left mesh)
    dovetail.apply_transform(
        trimesh.transformations.rotation_matrix(
            np.pi / 2,
            [0, 0, 1]
        )
    )

    # rotate so dovetails are horizontal
    dovetail.apply_transform(
        trimesh.transformations.rotation_matrix(
            np.pi / 2,
            [1, 0, 0]
        )
    )

    return dovetail, large_height

