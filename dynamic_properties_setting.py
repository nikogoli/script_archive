import bpy
from bpy.props import *

from bpy.types import Context, UILayout


bl_info = {
    "name": "Dynamic-property-setting Experimtents",
    "author": "nikogoli",
    "version": (0, 1),
    "blender": (3, 3, 0),
    "location": "None",
    "description": "Experimtents",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Custom"
}

# ----- draw helper ---------------
def indented_layout( context: Context, layout: UILayout, level = 0, indent_width = 16):
    if level == 0:
        return layout
    else:
        indent = level * indent_width / context.region.width
        split = layout.split(factor=indent)
        _col = split.column()
        col = split.column()
        return col


# ----- functions -----------------
def prop_operator_search_items(self, context, edit_tect):
    items = []
    for mod in dir(bpy.ops):
        for op in dir(getattr(bpy.ops, mod)):
            name = mod + '.' + op
            items.append(name)
    return items


def get_operator(name):
    split = name.split('.')
    op = None
    if len(split) == 2:
        m, o = split
        if m in dir(bpy.ops):
            mod = getattr(bpy.ops, m)
            if o in dir(mod):
                op = getattr(mod, o)
    return op


def prop_from_struct(prop):
    def set_base_dict(prop):
        dict = {
            'name': prop.name,
            'description': prop.description,
            'subtype': prop.subtype
        }
        options = set()
        if prop.is_hidden:
            options.add('HIDDEN')
        if prop.is_animatable:
            options.add('ANIMATABLE')
        if prop.is_enum_flag:
            options.add('ENUM_FLAG')
        dict['options'] = options
        return dict

    def create_bool_prop(prop):
        attrs = set_base_dict(prop)
        if prop.array_length > 0:
            attrs['default'] = tuple(prop.default_array)
            attrs['size'] = prop.array_length
            return BoolVectorProperty(**attrs)
        else:
            attrs['default'] = prop.default
            return BoolProperty(**attrs)

    def create_int_prop(prop):
        attrs = set_base_dict(prop)
        attrs['min'] = prop.hard_min
        attrs['max'] = prop.hard_max
        attrs['soft_min'] = prop.soft_min
        attrs['soft_max'] = prop.soft_max
        attrs['step'] = prop.step
        if prop.array_length > 0:
            attrs['default'] = tuple(prop.default_array)
            attrs['size'] = prop.array_length
            return IntVectorProperty(**attrs)
        else:
            attrs['default'] = prop.default
            return IntProperty(**attrs)

    def create_float_prop(prop):
        attrs = set_base_dict(prop)
        attrs['min'] = prop.hard_min
        attrs['max'] = prop.hard_max
        attrs['soft_min'] = prop.soft_min
        attrs['soft_max'] = prop.soft_max
        attrs['step'] = prop.step
        attrs['precision'] = prop.precision
        attrs['unit'] = prop.unit
        if prop.array_length > 0:
            attrs['default'] = tuple(prop.default_array)
            attrs['size'] = prop.array_length
            return FloatVectorProperty(**attrs)
        else:
            attrs['default'] = prop.default
            return FloatProperty(**attrs)

    def create_string_prop(prop):
        attrs = set_base_dict(prop)
        attrs['default'] = prop.default		
        attrs['maxlen'] = prop.length_max
        return StringProperty(**attrs)

    def create_enum_prop(prop):
        attrs = set_base_dict(prop)
        attrs.pop("subtype")
        defau = prop.default if prop.default != "" else prop.enum_items[0].identifier
        attrs['default'] = defau if not prop.is_enum_flag else set([defau])
        attrs['items'] = tuple(
            [(p.identifier, p.name, p.description, p.icon, p.value) for p in prop.enum_items]
        )
        return EnumProperty(**attrs)

    if prop.type == "BOOLEAN":
        return create_bool_prop(prop)
    elif prop.type == "INT":
        return create_int_prop(prop)
    elif prop.type == "FLOAT":
        return create_float_prop(prop)
    elif prop.type == "STEING":
        return create_string_prop(prop)
    elif prop.type == "ENUM":
        return create_enum_prop(prop)
    else:
        return None


def dynamic_prop_setter(self, context):
    op = get_operator(self.name)
    if op == None:
        return
    bl_rna = op.get_rna_type()
    props = [p for p in bl_rna.properties if p.identifier != 'rna_type']
    for prop in props:
        base_name = self.name.replace(".", "__")
        name =  f"{base_name}__{prop.identifier}"
        bl_prop = prop_from_struct(prop)
        setattr(ExperimentOp, name, bl_prop)


# ----- property class --------------
class ExperimentOp(bpy.types.PropertyGroup):
    name: StringProperty(name="オペレーター名", default="",
                        update=dynamic_prop_setter, search=prop_operator_search_items )
    show_expanded: BoolProperty( name='Show Details', default=True)

    def draw(self, context:Context, layout:UILayout):
        base = layout.column()
        row_1 = base.row()

        [R1_icon, R1_label] = [row_1.row() for i in range(2)]
        icon = 'TRIA_DOWN' if self.show_expanded else 'TRIA_RIGHT'
        R1_icon.prop(self, "show_expanded", text='', icon=icon, emboss=False)
        R1_label.prop(self, "name")

        if self.show_expanded:
            indented = indented_layout(context, base, 1).box()
            if self.name != "":
                for name in [p for p in dir(self) if p.startswith(self.name.replace(".", "__")) ]:
                    indented.prop(self, name)


# ----- preference --------------------
class AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __name__
    operators: CollectionProperty( name='Operator', type=ExperimentOp )

    def draw(self, context: Context):
        base: UILayout = self.layout.column()
        for op in self.operators:
            op.draw(context, base)

    def prop_restore(self):
        for item in self.operators:
            dynamic_prop_setter(item, bpy.context)

#---------------------------------------------------

classes = [
    ExperimentOp,
    AddonPrefs
]

@bpy.app.handlers.persistent
def load_handler(dummy):
    prefs = bpy.context.preferences.addons[__name__].preferences
    prefs.prop_restore()		


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    prefs = bpy.context.preferences.addons[__name__].preferences
    items = prefs.operators
    if len(items) == 0:
        for i in range(3):
            items.add()
    bpy.app.handlers.load_post.append(load_handler)
        

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.app.handlers.load_post.remove(load_handler)


if __name__ == "__main__":
    register()