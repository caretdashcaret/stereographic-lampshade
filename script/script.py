"""
A script to create stereographic lampshades from SVG patterns
Inspired by http://jasmcole.com/2014/11/01/stereographic-lampshades/
"""
import bpy
import mathutils

from math import cos, sin, atan, atan2

bl_info = {
        "name": "Stereographic Projection",
        "description": "Make stereographic projections from a SVG image",
        "author": "Jenny \"caretdashcaret\", Simon Egli",
        "version": (0, 9),
        "blender": (2, 75, 0),
        "location": "Add > Mesh > Stereographic Projection",
        "warning": "", # used for warning icon and text in addons panel
        "wiki_url": ""
        "",
        "category": "Add Mesh"}


class Projection():
    """Class for calculating stereographic projections"""

    def __init__(self):
        self.test = 1

    def convert_to_polar_coordinates(self,x, y):
        """
        finds the polar coordinates given cartesian x and y
        returns r, theta(degrees)
        """
        polar_radius = (x ** 2 + y ** 2) ** .5
        polar_phi = atan2(y,x)
        return polar_radius, polar_phi


    def compute_angle_from_top_lampshade(self,r, a, h):
        return atan(float(r) / (a + h))


    def compute_new_coordinates(self,vertex_coordinates, distance_to_center_of_lampshade, radius_of_lampshade):
        """
        Back computing the projection onto the sphere
        """
        x, y, z = vertex_coordinates
        polar_radius, polar_phi = self.convert_to_polar_coordinates(x,y)

        theta = self.compute_angle_from_top_lampshade(
            polar_radius,
            radius_of_lampshade,
            distance_to_center_of_lampshade
        )
        alpha = 2 * theta

        x_new =radius_of_lampshade * sin(alpha) * cos(polar_phi)
        y_new =radius_of_lampshade * sin(alpha) * sin(polar_phi)
        z_new = distance_to_center_of_lampshade - radius_of_lampshade * cos(alpha)

        return (x_new, y_new, z_new)


    def move_svg_to_origin(self):
        """
        Moves the SVG Object to origin
        """
        bpy.ops.object.mode_set(mode="OBJECT")
        #move the object to origin
        bpy.ops.object.origin_set(type="GEOMETRY_ORIGIN")


    def scale_svg(self,factor):
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


    def setup_svg(self,scale=100):
        """
        Assume the imported SVG is very small, scale the SVG up for easier manipulation
        """
        self.move_svg_to_origin()
        self.scale_svg(scale)


    def convert_svg_to_mesh(self):
        #convert SVG (Blender Curve) to a Mesh
        bpy.ops.object.convert(target='MESH', keep_original=False)

        self.cleanup_mesh_to_reduce_future_artifacts()


    def rearrange_faces_for_better_results(self):
        """
        This will remove long thin faces, that will cause artifacts
        """
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.beautify_fill()
        bpy.ops.object.mode_set(mode="OBJECT")


    def change_mesh_color_for_better_visualization(self,selected_object):
        #fancy display to better visualize the changes
        selected_object.data.materials[0].diffuse_color = (1.0, 1.0, 1.0)


    def remove_duplicate_vertices(self):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(use_unselected=True)
        #need to switch modes for the remove doubles to apply
        bpy.ops.object.mode_set(mode="OBJECT")


    def make_normals_consistently_outwards(self):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.normals_make_consistent()
        bpy.ops.object.mode_set(mode="OBJECT")


    def extrude(self,value):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.extrude_region_move(
            TRANSFORM_OT_translate={"value":(0,0,value)}
        )


    def scale_after_extrusion(self,extrude_value, radius_of_lampshade):
        """
        Proportionally scale outwards after the extrusion to create a lampshade with some thickness
        """
        resize = 1 - extrude_value/radius_of_lampshade
        bpy.ops.transform.resize(value=(resize, resize, resize))


    def cleanup_mesh_to_reduce_future_artifacts(self):
        self.remove_duplicate_vertices()
        self.rearrange_faces_for_better_results()


    def transform_to_lampshade(self,selected_object, distance_to_center_of_lampshade, radius_of_lampshade):
        for vertex in selected_object.data.vertices:
            vertex.co = self.compute_new_coordinates(vertex.co, distance_to_center_of_lampshade, radius_of_lampshade)


    def make_printable(self,thickness, radius_of_lampshade):
        self.make_solid(thickness, radius_of_lampshade)
        self.make_normals_consistently_outwards()


    def make_solid(self,thickness, radius_of_lampshade):
        self.extrude(thickness)
        self.scale_after_extrusion(thickness, radius_of_lampshade)

    def move_object_to_center(self, selected_object, distance_to_center_of_lampshade, radius_of_lampshade):
        # adjustment values
       (x,y,z) = (0,0,radius_of_lampshade-distance_to_center_of_lampshade)

       # adding adjustment values to the property
       selected_object.location = selected_object.location + mathutils.Vector((x,y,z))
       bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
       #bpy.ops.object.origin_set(type="GEOMETRY_ORIGIN")


    def create_stereographic_lampshade(self, distance_to_center_of_lampshade,
                                       radius_of_lampshade,
                                       thickness_of_lampshade):
        """
        distance_to_center_of_lampshade and radius_of_lampshade are used to back project the SVG
        the actual height and radius may very a little depending on the thickness_of_lampshade
        """

        selected_object = bpy.context.scene.objects.active

        self.setup_svg()

        self.convert_svg_to_mesh()

        self.change_mesh_color_for_better_visualization(selected_object)

        self.transform_to_lampshade(selected_object, distance_to_center_of_lampshade, radius_of_lampshade)

        self.make_printable(thickness_of_lampshade, radius_of_lampshade)
        self.move_object_to_center(selected_object, distance_to_center_of_lampshade, radius_of_lampshade)

import bpy
from bpy.props import *
from bpy_extras import object_utils

class add_mesh_projection(bpy.types.Operator):
    """Add entry for stereographic projection"""
    bl_idname = 'mesh.projection_add'
    bl_label = 'Add Stereographic Projection'
    bl_options = {'REGISTER', 'UNDO'}

    dist = FloatProperty(
        name = 'Distance', default = 5.0,
        min = 0.0,
        description='Distance of lamp to Polar')

    radius = FloatProperty(
        name = 'Radius', default = 5.0,
        min = 0.0,
        description='Radius of lampshade')

    thickness = FloatProperty(
        name = 'Thickness', default = 0.05,
        min = 0.0,
        description='Thickness to print')

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return context.scene is not None

    ##### EXECUTE #####
    def execute(self, context):
        mesh = bpy.data.meshes.new(name='projection')

        proj = Projection()
        #distance,radius,thickness
        proj.create_stereographic_lampshade(self.dist,self.radius,self.thickness)


        return {'FINISHED'}


def menu_func(self, context):
        self.layout.operator(add_mesh_projection.bl_idname, text = bl_info['name'], icon="PLUGIN")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
