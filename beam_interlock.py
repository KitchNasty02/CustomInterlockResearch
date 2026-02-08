import numpy as np
import trimesh

from split_mesh import get_split_face

# Global variables set at Prusa 0.15 mm preset
NOZZLE_SIZE = 0.4 # mm
LAYER_HEIGHT = 0.15 # mm


def add_beam_interlock_in_z(mesh_left, mesh_right, beam_width_layers=2, beam_height_layers=2, beam_depth_layers=2, avoidance_dist=NOZZLE_SIZE):
    """
    Adds a beam-based interlock between two mesh halves
    
    Args:
        mesh_left: The mesh to have interlock union
        mesh_right: The mesh to have interlock difference
        centroid: Centroid of original mesh
        beam_width_layers: How many layers wide the interlock is. Defaults to 2
        beam_height_layers: How many layers tall the interlock is. Default is 2
        beam_depth_layers: How many layer interlock goes into other mesh. Default is 2
        avoidance_dist: How far interlock is from outer surfaces. Default is the nozzle size

    Returns:
        Two mesh objects with interlock
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
    beam_d = beam_depth_layers*NOZZLE_SIZE
    beam_w = interlock_width        # TODO -- OR (beam_width_layers*NOZZLE_SIZE)
    beam_h = beam_height_layers*LAYER_HEIGHT
    beam_size = [beam_d, beam_w, beam_h] # in mm 

    # hold the beam starting heights to be added/subtracted
    pattern_start_heights = []

    # populate start heights
    h = start_height
    while h < end_height:
        pattern_start_heights.append(h)
        h += beam_h

    # plane to add beams to
    plane_x = mesh_left.bounds[1][0] # max left of mesh (where the cut was)

    # add/subtract beams from meshes
    for i, h in enumerate(pattern_start_heights):
        beam = trimesh.creation.box(extents=beam_size)
        
        # alternate union and diff + translate
        if i % 2 == 0:
            beam.apply_translation([plane_x + beam_d/2, min_int_y + beam_w/2, h])
             # add beam to left mesh
            mesh_left = trimesh.boolean.union([mesh_left, beam], engine='manifold')
            # subtract beam to right mesh
            mesh_right = trimesh.boolean.difference([mesh_right, beam], engine='manifold')
        else:
            beam.apply_translation([plane_x - beam_d/2, min_int_y + beam_w/2, h])
            # subtract beam to left mesh
            mesh_left = trimesh.boolean.difference([mesh_left, beam], engine='manifold')
            # add beam to right mesh
            mesh_right = trimesh.boolean.union([mesh_right, beam], engine='manifold')

    # repair
    mesh_left.fill_holes()
    mesh_left.fix_normals()
    mesh_right.fill_holes()
    mesh_right.fix_normals()

    return mesh_left, mesh_right




def add_beam_interlock_in_y(mesh_left, mesh_right, beam_width_layers=2, beam_height_layers=2, beam_depth_layers=2, avoidance_dist=NOZZLE_SIZE):
    """
    Adds a beam-based interlock between two mesh halves
    
    Args:
        mesh_left: The mesh to have interlock union
        mesh_right: The mesh to have interlock difference
        centroid: Centroid of original mesh
        beam_width_layers: How many layers wide the interlock is. Defaults to 2
        beam_height_layers: How many layers tall the interlock is. Default is 2
        beam_depth_layers: How many layer interlock goes into other mesh. Default is 2
        avoidance_dist: How far interlock is from outer surfaces. Default is the nozzle size

    Returns:
        Two mesh objects with interlock
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

    num_int_horiz = interlock_width / (beam_width_layers*LAYER_HEIGHT)
    
    # if the num is within the tolerance of a beam, then go ahead and add it
    if np.ceil(num_int_horiz) - num_int_horiz < 0.25:
        num_int_horiz = np.ceil(num_int_horiz)
    else:
        num_int_horiz = np.floor(num_int_horiz)

    # num_int_horiz = np.floor(interlock_width / (beam_width_layers*LAYER_HEIGHT))
    int_horiz_width = np.round(num_int_horiz * (beam_width_layers*LAYER_HEIGHT), 3) # round to get rid of division errors
    # print(f'num interlock beams horiz: {num_int_horiz}')
    # print(f'width of interlock pattern {int_horiz_width} mm')
    
    # calculate start and end point of interlock pattern (lowest z to highest z)
    center_width = (bounds[0] + cut_width/2)
    start_width = center_width - (int_horiz_width/2)
    end_width = center_width + (int_horiz_width/2)

    # print(f'center_width: {center_width}')
    # print(f'start_width: {start_width}')
    # print(f'end_width: {end_width}')
    
    # define interlock beams
    beam_d = beam_depth_layers*NOZZLE_SIZE
    beam_w = beam_width_layers*LAYER_HEIGHT 
    beam_h = interlock_height
    beam_size = [beam_d, beam_w, beam_h] # in mm 

    # hold the beam starting heights to be added/subtracted
    pattern_start_widths = []

    # populate start heights
    w = start_width
    while w < end_width:
        pattern_start_widths.append(w)
        w += beam_w

    # plane to add beams to
    plane_x = mesh_left.bounds[1][0] # max left of mesh (where the cut was)

    # add/subtract beams from meshes
    for i, w in enumerate(pattern_start_widths):
        beam = trimesh.creation.box(extents=beam_size)
        
        # alternate union and diff + translate
        if i % 2 == 0:
            beam.apply_translation([plane_x + beam_d/2, w, min_int_z + beam_h/2])
             # add beam to left mesh
            mesh_left = trimesh.boolean.union([mesh_left, beam], engine='manifold')
            # subtract beam to right mesh
            mesh_right = trimesh.boolean.difference([mesh_right, beam], engine='manifold')
        else:
            beam.apply_translation([plane_x - beam_d/2, w, min_int_z + beam_h/2])
            # subtract beam to left mesh
            mesh_left = trimesh.boolean.difference([mesh_left, beam], engine='manifold')
            # add beam to right mesh
            mesh_right = trimesh.boolean.union([mesh_right, beam], engine='manifold')

    # repair
    mesh_left.fill_holes()
    mesh_left.fix_normals()
    mesh_right.fill_holes()
    mesh_right.fix_normals()

    return mesh_left, mesh_right

