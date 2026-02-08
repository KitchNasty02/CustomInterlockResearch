import numpy as np
import trimesh



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



def add_cube_interlock(mesh_left, mesh_right, centroid):
    """
    Adds a cube-based interlock between two mesh halves
    
    Args:
        mesh_left: The mesh to have interlock union
        mesh_right: The mesh to have interlock difference
        centroid: Centroid of original mesh

    Returns:
        Two mesh objects with interlock
    """
    # define interlock cube
    cube_size = [1.0, 1.0, 1.0] # in mm -- MAKE BASED ON INTERFACE SIZE

    plane_x = mesh_left.bounds[1][0] # max left of mesh (where the cut was)

    # create cube and align with cut plane
    cube = trimesh.creation.box(extents=cube_size)
    cube.apply_translation([plane_x + cube_size[0]/2, centroid[1], centroid[2]])

    # add cube to left mesh
    mesh_left_with_union = trimesh.boolean.union([mesh_left, cube], engine='manifold')

    # add cube to right mesh
    mesh_right_with_difference = trimesh.boolean.difference([mesh_right, cube], engine='manifold')

    # repair
    mesh_left_with_union.fill_holes()
    mesh_left_with_union.fix_normals()
    mesh_right_with_difference.fill_holes()
    mesh_right_with_difference.fix_normals()

    return mesh_left_with_union, mesh_right_with_difference




def main():
    # messages will print to console
    trimesh.util.attach_to_log()

    mesh = trimesh.load('input_stl/ASTM_D638_TypeIV_Tensile_Test.STL')
    mesh_left, mesh_right, centroid = split_mesh(mesh)

    mesh_left_with_interlock, mesh_right_with_interlock = add_cube_interlock(mesh_left, mesh_right, centroid)


    mesh_left_with_interlock.export('output/mesh_left.stl')
    mesh_right_with_interlock.export('output/mesh_right.stl')



if __name__ == '__main__':
    main()

