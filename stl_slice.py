from split_mesh import split_mesh
from beam_interlock import add_beam_interlock_in_y, add_beam_interlock_in_z
from dovetail_interlock import add_dovetail_interlock_in_z
import trimesh


def main():
    # messages will print to console
    trimesh.util.attach_to_log()

    mesh = trimesh.load('input_stl/ASTM_D638_TypeIV_Tensile_Test.STL')
    mesh_left, mesh_right = split_mesh(mesh)

    # mesh_left, mesh_right = add_beam_interlock_in_z(mesh_left, mesh_right, beam_depth_layers=4)
    mesh_left, mesh_right = add_dovetail_interlock_in_z(mesh_left, mesh_right, taper_angle_deg=25, beam_depth_layers=8, beam_height_layers=4, avoidance_dist=0.8)


    mesh_left.export('output/mesh_left.stl')
    mesh_right.export('output/mesh_right.stl')



if __name__ == '__main__':
    main()

