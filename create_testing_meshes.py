from split_mesh import split_mesh
from dovetail_interlock_3D import add_3d_dovetail_interlock
import trimesh
import os

"""
Testing script to create all of the STL files for different parameters
"""

def test():
    # messages will print to console
    trimesh.util.attach_to_log()

    test_mesh = trimesh.load('input_stl/ASTM_D638_TypeIV_Tensile_Test.STL')
    test_left_mesh, test_right_mesh = split_mesh(test_mesh)

    # ------------------------- TESTING DIFFERENT INVERSIONS WITH EACH OTHER TEST ------------------------- #

    # different inversion options (z_invert, y_invert)
    inversions = [(False, False), (True, False), (False, True), (True, True)]

    for (z_invert, y_invert) in inversions:

        # create invert text for file paths
        if z_invert and y_invert:
            invert_folder_path = 'y_and_z_invert'

        elif z_invert and not y_invert:
            invert_folder_path = 'z_invert_only'

        elif not z_invert and y_invert:
            invert_folder_path = 'y_invert_only'

        else:
            invert_folder_path = 'no_invert'
        

        # ------------------------- TESTING DIFFERENT TAPER ANGLES ------------------------- #
        
        print('Testing different taper angles...')

        # parameters
        beam_depth_layers = 4
        beam_height_layers = 4 
        avoidance_layers = 2

        # variable parameter
        taper_angles = [25, 30, 35, 40, 45, 50]

        for z_angle in taper_angles:

            for y_angle in taper_angles:

                left_mesh = test_left_mesh.copy()
                right_mesh = test_right_mesh.copy()

                add_3d_dovetail_interlock(
                    left_mesh, 
                    right_mesh, 
                    taper_angle_z_deg=z_angle, 
                    taper_angle_y_deg=y_angle, 
                    beam_width_layers=beam_depth_layers, 
                    beam_height_layers=beam_height_layers, 
                    avoidance_layers=avoidance_layers, 
                    z_inverted=z_invert,
                    y_inverted=y_invert
                )

                # create paths and export meshes
                left_mesh_path = f'output/taper_angles/{invert_folder_path}/mesh_left_z_{z_angle}_y_{y_angle}.stl'
                right_mesh_path = f'output/taper_angles/{invert_folder_path}/mesh_right_z_{z_angle}_y_{y_angle}.stl'

                os.makedirs(os.path.dirname(left_mesh_path), exist_ok=True)
                os.makedirs(os.path.dirname(right_mesh_path), exist_ok=True)

                left_mesh.export(left_mesh_path)
                right_mesh.export(right_mesh_path)

        print('Taper angle testing complete')


        print(f'Completed tesing inversion ({invert_folder_path})')

    

    print('All testing complete')

    
if __name__ == '__main__':
    test()



