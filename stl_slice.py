import numpy as np
import trimesh


# messages will print to console
trimesh.util.attach_to_log()

mesh = trimesh.load('input_stl/ASTM_D638_TypeIV_Tensile_Test.STL')
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

print(f'Is left watertight: {mesh_left.is_watertight}')
print(f'Is right watertight: {mesh_right.is_watertight}')


mesh_left.export('output/mesh_left.stl')
mesh_right.export('output/mesh_right.stl')


