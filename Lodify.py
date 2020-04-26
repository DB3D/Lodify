
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

###########################################################################################

bl_info = {
    "name"        : "Lodify",
    "description" : "Both LODs and Proxy system for blender 2.80+",
    "author"      : "DB3D",
    "version"     : (0, 1),
    "blender"     : (2, 80, 0),
    "location"    : "''Propeties'' > ''Object Data'' > ''Level of Detail''",
    "warning"     : "",
    "wiki_url"    : "",
    "tracker_url" : "",
    "category"    : "Object"
}

import bpy

###########################################################################################

doctxt="""
_____________________________________________________________________________________________                    

About the addon:
_____________________________________________________________________________________________                    

 -  You can choose which lods you want to display in either the active viewport, the
    rendered view or the final render individually. 
  
 -  The LOD system use API properties stored within your object and object-data
    properties, that mean that once you created a LOD system for your object,
    the LOD(s) data will stick with it once you copy or append your obj to
    another file for example. Even to users who don't have Lodify installed yet. 

 -  You can automatically search for lods according to their names,  if you use a 
    "Suzanne LOD 0","Suzanne LOD 1","Suzanne LOD 2" naming system or something similar. 

 -  You can use this LOD system as a data backup management system if you need to store
    your mesh data while working on destructive hardsurface modeling for example.
    You will find two 'backup' operators in the menu next to the LOD list. 

 -  Note that each LODs can have their own materials, as the material data is stored per
    meshes and not per objects.

 -  Keep in mind that pointers are considered as data-users. You might want to clean
    leftovers pointers from deleted objects with the 'cleanse data-block' operator.

 -  If you are animating via Modifiers (Bones for ex) the LOD system will work perfectly with
    your animation, assuming that the Vgroups are all assigned correctly for each level of detail
    (that's why it's more easy to create your lod from the final model, as the vgroup will 
    automatically be assigned when you simplify the topology or decimate it).Shape Keys animation
    are not compatible with LOD.

 - Regarding the Rendered view automatic mesh-data switching:
   Note that Lodify will try to update the mesh-data on each "blender internal update signal" 
   (called depsgraph update), so if you use a custom shortcut or pie menu that don't send those 
   "depsgraph updates" you might just want to click anywhere on the viewport to send a new one. 
   (the default header shading viewport buttons will work 100% of the time for sure).

 - The addon was not made with linking from external blends in mind.

_____________________________________________________________________________________________                    

About the addon python code:
_____________________________________________________________________________________________                    

 -  This addon basically act as a big mesh-data exchanging system where i exchange mesh data
    according to booleans stored in ui-lists. 

 -  As i'm drawing inside object-meshdata and i'm constantly switching the active mesh,
    'lod_original' pointer is used as a constance, and is stored in object properties of
    all mesh-data owners. if you need to work with lodify api, always use this constance 
    if not None. object.data is simply not reliable (-> 'true_mesh_data')

 -  All the Lod-switch is done via a fct on each depsg udpate, (->'analyse_and_exchange_data')
    the code just analyse the ui-lists of all objects, if list exist and if boolean filled,
    the mesh-data is exchanged or restored accordingly.

 -  Due to a severe blender crash, while in rendered view, if data is changed from a fct in a
    depsgraph, it will crash blender back to desktop instantaneously. To counter that, if user 
    in rendered view and changing rendered boolan, the view will be toggled back and forth.
    You can experience this bug for yourself if you delete 'toggle_shading' in lines 825 and 827.


"""
###########################################################################################
#
#   .oooooo.                                               .
#  d8P'  `Y8b                                            .o8
# 888      888 oo.ooooo.   .ooooo.  oooo d8b  .oooo.   .o888oo  .ooooo.  oooo d8b  .oooo.o
# 888      888  888' `88b d88' `88b `888""8P `P  )88b    888   d88' `88b `888""8P d88(  "8
# 888      888  888   888 888ooo888  888      .oP"888    888   888   888  888     `"Y88b.
# `88b    d88'  888   888 888    .o  888     d8(  888    888 . 888   888  888     o.  )88b
#  `Y8bood8P'   888bod8P' `Y8bod8P' d888b    `Y888""8o   "888" `Y8bod8P' d888b    8""888P'
#               888
#              o888o
###########################################################################################


class LODIFY_OT_list_actions(bpy.types.Operator):
    """add or remove items from list"""
    bl_idname      = "lodify.list_action"
    bl_label       = ""
    bl_description = "Add and remove Level of Details"

    action : bpy.props.StringProperty()
    mesh_n : bpy.props.StringProperty()

    def execute(self, context):

        msh = bpy.data.meshes[self.mesh_n]
        idx = msh.lod_list_index

        if self.action == 'ADD':
            item = msh.lod_list.add()
            item.name = msh.name
            item.ui_idx = len(msh.lod_list)
            msh.lod_list_index = len(msh.lod_list)-1
            # fill pointer with original data if needed
            fill_original_pointer(msh)

        if self.action == 'REMOVE':
            msh.lod_list_index -= 1
            msh.lod_list.remove(idx)
            # clean pointer and restore original data if needed
            clean_original_pointer()
            # maybe user deleted active boolean
            analyse_and_exchange_data()
        return {"FINISHED"}


class LODIFY_OT_clear_list(bpy.types.Operator):
    """Clear all items of the desired mesh list"""
    bl_idname      = "lodify.clear_list"
    bl_label       = ""
    bl_description = "Clear all items of the list"

    mesh_n : bpy.props.StringProperty()

    def execute(self, context):

        if bool(bpy.data.meshes[self.mesh_n].lod_list):
            bpy.data.meshes[self.mesh_n].lod_list.clear()
            #clean pointer and restore original data if needed
            clean_original_pointer()
        return{'FINISHED'}


class LODIFY_OT_docs(bpy.types.Operator):
    """Clear all items of the desired mesh list"""
    bl_idname      = "lodify.docs"
    bl_label       = ""
    bl_description = "Pop up documentations"

    def execute(self, context):

        def draw(self, context):
            global doctxt
            layout = self.layout
            layout.scale_y = 0.8
            for line in doctxt.splitlines():
                layout.label(text=line)

        bpy.context.window_manager.popup_menu(draw, title = 'Documentation', icon = 'QUESTION')
        return{'FINISHED'}

 
class LODIFY_OT_data_refresh(bpy.types.Operator):
    """scan for mesh-data to exchange manually
    usually this fct is done on each despg update
    within the addon, but you might want to refresh it manually"""
    bl_idname      = "lodify.data_refresh"
    bl_label       = ""
    bl_description = "scan for mesh-data to exchange according to ui-list booleans"

    def execute(self, context):
        analyse_and_exchange_data()
        return{'FINISHED'}


class LODIFY_OT_create_backup(bpy.types.Operator):
    """create a backup of the active mesh-data used by the object, and store it as a Lod"""
    bl_idname      = "lodify.create_backup"
    bl_label       = ""
    bl_description = "use the lod system to create a backup of the active mesh your object is using"

    def execute(self, context):
        obj = context.object
        new_msh = bpy.data.meshes.new_from_object(obj)
        new_msh.name = obj.data.name + '_copy'

        msh = true_mesh_data(obj)
        bpy.ops.lodify.list_action(action='ADD',mesh_n=msh.name)
        obj.lod_original.lod_list[-1].ui_lod = new_msh

        return{'FINISHED'}


class LODIFY_OT_restore_backup(bpy.types.Operator):
    """restore chosen backup data to mesh-data of active object"""

    bl_idname      = "lodify.restore_backup"
    bl_label       = ""
    bl_description = "restore chosen backup data to mesh-data of active object"

    act_n : bpy.props.StringProperty(description="active msh name")
    bck_n : bpy.props.StringProperty(description="backup msh name")

    def execute(self, context):

        if (self.act_n in bpy.data.meshes) and (self.bck_n in bpy.data.meshes):
            act_n =  bpy.data.meshes[self.act_n]
            bck_n =  bpy.data.meshes[self.bck_n]
            exchange_bmesh_data( act_n , bck_n )

        return{'FINISHED'}


class LODIFY_MT_restore_backup(bpy.types.Menu):
    """restore backup sub-menu"""
    bl_idname = "LODIFY_MT_restore_backup"
    bl_label  = ""

    def draw(self, context):
        layout = self.layout
        layout.label(text='Replace active data by : ')
        layout.separator(factor=1.0)

        obj = context.object
        msh = true_mesh_data(obj)
        for lod_n in [s.ui_lod.name for s in msh.lod_list if s.ui_lod]:
            t=layout.operator("lodify.restore_backup", icon="LOOP_BACK", text=lod_n)
            t.act_n=obj.data.name
            t.bck_n=lod_n


class LODIFY_OT_cleanse_data(bpy.types.Operator):
    """when user delete meshes that use a lod system, the deleted data
    may still have used-pointer that take users data. (may)
    if a mesh-data iss not used in any scenes, and if this mesh-data have
    an active lod-list with active pointers, or, if not used object still
    have original_mesh pointer active, all pointer need to be cleanse"""
    bl_idname      = "lodify.cleanse_data"
    bl_label       = ""
    bl_description = "cleanse left over pointers from deleted/non-used data (obj/msh)"

    def execute(self, context):

        for msh in _all_unused_meshes():
            if len(msh.lod_list) !=0:
                #print(f'unused list detected,start cleaning :{msh.name}')
                bpy.ops.lodify.clear_list(mesh_n=msh.name)
                msh.lod_enabled = False

        for obj in _all_unused_objects():
            if bool(obj.lod_original):
                #print(f'unused original pointer detected,start cleaning :{obj.name}')
                obj.lod_original = None

        return{'FINISHED'}


class LODIFY_OT_clear_by_index(bpy.types.Operator):
    """clear specific slot from ui-list by it's index, starting from 0"""
    bl_idname      = "lodify.clear_by_index"
    bl_label       = ""
    bl_description = "clear this specific slot"

    index : bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object 
        msh = true_mesh_data(obj)

        msh.lod_list_index -= 1
        msh.lod_list.remove(self.index)
        # clean pointer and restore original data if needed
        clean_original_pointer()
        # maybe user deleted active boolean
        analyse_and_exchange_data()

        return{'FINISHED'}


class LODIFY_MT_clear_by_index(bpy.types.Menu):
    """clear_by_index"""
    bl_idname = "LODIFY_MT_clear_by_index"
    bl_label  = ""

    def draw(self, context):
        layout = self.layout
        layout.label(text='Clear a Specific Slot : ')
        layout.separator(factor=1.0)

        obj = context.object
        msh = true_mesh_data(obj)
        for i,s in enumerate(msh.lod_list):
            t=layout.operator("lodify.clear_by_index", icon="PANEL_CLOSE", text= str(i) + ' : ' + s.ui_lod.name if s.ui_lod else str(i) )
            t.index = i


class LODIFY_OT_auto_setup_op(bpy.types.Operator):
    """automatically set up lods/proxies from a naming system"""
    bl_idname      = "lodify.auto_setup_op"
    bl_label       = ""
    bl_description = "automatically set up lods/proxies from a naming system"

    object_n : bpy.props.StringProperty() 
    basic    : bpy.props.StringProperty() 
    suffixn  : bpy.props.StringProperty(default='_LOD_') 
    nbr      : bpy.props.IntProperty(min=1,max=3)
    auto     : bpy.props.BoolProperty(default=False) #auto set LOD0 to render, last LOD to display

    def execute(self, context):

        lod_list = find_lod(self.basic,self.suffixn,self.nbr)
        obj      = bpy.data.objects[self.object_n]
        setup_obj_lod(obj, lod_list,self.auto)

        #reset default 
        self.suffixn = '_LOD_'
        self.auto = False
        return{'FINISHED'}


class LODIFY_OT_auto_setup_dialog(bpy.types.Operator):
    """Dialog Box as Preference UI"""
    bl_idname = "lodify.auto_setup_dialog"
    bl_label = "What is the name of your Object ?"
    bl_options = {'REGISTER', 'INTERNAL'}

    ob_all  : bpy.props.EnumProperty(items= [('scene','Whole Scene assets',''),('ob','Just this asset','')],default='ob') #just ob supported right now
    basic   : bpy.props.StringProperty()
    suffixn : bpy.props.StringProperty(default='_LOD_')
    nbr     : bpy.props.EnumProperty(items= [('1','1',''),('2','2',''),('3','3','')],default  = '1')

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.lodify.auto_setup_op(object_n= context.object.name, basic= self.basic, suffixn= self.suffixn,nbr= int(self.nbr),auto= True)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        if self.ob_all == 'ob':
            layout.prop(self, 'basic',text="")

        layout.label(text=f'What is your Suffix ?')
        layout.prop(self, 'suffixn',text="")

        layout.label(text=f'How many Numbers after your Suffix ?')
        layout.prop(self, 'nbr',text="")

        if self.ob_all == 'ob':
            l = find_lod(self.basic, self.suffixn, int(self.nbr))
            txt=layout.column()
            txt.label(text=f'We found  {len(l)}  Lod(s) for the automatic set-up.')
            txt.scale_y = 0.9
            for m in l: txt.label(text=f'     " {m.name} "')


###########################################################################################
#
# oooooooooooo                                       .    o8o
# `888'     `8                                     .o8    `"'
#  888         oooo  oooo  ooo. .oo.    .ooooo.  .o888oo oooo   .ooooo.  ooo. .oo.    .oooo.o
#  888oooo8    `888  `888  `888P"Y88b  d88' `"Y8   888   `888  d88' `88b `888P"Y88b  d88(  "8
#  888    "     888   888   888   888  888         888    888  888   888  888   888  `"Y88b.
#  888          888   888   888   888  888   .o8   888 .  888  888   888  888   888  o.  )88b
# o888o         `V88V"V8P' o888o o888o `Y8bod8P'   "888" o888o `Y8bod8P' o888o o888o 8""888P'
#
###########################################################################################

def true_mesh_data(obj):
    """ because user will constantly switch data,
    and gui rely on data, we'll need to find correct mesh"""
    if obj.lod_original: return obj.lod_original
    else:                return obj.data

def only_one_prop(msh,active_idx,prop_api): 
    """ only one boolean props active at the time per type"""
    clist = msh.lod_list

    #loop over ui list slots
    for p in clist:
        if p.ui_idx != active_idx:
            exec(f"p.{prop_api} = False")
    return None 

def all_handlers():
    """return a list of all handlers of the blend"""
    r = []
    for oh in bpy.app.handlers: #so can also remove dupplicates
        try:
            for h in oh:
                r.append(h)
        except:
            pass
    return r

def _all_viewports_shading_type():
    """list all shading in window_manager"""
    r = []
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if(area.type == 'VIEW_3D'):
                for space in area.spaces:
                    if(space.type == 'VIEW_3D'):
                        r.append(space.shading.type)
    return r

def quit_rendered_shading():
    """for all spaces,quit rendered back to solid"""

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if(area.type == 'VIEW_3D'):
                for space in area.spaces:
                    if(space.type == 'VIEW_3D'):
                        if(space.shading.type == 'RENDERED'):
                            space.shading.type = 'SOLID'
    return None 

spc = None #global prop
def toggle_shading(True_False):
    """because of a blender related bug
    changind data from a handler while in rendered
    view will crash to destop, forced to back down"""
    
    global spc 
    if True_False == False:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if(area.type == 'VIEW_3D'):
                    for space in area.spaces:
                        if(space.type == 'VIEW_3D'):
                            if(space.shading.type == 'RENDERED'):
                                spc = space
                                space.shading.type = 'SOLID'        
    else:
        if spc != None: spc.shading.type = 'RENDERED'
    return None 

def find_instances(mesh_data):
    """return all obj using this mesh data"""
    r=[]
    for o in bpy.data.objects:
        if (o.type=='MESH'):
            if true_mesh_data(o) == mesh_data:
                r.append(o)
    return r

def fill_original_pointer(mesh_data):
    """fill original data pointer
    according to list status, to all instances"""

    for ob in find_instances(mesh_data):
        #if ui list not empty but pointer is -> fill pointer 
        if (len(ob.data.lod_list) > 0) and (not ob.lod_original): ob.lod_original = mesh_data
    return None 

def clean_original_pointer():
    """clean original-data-pointer (lod_original) to all obj
    in data if ui list empty, and restore to original"""

    for ob in bpy.data.objects:
        if ob.type =='MESH':
            #if ui list empty but pointer original full -> restore and clean
            if (ob.lod_original) and (len(ob.lod_original.lod_list) == 0):
                if ob.data != ob.lod_original: ob.data = ob.lod_original
                ob.lod_original = None 
    return None

def c_print(txt):
    """custom print, only when boolean allows it"""
    if bpy.context.scene.lod.p_dev_print: print(txt)
    return None 

def find_lod(basic,suf,nbr):
    """return all lod meshes from data.meshes
    from a given naming system"""
    r = []
    for m in bpy.data.meshes:
        #if suffix at right place
        if m.name[-len(suf)-nbr:-nbr] == suf:
            #if basic name ok
            if m.name.split(suf)[0] == basic:
                r.append(m)
    return r

def setup_obj_lod(obj,mesh_lod_list,auto):
    """automatic set up lods"""
    if mesh_lod_list:

        #clean list
        bpy.ops.lodify.clear_list(mesh_n=obj.data.name)

        for i,msh in enumerate(mesh_lod_list):

            #add new item in list
            item = obj.data.lod_list.add()
            item.name = obj.data.name
            item.ui_idx = len(obj.data.lod_list)
            #fill original pointer with data
            if (i==0): fill_original_pointer(obj.data)
            #define item lod
            item.ui_lod = msh
            #automatic boolean set up
            if (auto==True) and (i==0): item.ui_rdf = item.ui_rdv = True #render and rendered true if first (highest resolution)
            if (auto==True) and (i+1==len(mesh_lod_list)): item.ui_dsp = True #display true if last (lowest resolution)
            #adjust index
            obj.data.lod_list_index = len(obj.data.lod_list)-1

def _all_unused_meshes():
    """search for unused meshes"""
    scn_obj = [ob for scene in bpy.data.scenes for ob in scene.objects if ob.type == 'MESH']
    msh_scn = [ob.data for ob in scn_obj]#all scene meshes
    msh_pnt = [ui.ui_lod for msh in msh_scn for ui in msh.lod_list if ui.ui_lod]#all pointers used
    msh_opt = [ob.lod_original for ob in scn_obj if ob.lod_original]#all pointer from obj
    msh_act = msh_scn + msh_pnt + msh_opt #all scnenes meshes and their relative active pointers 
    return [x for x in list(bpy.data.meshes) if x not in msh_act]

def _all_unused_objects():
    """search for unused objects"""
    scn_obj = [ob for scene in bpy.data.scenes for ob in scene.objects if ob.type == 'MESH']
    return [x for x in list(bpy.data.objects) if x not in scn_obj]

def exchange_bmesh_data(msh_active,msh_paste):
    """exchange bmesh data, args must be data.meshes"""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(msh_paste)
    bm.to_mesh(msh_active)
    msh_active.update()


###########################################################################################
#
# oooooooooo.                                        o8o
# `888'   `Y8b                                       `"'
#  888      888 oooo d8b  .oooo.   oooo oooo    ooo oooo  ooo. .oo.    .oooooooo
#  888      888 `888""8P `P  )88b   `88. `88.  .8'  `888  `888P"Y88b  888' `88b
#  888      888  888      .oP"888    `88..]88..8'    888   888   888  888   888
#  888     d88'  888     d8(  888     `888'`888'     888   888   888  `88bod8P'
# o888bood8P'   d888b    `Y888""8o     `8'  `8'     o888o o888o o888o `8oooooo.
#                                                                     d"     YD
#                                                                     "Y88888P'
###########################################################################################



class LODIFY_UL_items(bpy.types.UIList):
    """ui list drawing"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
            
        scn  = context.scene
        row = layout.row(align=True)
        
        sub=row.row(align=True)
        sub.scale_x = 1.75
        sub.prop(item,"ui_lod",text='')

        sub=row.row(align=True)
        sub.scale_x = 1.1
        sub.enabled = bool(item.ui_lod)
        sub.prop(item,"ui_dsp",text='',icon='RESTRICT_VIEW_OFF'  if item.ui_dsp else'RESTRICT_VIEW_ON')

        if scn.lod.p_rdv_switch: sub.prop(item,'ui_rdv',text='',icon='SHADING_RENDERED')
        if scn.lod.p_rdf_switch: sub.prop(item,"ui_rdf",text='',icon='RESTRICT_RENDER_OFF'if item.ui_rdf else'RESTRICT_RENDER_ON')



class LODIFY_PT_objectList(bpy.types.Panel):
    """panel drawing in mesh data"""
    bl_idname      = 'LODIFY_PT_objectList'
    bl_label       = "Level of Detail"
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "data"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj!=None) and (obj.type=='MESH')

    def draw_header(self, context):
        layout = self.layout
        obj    = context.object
        msh    = true_mesh_data(obj)

        layout.prop(msh,"lod_enabled", text="")
        layout.enabled = (not obj.data.is_editmode)

    def draw(self, context):
        layout = self.layout
        obj    = context.object
        scn    = context.scene
        msh    = true_mesh_data(obj)

        #disable in edit mode or if Boolean false
        layout.enabled = (msh.lod_enabled) and (not obj.data.is_editmode)

        #dev info 
        if scn.lod.p_dev_info:
            dev = layout.box().column()
            dev.box().label(text='Developpement Infos-Box',icon='INFO')
            dev.separator()
            dev.prop(obj,'data',text='active mesh')
            dev.prop(obj,'lod_original')
            dev.separator()
            dev.label(text=f'actively drawing panel for     : {msh.name}')
            dev.separator()
        
        #define two rows
        row = layout.row()
        col1 = row.column()
        col2 = row.column()

        #draw template
        template = col1.column()
        template.template_list("LODIFY_UL_items", "", msh, "lod_list", msh, "lod_list_index", rows=2)
        template.scale_y = 1.1
        #
        #original/active mesh
        original = col1.column(align=False)
        original.prop(obj,'lod_original',text='original')
        original.prop(obj,'data',text='active')
        original.enabled = False #always disabled 
        original.scale_y = 0.9

        #draw side bar 
        col2.separator(factor=1.0)
        #
        add = col2.column(align=True)
        t = add.operator("lodify.list_action", icon='ADD', text="")
        t.action = 'ADD'
        t.mesh_n = msh.name
        #
        rem = col2.column(align=True)
        rem.enabled = bool(len(msh.lod_list))
        t = rem.operator("lodify.list_action", icon='REMOVE', text="")
        t.action = 'REMOVE'
        t.mesh_n = msh.name
        #
        col2.separator()
        col2.menu("LODIFY_MT_operators_menu", icon='DOWNARROW_HLT', text="")



class LODIFY_MT_operators_menu(bpy.types.Menu):
    """operator sub menu"""
    bl_idname = "LODIFY_MT_operators_menu"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        obj    = context.object
        msh    = true_mesh_data(obj)

        layout.operator("lodify.auto_setup_dialog", icon="SMALL_CAPS", text="Search for Lod(s)").basic = obj.name
        layout.separator()
        layout.menu("LODIFY_MT_clear_by_index" ,icon="TRASH"       ,text="Clear Specific")
        layout.operator("lodify.clear_list"    ,icon="TRASH"       ,text="Clear Whole List").mesh_n = msh.name
        layout.operator("lodify.cleanse_data"  ,icon="TRASH"       ,text="Cleanse data-block")
        layout.separator()
        layout.operator("lodify.create_backup" ,icon="COPY_ID"     ,text="Store as Back-up")
        layout.menu("LODIFY_MT_restore_backup" ,icon="COPY_ID"     ,text="Restore active data")
        layout.separator()
        layout.operator("lodify.dialog"        ,icon="PREFERENCES" ,text="Parameters")
        layout.operator("lodify.docs"          ,icon="QUESTION"    ,text="Documentation")


class LODIFY_OT_dialog(bpy.types.Operator):
    """Dialog Box as Preference UI"""
    bl_idname = "lodify.dialog"
    bl_label = "Options"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        obj    = context.object
        scn    = context.scene
        msh    = true_mesh_data(obj)

        #switch enable1
        layout.box().label(text='Enable automatic LOD switching',icon='ARROW_LEFTRIGHT')
        layout.prop(scn.lod, 'p_rdf_switch' ,text='automatically switch LODs on final render' )#,icon='SHADING_RENDERED')
        layout.prop(scn.lod, 'p_rdv_switch' ,text='automatically switch LODs on rendered view')#,icon='RESTRICT_RENDER_OFF')

        #switch behavior
        if scn.lod.p_rdf_switch :
            layout.box().label(text='LOD switching behavior',icon='FILE_CACHE')
            #lead to a cycle error msg but everything still works fine
            layout.prop(scn.lod,'p_tor_switch',text='turn off all rendered view after final render')
        #devs
        layout.box().label(text='Developpement',icon='SCRIPT')
        layout.prop(scn.lod, 'p_dev_info'  ,text='show developper infos in gui' )
        layout.prop(scn.lod, 'p_dev_print' ,text='show developper prints in console' )



###########################################################################################
#
# ooooo   ooooo                             .o8  oooo
# `888'   `888'                            "888  `888
#  888     888   .oooo.   ooo. .oo.    .oooo888   888   .ooooo.  oooo d8b  .oooo.o
#  888ooooo888  `P  )88b  `888P"Y88b  d88' `888   888  d88' `88b `888""8P d88(  "8
#  888     888   .oP"888   888   888  888   888   888  888ooo888  888     `"Y88b.
#  888     888  d8(  888   888   888  888   888   888  888    .o  888     o.  )88b
# o888o   o888o `Y888""8o o888o o888o `Y8bod88P" o888o `Y8bod8P' d888b    8""888P'
#
###########################################################################################


# ooooooooo.                               .o8                                     .o8
# `888   `Y88.                            "888                                    "888
#  888   .d88'  .ooooo.  ooo. .oo.    .oooo888   .ooooo.  oooo d8b  .ooooo.   .oooo888
#  888ooo88P'  d88' `88b `888P"Y88b  d88' `888  d88' `88b `888""8P d88' `88b d88' `888
#  888`88b.    888ooo888  888   888  888   888  888ooo888  888     888ooo888 888   888
#  888  `88b.  888    .o  888   888  888   888  888    .o  888     888    .o 888   888
# o888o  o888o `Y8bod8P' o888o o888o `Y8bod88P" `Y8bod8P' d888b    `Y8bod8P' `Y8bod88P"



#2.81 introduced an new 'optional' args in desp_post, breaking everything..
def reg_unreg_deps_post(reg):
    """ reg/unreg dpsgraph update fcts"""
    if reg == 'reg':
        if '2.80' in bpy.app.version_string:
            if lodify_mesh_data_exchange_80 not in all_handlers():
                #print('PROXIFY HANDLER: register: "lodify_mesh_data_exchange_80" @persistent (2.80)')
                bpy.app.handlers.depsgraph_update_post.append(lodify_mesh_data_exchange_80)
        else:
            if lodify_mesh_data_exchange_81 not in all_handlers():
                #print('PROXIFY HANDLER: register: "lodify_mesh_data_exchange_81" @persistent (2.81+)')
                bpy.app.handlers.depsgraph_update_post.append(lodify_mesh_data_exchange_81)

    if reg == 'unreg':
        if '2.80' in bpy.app.version_string:
            for h in all_handlers(): #so can also remove dupplicates
                if h == lodify_mesh_data_exchange_80:
                    bpy.app.handlers.depsgraph_update_post.remove(lodify_mesh_data_exchange_80)
                    #print('PROXIFY HANDLER: unregister: "lodify_mesh_data_exchange_80" (2.80)')
        else:
            for h in all_handlers(): #so can also remove dupplicates
                if h == lodify_mesh_data_exchange_81:
                    bpy.app.handlers.depsgraph_update_post.remove(lodify_mesh_data_exchange_81)
                    #print('PROXIFY HANDLER: unregister: "lodify_mesh_data_exchange_81" (2.81+)')


@bpy.app.handlers.persistent #for 2.80
def lodify_mesh_data_exchange_80(scene):
    analyse_and_exchange_data()

@bpy.app.handlers.persistent #for 2.81
def lodify_mesh_data_exchange_81(scene,desp): #new "optional" arg 
    analyse_and_exchange_data()


def analyse_and_exchange_data():
    """analyse and change data from ui list
    while storing data when recovery needed"""

    scn  = bpy.context.scene

    ###### - RENDERED

    if (scn.lod.p_rdv_switch) and ('RENDERED' in _all_viewports_shading_type()): #actions if rendered view detected
        c_print("LODIFY HANDLER: despgraph_changed: [rendered]")

        ops = []
        #loop over all data.objects if lod_original exist
        for ob in [o for o in bpy.data.objects if (o.type=='MESH') and (bool(o.lod_original))]:

            #if turn off is True, then use original and continue 
            if not (ob.lod_original.lod_enabled):
                if ob.data != ob.lod_original:
                    c_print(f"                      - lod system turned off, restoring original-data ''{ob.data.name}'' to ''{ob.lod_original.name}''")
                    #what i'm doing below is to counter a bug, idealy id need to run "ob.data = ob.lod_original" but due to a blender crash (rendered view mesh-data change from depsgraph = crash to desktop) i will disable the rendered view (once only)
                    ops.append(f'bpy.data.objects["{ob.name}"].data = bpy.data.meshes["{ob.lod_original.name}"]')

            else:
                #get info needed from ui list 
                tup = [ (s.ui_rdv,s.ui_lod) for s in ob.lod_original.lod_list if s.ui_rdv]

                #if tup list exist, then boolean rendered active
                if (tup):
                    if tup[0][1]:
                        if ob.data != tup[0][1]:
                            c_print(f"                      - changing mesh-data for ''{ob.data.name}'' to ''{tup[0][1].name}''")
                            #what i'm doing below is to counter a bug, idealy id need to run "ob.data = tup[0][1]" but due to a blender crash (rendered view mesh-data change from depsgraph = crash to desktop) i will disable the rendered view (once only)
                            ops.append(f'bpy.data.objects["{ob.name}"].data = bpy.data.meshes["{tup[0][1].name}"]')
        #bug counter 
        if bool(ops):
            toggle_shading(False)#shut down rendered view, cause crash if changing data
            for code in ops: exec(code)
            toggle_shading(True)#restore (only support one rendered view, if multiple, only restore last one)
    

    ###### - NOT RENDERED 

    else: #actions outside rendered view 
        c_print("LODIFY HANDLER: despgraph_changed: [not rendered]")

        #loop over all data.objects if lod_original exist
        for ob in [o for o in bpy.data.objects if (o.type=='MESH') and (o.lod_original!=None)]:

            #if turn off is True, then use original and continue 
            if not (ob.lod_original.lod_enabled):
                if ob.data != ob.lod_original:
                    c_print(f"                      - lod system turned off, restoring original-data")
                    ob.data = ob.lod_original
                continue 

            #get info needed from ui list 
            tup = [ (s.ui_dsp,s.ui_lod) for s in ob.lod_original.lod_list if s.ui_dsp]

            #if tup list exist, then boolean display active
            if (tup): 
                if tup[0][1]:
                    if ob.data != tup[0][1]:
                        c_print(f"                      - changing mesh-data for ''{ob.data.name}'' to ''{tup[0][1].name}''")
                        ob.data = tup[0][1]

            #else no active display and replace data back to original
            else:
                if ob.data != ob.lod_original:
                    c_print(f"                      - restoring original data for ''{ob.data.name}'' back to ''{ob.lod_original.name}''")
                    ob.data = ob.lod_original
    return None 



# oooooooooooo  o8o                        oooo       ooooooooo.                               .o8
# `888'     `8  `"'                        `888       `888   `Y88.                            "888
#  888         oooo  ooo. .oo.    .oooo.    888        888   .d88'  .ooooo.  ooo. .oo.    .oooo888   .ooooo.  oooo d8b
#  888oooo8    `888  `888P"Y88b  `P  )88b   888        888ooo88P'  d88' `88b `888P"Y88b  d88' `888  d88' `88b `888""8P
#  888    "     888   888   888   .oP"888   888        888`88b.    888ooo888  888   888  888   888  888ooo888  888
#  888          888   888   888  d8(  888   888        888  `88b.  888    .o  888   888  888   888  888    .o  888
# o888o        o888o o888o o888o `Y888""8o o888o      o888o  o888o `Y8bod8P' o888o o888o `Y8bod88P" `Y8bod8P' d888b



def reg_unreg_deps_render(reg):
    """reg/unreg actions before and after F12 render"""
    if reg == 'reg':
        if lodify_pre_render  not in all_handlers():
            #print('LODIFY HANDLER: register: "lodify_pre_render" @persistent')
            bpy.app.handlers.render_pre.append (lodify_pre_render )
        if lodify_post_render not in all_handlers():
            #print('LODIFY HANDLER: register: "lodify_post_render" @persistent')
            bpy.app.handlers.render_post.append(lodify_post_render)

    if reg == 'unreg':
        for h in all_handlers():
            if h == lodify_pre_render:
                bpy.app.handlers.render_pre.remove (lodify_pre_render)
                #print('LODIFY HANDLER: unregister: "lodify_pre_render"')
            if h == lodify_post_render:
                bpy.app.handlers.render_post.remove(lodify_post_render)
                #print('LODIFY HANDLER: unregister: "lodify_post_render"')


@bpy.app.handlers.persistent
def lodify_pre_render(scene):
    """pre render actions"""
    scn = bpy.context.scene
    if scn.lod.p_rdf_switch:
        c_print("LODIFY HANDLER: [pre F12 render]")

        #loop over all data.objects if lod_list exist
        for ob in [o for o in bpy.data.objects if (o.type=='MESH') and (o.lod_original!=None)]:

            #if turn off is True, then use original and continue 
            if not (ob.lod_original.lod_enabled):
                if ob.data != ob.lod_original:
                    c_print(f"                      - lod system turned off, retoring to original data")
                    ob.data = ob.lod_original
                continue

            #get info needed from ui list 
            tup = [ (s.ui_rdf,s.ui_lod) for s in ob.lod_original.lod_list if s.ui_rdf]

            #if tup list exist, then boolean display active
            if (tup): 
                if tup[0][1]:
                    if ob.data != tup[0][1]:
                        c_print(f"                      - changing display data for ''{ob.name}'' to ''{tup[0][1].name}''")
                        ob.data = tup[0][1]

@bpy.app.handlers.persistent
def lodify_post_render(scene):
    """post render actions"""
    scn = bpy.context.scene
    c_print("LODIFY HANDLER: [post F12 render]")

    #lead to a cycle error msg but everything still works fine
    if scn.lod.p_tor_switch: 
        c_print("                      - turning off all rendered view")
        #change back lods to solid view status
        quit_rendered_shading()

    if scn.lod.p_rdf_switch:
        #always disable rendered view after final render. anoying anyway.. 
        analyse_and_exchange_data()


###########################################################################################
#
# ooooooooo.                                                        .    o8o
# `888   `Y88.                                                    .o8    `"'
#  888   .d88' oooo d8b  .ooooo.  oo.ooooo.   .ooooo.  oooo d8b .o888oo oooo   .ooooo.   .oooo.o
#  888ooo88P'  `888""8P d88' `88b  888' `88b d88' `88b `888""8P   888   `888  d88' `88b d88(  "8
#  888          888     888   888  888   888 888ooo888  888       888    888  888ooo888 `"Y88b.
#  888          888     888   888  888   888 888    .o  888       888 .  888  888    .o o.  )88b
# o888o        d888b    `Y8bod8P'  888bod8P' `Y8bod8P' d888b      "888" o888o `Y8bod8P' 8""888P'
#                                  888
#                                 o888o
###########################################################################################

############ Ui List Props 

#v# update make sure disable boolean if remove
def ui_lod_upd(self,context):
    if not self.ui_lod: self.ui_rdf = self.ui_rdv = self.ui_dsp = False
    return None
#v# update make sure only one boolean active
def ui_dsp_upd(self,context):
    if self.ui_dsp == True: only_one_prop(self.id_data, self.ui_idx, "ui_dsp")
    return None
#v# update make sure only one boolean active
def ui_rdv_upd(self,context):
    if self.ui_rdv == True: only_one_prop(self.id_data, self.ui_idx, "ui_rdv")
    return None
#v# update make sure only one boolean active
def ui_rdf_upd(self,context):
    if self.ui_rdf == True: only_one_prop(self.id_data, self.ui_idx, "ui_rdf")
    return None
#v# update make sure only one boolean active
class LODIFY_props_list(bpy.types.PropertyGroup):
    #name   : StringProperty() -> Instantiated by default
    ui_idx : bpy.props.IntProperty(description='UI List Index') #carrefull idx = list[i] +1
    ui_lod : bpy.props.PointerProperty(type=bpy.types.Mesh,description='Level of Detail mesh-data' ,update=ui_lod_upd)
    #Booleans used for the Mesh-data exchange system (see in handlers) 
    ui_dsp : bpy.props.BoolProperty(default=False,description="set this mesh-data as active Lod in the viewport only"      ,update=ui_dsp_upd)
    ui_rdv : bpy.props.BoolProperty(default=False,description="set this mesh-data as active Lod in the rendered view only" ,update=ui_rdv_upd)
    ui_rdf : bpy.props.BoolProperty(default=False,description="set this mesh-data as active Lod in the final render only"  ,update=ui_rdf_upd)

############ Scene props 

class LODIFY_props_scn(bpy.types.PropertyGroup):
    #enable switching
    p_rdf_switch : bpy.props.BoolProperty(default=True,description='automatically change the LOD on final render')
    p_rdv_switch : bpy.props.BoolProperty(default=True,description='automatically change the LOD on rendered view')
    #switch behaviors
    p_tor_switch : bpy.props.BoolProperty(default=False,description='turn off all rendered view after final render')
    #props for devs usage  
    p_dev_info   : bpy.props.BoolProperty(default=False,description='display more infos in the panel (for devs)')
    p_dev_print  : bpy.props.BoolProperty(default=False,description='display more infos in the console (for devs)')



def reg_unreg_props(reg):
    """register/unregister all created props"""
    if reg == 'reg':
        #mesh
        bpy.types.Mesh.lod_list       = bpy.props.CollectionProperty(type=LODIFY_props_list)
        bpy.types.Mesh.lod_list_index = bpy.props.IntProperty()
        bpy.types.Mesh.lod_enabled    = bpy.props.BoolProperty(default=False,description='Enable the lod system for this mesh.')
        #scene
        bpy.types.Scene.lod           = bpy.props.PointerProperty(type=LODIFY_props_scn)
        #used to restore data
        bpy.types.Object.lod_original = bpy.props.PointerProperty(type=bpy.types.Mesh,description='Original Mesh-Data name, to restore when no more lods active')
    
    if reg == 'unreg':
        del bpy.types.Mesh.lod_list
        del bpy.types.Mesh.lod_list_index
        del bpy.types.Scene.lod
        del bpy.types.Object.lod_original


###########################################################################################
#
# ooooooooo.                         o8o               .
# `888   `Y88.                       `"'             .o8
#  888   .d88'  .ooooo.   .oooooooo oooo   .oooo.o .o888oo  .ooooo.  oooo d8b
#  888ooo88P'  d88' `88b 888' `88b  `888  d88(  "8   888   d88' `88b `888""8P
#  888`88b.    888ooo888 888   888   888  `"Y88b.    888   888ooo888  888
#  888  `88b.  888    .o `88bod8P'   888  o.  )88b   888 . 888    .o  888
# o888o  o888o `Y8bod8P' `8oooooo.  o888o 8""888P'   "888" `Y8bod8P' d888b
#                        d"     YD
#                        "Y88888P'
#
###########################################################################################

classes = (
            #--------------------operators
            LODIFY_OT_list_actions,
            LODIFY_OT_clear_list,
            LODIFY_OT_docs,
            LODIFY_OT_data_refresh,
            LODIFY_OT_create_backup,
            LODIFY_OT_restore_backup,
            LODIFY_MT_restore_backup,
            LODIFY_OT_auto_setup_op,
            LODIFY_OT_auto_setup_dialog,
            LODIFY_OT_cleanse_data,
            LODIFY_OT_clear_by_index,
            LODIFY_MT_clear_by_index,
            #--------------------drawing
            LODIFY_UL_items,
            LODIFY_PT_objectList,
            LODIFY_OT_dialog,
            LODIFY_MT_operators_menu,
            #--------------------props
            LODIFY_props_list,
            LODIFY_props_scn,
          )

def register():
    from bpy.utils import register_class
    #classes
    for cls in classes: register_class(cls)
    #properties
    reg_unreg_props('reg')
    #despgraph post
    reg_unreg_deps_post('reg')
    #post & pre final render
    reg_unreg_deps_render('reg')

def unregister():
    from bpy.utils import unregister_class
    #classes
    for cls in reversed(classes): unregister_class(cls)
    #properties
    reg_unreg_props('unreg')
    #despgraph post
    reg_unreg_deps_post('unreg')
    #post & pre final render
    reg_unreg_deps_render('unreg')