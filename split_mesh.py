import numpy as np
import trimesh


def split_mesh(mesh):
    """
    Splits mesh into two halves
    
    Args:
        mesh: The mesh to be split

    Returns:
        Two mesh objects
        
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

    return mesh_left, mesh_right



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

    # print(f'Cutface width (Y): {cut_width:.2f} mm')
    # print(f'Cutface height (Z): {cut_height:.2f} mm')

    return cut_width, cut_height, (min_y, max_y, min_z, max_z)

