bl_info = {
    "name": "Arma 3 Object Builder utility functions",
    "author": "MrClock",
    "version": (1, 0, 0),
    "blender": (2, 83, 0),
    "location": "View 3D > Object Builder",
    "description": "Utility functions based on some features of the Arma 3 Object Builder",
    "warning": "Initial release",
    # "tracker_url": "",
    # "support": "TESTING",
    "doc_url": "",
    "category": "3D View"
}

import bpy
import bmesh
import re

# Utility functions
def ShowInfoBox(message,title = "",icon = 'INFO'):
    def draw(self,context):
        self.layout.label(text = message)
    bpy.context.window_manager.popup_menu(draw,title = title,icon = icon)
    
def isSingleSelection():
    if len(bpy.context.selected_objects) != 1:
        ShowInfoBox('More than one objects are selected','Error','ERROR')
        return False
    return True
    
def isMesh(obj):
    if obj.type != 'MESH':
        ShowInfoBox('The selected object is not a mesh','Error','ERROR')
        return False
    return True

# Operator functions
def findComponents(convexHull=False):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_mode(type='VERT')
    
    activeObj = bpy.context.active_object
    
    # Remove pre-existing component selections
    componentGroups = []
    for group in activeObj.vertex_groups:
        if re.match('component\d+',group.name,re.IGNORECASE):
            componentGroups.append(group.name)
    
    for i,group in enumerate(componentGroups):
        bpy.ops.object.vertex_group_set_active(group=group)
        bpy.ops.object.vertex_group_remove()
        
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Create new groups
    componentID = 1
    for i in range(len(activeObj.data.vertices)):
        if activeObj.data.vertices[i].hide == True:
            continue
        
        activeObj.data.vertices[i].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_linked()
        bpy.ops.object.mode_set(mode='OBJECT')
        
        if convexHull:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.convex_hull()
            bpy.ops.object.mode_set(mode='OBJECT')
            
        bpy.ops.object.mode_set(mode='EDIT')
        activeObj.vertex_groups.new(name=('Component%02d' % componentID))
        bpy.ops.object.vertex_group_assign()
        componentID += 1
        bpy.ops.mesh.hide()
        bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

def convexHull():
    # Force edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_mode(type="EDGE")
    bpy.ops.mesh.select_all(action = 'SELECT')

    bpy.ops.mesh.convex_hull()
    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

def componentConvexHull(): # DEPRECATED
    activeObj = bpy.context.selected_objects[0]
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action = 'DESELECT')
    
    activeObj.vertex_groups.active_index = 0
    print(activeObj.vertex_groups.active_index)
    
    for i,group in enumerate(activeObj.vertex_groups):
        if not re.match('component\d+',group.name,re.IGNORECASE):
            continue
                
        bpy.ops.mesh.select_all(action = 'DESELECT')
        activeObj.vertex_groups.active_index = i
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.convex_hull()
        
    bpy.ops.mesh.select_all(action = 'DESELECT')

def checkClosed():
    # Force edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="EDGE")
    
    bpy.ops.mesh.select_non_manifold()

def checkConvexity():
    activeObj = bpy.context.selected_objects[0]

    # Force edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action = 'DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')    
    
    bm = bmesh.new(use_operators=True)
    
    bm.from_mesh(activeObj.data)
    
    concaveCount = 0
    
    for edge in bm.edges:
        if not edge.is_convex:

            face1 = edge.link_faces[0]
            face2 = edge.link_faces[1]
            dot = face1.normal.dot(face2.normal)
            
            if not (0.9999 <= dot and dot <=1.0001):
                edge.select_set(True)
                concaveCount += 1
            
    bm.to_mesh(activeObj.data)
        
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="EDGE")
    
    return activeObj.name, concaveCount

# Menus
class MRC_A3_MT_ObjectBuilder_Topo(bpy.types.Menu):
    '''Object Builder topology functions'''
    
    bl_label = 'Topology'
    
    def draw(self,context):
        self.layout.operator(MRC_A3_OT_CheckClosed.bl_idname)
        self.layout.operator(MRC_A3_OT_FindComponents.bl_idname)

class MRC_A3_MT_ObjectBuilder_Convexity(bpy.types.Menu):
    '''Object Builder convexity functions'''
    
    bl_label = 'Convexity'
    
    def draw(self,context):
        self.layout.operator(MRC_A3_OT_CheckConvexity.bl_idname)
        self.layout.operator(MRC_A3_OT_ConvexHull.bl_idname)
        self.layout.operator(MRC_A3_OT_ComponentConvexHull.bl_idname)

class MRC_A3_MT_ObjectBuilder(bpy.types.Menu):
    '''Arma 3 Object Builder utility functions'''
    
    bl_label = 'Object Builder'
    
    def draw(self,context):
        self.layout.menu('MRC_A3_MT_ObjectBuilder_Topo')
        self.layout.menu('MRC_A3_MT_ObjectBuilder_Convexity')

# Operators
class MRC_A3_OT_CheckConvexity(bpy.types.Operator):
    '''Find concave edges'''
    
    bl_label = 'Find Non-Convexities'
    bl_idname = 'mrc_a3_ob.nonconvexities'
    
    @classmethod
    def poll(cls,context):
        return len(bpy.context.selected_objects) == 1 and bpy.context.selected_objects[0].type == 'MESH'
    
    def execute(self,context):
        name, concaves = checkConvexity()
        
        if concaves > 0:
            self.report({'WARNING'},f'{name} has {concaves} concave edges')
            ShowInfoBox(f'{name} has {concaves} concave edges','Warning','ERROR')
        else:
            self.report({'INFO'},f'{name} is convex')
            ShowInfoBox(f'{name} is convex','Info','INFO')
        
        return {'FINISHED'}

class MRC_A3_OT_CheckClosed(bpy.types.Operator):
    '''Find non-closed parts of model'''
    
    bl_label = 'Find Non-Closed'
    bl_idname = 'mrc_a3_ob.nonclosed'
    
    @classmethod
    def poll(cls,context):
        return len(bpy.context.selected_objects) == 1 and bpy.context.selected_objects[0].type == 'MESH'
    
    def execute(self,context):
        
        checkClosed()
        
        return {'FINISHED'}

class MRC_A3_OT_ConvexHull(bpy.types.Operator):
    '''Calculate convex hull for entire object'''
    
    bl_label = 'Convex Hull'
    bl_idname = 'mrc_a3_ob.convexhull'
    
    @classmethod
    def poll(cls,context):
        return len(bpy.context.selected_objects) == 1 and bpy.context.selected_objects[0].type == 'MESH'
    
    def execute(self,context):
        mode = bpy.context.object.mode
        convexHull()
        bpy.ops.object.mode_set(mode=mode)
        
        return {'FINISHED'}
    
class MRC_A3_OT_ComponentConvexHull(bpy.types.Operator):
    '''Create convex named component selections'''
    
    bl_label = 'Component Convex Hull'
    bl_idname = 'mrc_a3_ob.componentconvexhull'
    
    @classmethod
    def poll(cls,context):
        return len(bpy.context.selected_objects) == 1 and bpy.context.selected_objects[0].type == 'MESH'
    
    def execute(self,context):
        mode = bpy.context.object.mode
        findComponents(True)
        bpy.ops.object.mode_set(mode=mode)
        
        return {'FINISHED'}

class MRC_A3_OT_FindComponents(bpy.types.Operator):
    '''Create named component selections'''
    
    bl_label = 'Find Components'
    bl_idname = 'mrc_a3_ob.findcomponents'
    
    @classmethod
    def poll(cls,context):
        return len(bpy.context.selected_objects) == 1 and bpy.context.selected_objects[0].type == 'MESH'
    
    def execute(self,context):
        mode = bpy.context.object.mode
        findComponents()
        bpy.ops.object.mode_set(mode=mode)
        
        return {'FINISHED'}

classes = (
    MRC_A3_OT_CheckConvexity,
    MRC_A3_OT_CheckClosed,
    MRC_A3_OT_ConvexHull,
    MRC_A3_OT_ComponentConvexHull,
    MRC_A3_OT_FindComponents,
    MRC_A3_MT_ObjectBuilder,
    MRC_A3_MT_ObjectBuilder_Topo,
    MRC_A3_MT_ObjectBuilder_Convexity
)

def menu_func(self,context):
    self.layout.separator()
    self.layout.menu('MRC_A3_MT_ObjectBuilder')

def register():
    from bpy.utils import register_class
    
    for cls in classes:
        register_class(cls)
    
    bpy.types.VIEW3D_MT_editor_menus.append(menu_func)

def unregister():
    from bpy.utils import unregister_class
            
    bpy.types.VIEW3D_MT_editor_menus.remove(menu_func)

    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()