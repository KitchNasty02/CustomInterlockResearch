from split_mesh import split_mesh
from beam_interlock import add_beam_interlock_in_y, add_beam_interlock_in_z
import trimesh


def main():
    # messages will print to console
    trimesh.util.attach_to_log()

    mesh = trimesh.load('input_stl/ASTM_D638_TypeIV_Tensile_Test.STL')
    mesh_left, mesh_right = split_mesh(mesh)

    mesh_left_with_interlock, mesh_right_with_interlock = add_beam_interlock_in_z(mesh_left, mesh_right, beam_depth_layers=4)


    mesh_left_with_interlock.export('output/mesh_left.stl')
    mesh_right_with_interlock.export('output/mesh_right.stl')



if __name__ == '__main__':
    main()

