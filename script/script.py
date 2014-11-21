"""
A script to create stereographic lampshades from SVG patterns
Inspired by http://jasmcole.com/2014/11/01/stereographic-lampshades/
"""
import bpy

from math import cos, sin, atan, atan2


def convert_to_polar_coordinates(x, y):
    """
    finds the polar coordinates given cartesian x and y
    returns r, theta(degrees)
    """
    polar_radius = (x ** 2 + y ** 2) ** .5
    polar_phi = atan2(y,x)
    return polar_radius, polar_phi


def compute_angle_from_top_lampshade(r, a, h):
    return atan(float(r) / (a + h))


def compute_new_coordinates(vertex_coordinates, distance_to_center_of_lampshade, radius_of_lampshade):
    """
    Back computing the projection onto the sphere
    """
    x, y, z = vertex_coordinates
    polar_radius, polar_phi = convert_to_polar_coordinates(x,y)
    
    theta = compute_angle_from_top_lampshade(
        polar_radius,
        radius_of_lampshade,
        distance_to_center_of_lampshade
    )
    alpha = 2 * theta

    x_new = radius_of_lampshade * sin(alpha) * cos(polar_phi)
    y_new = radius_of_lampshade * sin(alpha) * sin(polar_phi)
    z_new = distance_to_center_of_lampshade - radius_of_lampshade * cos(alpha)
    
    return (x_new, y_new, z_new)


def move_svg_to_origin():
    """
    Moves the SVG Object to origin
    """
    bpy.ops.object.mode_set(mode="OBJECT")
    #move the object to origin
    bpy.ops.object.origin_set(type="GEOMETRY_ORIGIN")


def scale_svg(factor):
    #only scale x and y because SVG a flat image
     bpy.ops.transform.resize(
         value=(factor,factor, 1.0)
     )

     #need to transform apply otherwise the resize won't affect the mesh coordinates
     bpy.ops.object.transform_apply(
         location=False,
         rotation=False,
         scale=True
     )


def setup_svg(scale=100):
    """
    Assume the imported SVG is very small, scale the SVG up for easier manipulation
    """
    move_svg_to_origin()
    scale_svg(scale)
    

def convert_svg_to_mesh():
    #convert SVG (Blender Curve) to a Mesh
    bpy.ops.object.convert(target='MESH', keep_original=False)

    cleanup_mesh_to_reduce_future_artifacts()


def rearrange_faces_for_better_results():
    """
    This will remove long thin faces, that will cause artifacts
    """
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.beautify_fill()
    bpy.ops.object.mode_set(mode="OBJECT")


def change_mesh_color_for_better_visualization(selected_object):
    #fancy display to better visualize the changes
    selected_object.data.materials[0].diffuse_color = (1.0, 1.0, 1.0)


def remove_duplicate_vertices():
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(use_unselected=True)
    #need to switch modes for the remove doubles to apply
    bpy.ops.object.mode_set(mode="OBJECT")


def make_normals_consistently_outwards():
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent()
    bpy.ops.object.mode_set(mode="OBJECT")


def extrude(value):
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value":(0,0,value)}
    )


def scale_after_extrusion(extrude_value, radius_of_lampshade):
    """
    Proportionally scale outwards after the extrusion to create a lampshade with some thickness
    """
    resize = 1 - extrude_value/radius_of_lampshade
    bpy.ops.transform.resize(value=(resize, resize, resize))


def cleanup_mesh_to_reduce_future_artifacts():
    remove_duplicate_vertices()
    rearrange_faces_for_better_results()


def transform_to_lampshade(selected_object, distance_to_center_of_lampshade, radius_of_lampshade):
    for vertex in selected_object.data.vertices:
        vertex.co = compute_new_coordinates(vertex.co, distance_to_center_of_lampshade, radius_of_lampshade)


def make_printable(thickness, radius_of_lampshade):
    make_solid(thickness, radius_of_lampshade)
    make_normals_consistently_outwards()


def make_solid(thickness, radius_of_lampshade):
    extrude(thickness)
    scale_after_extrusion(thickness, radius_of_lampshade)


def create_stereographic_lampshade(distance_to_center_of_lampshade,
                                   radius_of_lampshade,
                                   thickness_of_lampshade):
    """
    distance_to_center_of_lampshade and radius_of_lampshade are used to back project the SVG
    the actual height and radius may very a little depending on the thickness_of_lampshade
    """
    
    selected_object = bpy.context.scene.objects.active
    
    setup_svg()
    
    convert_svg_to_mesh()

    change_mesh_color_for_better_visualization(selected_object)

    transform_to_lampshade(selected_object, distance_to_center_of_lampshade, radius_of_lampshade)

    make_printable(thickness_of_lampshade, radius_of_lampshade)


create_stereographic_lampshade(
    distance_to_center_of_lampshade=5,
    radius_of_lampshade=5,
    thickness_of_lampshade=0.08)
