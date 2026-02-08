import numpy as np
import trimesh

# Global variables set at Prusa 0.15 mm preset
NOZZLE_SIZE = 0.4 # mm
LAYER_HEIGHT = 0.15 # mm


def split_mesh(mesh):
    """
    Splits mesh into two halves
    
    Args:
        mesh: The mesh to be split

    Returns:
        Two mesh objects and centroid of original mesh
        
    """
    centroid = mesh.centroid
    extents = mesh.extents

    # define plane to split at
    plane_x = centroid[0]

    # define the size of the input mesh
    x_size = extents[0] * 2  # width in X
    y_size = extents[1] * 2  # cover full Y
    z_size = extents[2] * 2  # cover full Z


    # create box around half of the mesh and translate so the side of the box is on plane_x
    # the box covers all of the input mesh where X >= plane_x (center x of mesh)
    cutter = trimesh.creation.box(extents=[x_size, y_size, z_size])
    cutter.apply_translation([plane_x + x_size/2, centroid[1], centroid[2]])

    mesh_left = trimesh.boolean.difference([mesh, cutter], engine='manifold') # keeps X < plane_x
    mesh_right = trimesh.boolean.intersection([mesh, cutter], engine='manifold') # keeps X >= plane_x

    # repair
    mesh_left.fill_holes()
    mesh_left.fix_normals()
    mesh_right.fill_holes()
    mesh_right.fix_normals()

    # print(f'Is left watertight: {mesh_left.is_watertight}')
    # print(f'Is right watertight: {mesh_right.is_watertight}')

    return mesh_left, mesh_right, centroid



def get_split_face(mesh):
    """
    Calculate bounding box of mesh face
    
    Args:
        mesh: The mesh to find size of face

    Returns:
        Cut width (mm), cut height (mm), bounds
        
    """
    plane_x = mesh.bounds[1][0] # x coord of cut plane

    tolerance = 1e-5

    # find vertices that lie on the cut plane
    on_plane = np.abs(mesh.vertices[:, 0] - plane_x) < tolerance
    cut_vertices = mesh.vertices[on_plane]

    # project to YZ plane
    cut_yz = cut_vertices[:, 1:3]

    # compute bounding box of cut face
    min_y, min_z = cut_yz.min(axis=0)
    max_y, max_z = cut_yz.max(axis=0)

    cut_width = max_y - min_y
    cut_height = max_z - min_z

    print(f'Cutface width (Y): {cut_width:.2f} mm')
    print(f'Cutface height (Z): {cut_height:.2f} mm')

    return cut_width, cut_height, (min_y, max_y, min_z, max_z)




def add_cube_interlock(mesh_left, mesh_right, beam_width_layers=2, beam_height_layers=2, beam_depth_layers=2, avoidance_dist=NOZZLE_SIZE):
    """
    Adds a cube-based interlock between two mesh halves
    
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
    int_vertical_height = np.round(num_int_vertical * (beam_height_layers*LAYER_HEIGHT), 3) # round to get rid of division errors
    print(f'num interlock cubes vertical: {num_int_vertical}')
    print(f'height of interlock pattern {int_vertical_height} mm')
    
    # calculate start and end point of interlock pattern (lowest z to highest z)
    center_height = (bounds[2] + cut_height/2)
    start_height = center_height - (int_vertical_height/2)
    end_height = center_height + (int_vertical_height/2)

    # print(f'middle height cut: {center_height}')
    # print(f'start height: {start_height}')
    # print(f'end height: {end_height}')
    
    # define interlock cubes
    cube_d = beam_depth_layers*NOZZLE_SIZE
    cube_w = interlock_width        # TODO -- OR (beam_width_layers*NOZZLE_SIZE)
    cube_h = beam_height_layers*LAYER_HEIGHT
    cube_size = [cube_d, cube_w, cube_h] # in mm 

    # hold the cube starting heights to be added/subtracted
    pattern_start_heights = []

    # populate start heights
    h = start_height
    while h < end_height:
        pattern_start_heights.append(h)
        h += cube_h

    # plane to add cubes to
    plane_x = mesh_left.bounds[1][0] # max left of mesh (where the cut was)

    # add/subtract cubes from meshes
    for i, h in enumerate(pattern_start_heights):
        cube = trimesh.creation.box(extents=cube_size)
        
        # alternate union and diff + translate
        if i % 2 == 0:
            cube.apply_translation([plane_x + cube_d/2, min_int_y + cube_w/2, h])
             # add cube to left mesh
            mesh_left = trimesh.boolean.union([mesh_left, cube], engine='manifold')
            # subtract cube to right mesh
            mesh_right = trimesh.boolean.difference([mesh_right, cube], engine='manifold')
        else:
            cube.apply_translation([plane_x - cube_d/2, min_int_y + cube_w/2, h])
            # subtract cube to left mesh
            mesh_left = trimesh.boolean.difference([mesh_left, cube], engine='manifold')
            # add cube to right mesh
            mesh_right = trimesh.boolean.union([mesh_right, cube], engine='manifold')

    # repair
    mesh_left.fill_holes()
    mesh_left.fix_normals()
    mesh_right.fill_holes()
    mesh_right.fix_normals()

    return mesh_left, mesh_right




def main():
    # messages will print to console
    trimesh.util.attach_to_log()

    mesh = trimesh.load('input_stl/ASTM_D638_TypeIV_Tensile_Test.STL')
    mesh_left, mesh_right, centroid = split_mesh(mesh)

    mesh_left_with_interlock, mesh_right_with_interlock = add_cube_interlock(mesh_left, mesh_right, beam_depth_layers=4)


    mesh_left_with_interlock.export('output/mesh_left.stl')
    mesh_right_with_interlock.export('output/mesh_right.stl')



if __name__ == '__main__':
    main()

