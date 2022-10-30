import bpy
import blf
from bpy.props import *
import math

from collections.abc import Callable
from typing import Union, Any, Optional, Literal
from bpy.types import Context, UILayout, KeyMapItem, Event

SubKeyTypeType = Union[
    Literal["any"], Literal["shift_ui"], Literal["ctrl_ui"],
    Literal["alt_ui"], Literal["oskey_ui"], Literal["key_modifier"]
]

SubKeyType = Union[
    Literal["Any"], Literal["Shit"], Literal["Ctrl"], Literal["Alt"], Literal["Cmd"]
]



bl_info = {
    "name": "3-Keys Shortcut",
    "author": "nikogoli",
    "version": (1, 0),
    "blender": (3, 3, 0),
    "location": "None",
    "description": "Custom shortcut for 3 keys",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Custom"
}

PIXEL_SIZE = 1.0


# ----- draw helper ---------------
def indented_layout( context: Context,
                    layout: UILayout,
                    level = 0,
                    indent_width = 16) -> UILayout:
    """	一定の距離だけ右にインデントされた UIlayout(column) を返す

    context (bpy.types.Context): context
    layout (bpy.types.UIlayout): 親となる UIlayout 要素
    level (int): インデントの階数. デフォルト 0.
    indent_width (int): インデントの幅. デフォルト 16 (全角空白で約3文字)
    """
    if level == 0:
        return layout
    else:
        indent = level * indent_width / context.region.width
        split = layout.split(factor=indent)
        _col = split.column()
        col = split.column()
        return col


def draw_main_row(	cls: Any,
                    constext: Context,
                    layout: UILayout,
                    keyitem: KeyMapItem,
                    split_factor = 0.5,
                    use_active = True,
                    expansion_prop: Optional[str] = "show_expanded",
                    custom_label: Optional[Callable[[str],str]] = None,
                    key_info_first = False,
                    show_remove_func = True,
                    custom_remove_fuc: Optional[str] = None,
                    custom_remove_prop: Optional[dict[str, Any]] = None) -> None:
    """
    キーバインド設定UIの第1列である、オペレーターの名前とキー設定が表示される列を作成する

    cls (Any): この関数を draw() 内部で呼び出すクラス (self)
    context (bpy.types.Context): context
    layout (bpy.types.UIlayout): 親となる UIlayout 要素
    keyitem (bpy.types.KeyMapItem): KeyMapItem
    split_factor (float (0~1)): オペレーター名表示部分が列全体に占める割合. デフォルト 0.5
    use_active (bool): キーバインドの有効化を変更するチェックボックス表示の有無. デフォルト True
    expansion_prop (str): 詳細表示の有無を決めるクラス変数の名前. デフォルト 'show_expanded'
    custom_label ( ( (str)->str ) | None ): オペレーター名の表示内容を操作する関数. デフォルト None
    key_info_first (bool): 表示順を逆にして「キー設定  オペレーター名」形式で表示する. デフォルト None
    show_remove_func (bool): 列の右端のキーバインドを削除するボタンの表示の有無. デフォルト True
    custom_remove_fuc (str): 独自オペレーターでキーバインドを削除する場合、その idname. デフォルト None
    custom_remove_prop (dict[str, Any]): 独自オペレーターでキーバインドを削除する場合、その引数名と引数の辞書. デフォルト None
    """
    def row_create(layout:UILayout, sc:int):
        row = layout.row()
        row.ui_units_x = sc
        return row

    main_row = layout.split(factor=split_factor)
    L_half = main_row.row()
    R_half = main_row.row()

    L_icon =  L_half.row() if expansion_prop else None
    L_checkbox =  L_half.row() if use_active else None
    if not key_info_first:
        L_label = L_half.row()
        [R_key1, R_key2] = [ row_create(R_half, sc) for sc in [ 1.1, 0.9] ]
    else:
        [R_key1, R_key2] = [ row_create(L_half, sc) for sc in [ 1.3, 0.7] ]
        L_label = R_half.row()
    R_button = R_half.row()

    if expansion_prop:
        icon = 'TRIA_DOWN' if getattr(cls, expansion_prop) else 'TRIA_RIGHT'
        L_icon.prop(cls, expansion_prop, text='', icon=icon, emboss=False)
    if use_active:
        L_checkbox.prop(keyitem, "active", text="", emboss=False)

    if custom_label:
        L_label.label(text = custom_label(keyitem.name))
    else:
        L_label.label(text = keyitem.name)

    R_key1.prop(keyitem, "map_type", text="")
    if keyitem.map_type == 'KEYBOARD':
        R_key2.prop(keyitem, "type", text="", full_event=True)
    elif keyitem.map_type == 'MOUSE':
        R_key2.prop(keyitem, "type", text="", full_event=True)
    elif keyitem.map_type == 'NDOF':
        R_key2.prop(keyitem, "type", text="", full_event=True)
    elif keyitem.map_type == 'TIMER':
        R_key2.prop(keyitem, "type", text="")
    else:
        R_key2.label()
    
    if show_remove_func:
        if custom_remove_fuc:
            op = R_button.operator(custom_remove_fuc, text="", icon='X' )
            if custom_remove_fuc:
                for prop,val in custom_remove_prop.items():
                    setattr(op, prop, val)
        else:
            if (not keyitem.is_user_defined) and keyitem.is_user_modified:
                op = R_button.operator("preferences.keyitem_restore", text="", icon='BACK')
            else:
                icon = 'TRACKING_CLEAR_BACKWARDS' if keyitem.is_user_defined else 'X'
                op = R_button.operator("preferences.keyitem_remove", text="", icon=icon)
            op.item_id = keyitem.id


def draw_key_input(	cls: Any,
                    context: Context,
                    layout: UILayout,
                    keyitem: KeyMapItem,
                    direction: Union[Literal["vertical"], Literal["horizontal"]] = "vertical",
                    excludes: Optional[list[SubKeyTypeType]] = None ) -> None:
    """キーバインド設定UIにおける、キー設定の詳細部分の表示を作成する

    cls (Any): この関数を draw() 内部で呼び出すクラス (self)
    context (bpy.types.Context): context
    layout (bpy.types.UIlayout): 親となる UIlayout 要素
    keyitem (bpy.types.KeyMapItem): KeyMapItem
    direction ("vertical" | "horizontal"): 表示方向. デフォルト vertical
    excludes ("any"|"shift_ui"|"ctrl_ui"|"alt_ui"|"oskey_ui"|"key_modifier"|None):
        補助キー設定のうちの表示しないもののリスト. デフォルト None
    """
    if direction == "vertical":
        base = layout.column()
        R_input_row1 = base.row()
        if keyitem.map_type in {'KEYBOARD', 'MOUSE'} and keyitem.value == 'CLICK_DRAG':
            R_input_row15 = base.row()
        else:
            R_input_row15 = None
        R_input_row2 = base.row()
    else:
        base = layout.split(factor=0.5)
        Left = base.column()
        Right = base.column()
        R_input_row1 = Left.row()
        if keyitem.map_type in {'KEYBOARD', 'MOUSE'} and keyitem.value == 'CLICK_DRAG':
            R_input_row15 = Left.row()
        else:
            R_input_row15 = None
        R_input_row2 = Right.row()
    
    if keyitem.map_type == 'KEYBOARD':
        [R1_1, R1_2, R1_3] = [ R_input_row1.row(align=True) for i in range(3) ]
        R1_1.prop(keyitem, "type", text="", event=True)
        R1_2.prop(keyitem, "value", text="")
        R1_3.prop(keyitem, "repeat", text="Repeat")
        R1_3.active = keyitem.value in {'ANY', 'PRESS'}
    elif keyitem.map_type in {'MOUSE'}:
        [R1_1, R1_2] = [ R_input_row1.row(align=True) for i in range(2) ]
        R1_1.prop(keyitem, "type", text="")
        R1_2.prop(keyitem, "value", text="")

    if keyitem.map_type in {'KEYBOARD', 'MOUSE'} and keyitem.value == 'CLICK_DRAG':
        R_input_row15.prop(keyitem, "direction")

    subs = ["any", "shift_ui", "ctrl_ui", "alt_ui", "oskey_ui","key_modifier"]
    if excludes and len(excludes) > 0:
        subs = [x for x in subs if x not in excludes]
    if len(subs) >= 5:
        R_input_row2.scale_x = 0.75
    for sub in subs:
        R = R_input_row2.row()
        if sub in ["any", "shift_ui", "ctrl_ui", "alt_ui"]:
            R.prop(keyitem, sub, toggle=True)
        elif sub == "oskey_ui":
            R.prop(keyitem, "oskey_ui", text="Cmd", toggle=True)
        else:
            R.prop(keyitem, "key_modifier", text="", event=True)


def draw_keymap_detail(	cls: Any,
                        context: Context,
                        layout: UILayout,
                        keyitem: KeyMapItem,
                        draw_for_left_blank: Optional[Callable[[Any, UILayout, KeyMapItem],None]] = None
                        ) -> None :
    """キーバインド設定UIの第2列である、オペレーターの設定とキー設定の詳細が表示される列を作成する

    cls (Any): この関数を draw() 内部で呼び出すクラス (self)
    context (bpy.types.Context): context
    layout (bpy.types.UIlayout): 親となる UIlayout 要素
    keyitem (bpy.types.KeyMapItem): KeyMapItem
    draw_for_left_blank ( (Any, UIlayout,KeyMapItem)->None) | None ):
        オペレーター設定部分の下の余白に適用される独自の draw() 関数. デフォルト None
    """
    box = layout.box()
    main_row = box.split(factor=0.4)
    L_half = main_row.column()
    R_half = main_row.column()

    L_idname = L_half.row()
    L_idname.prop(keyitem, 'idname', text='')
    if draw_for_left_blank:
        draw_for_left_blank(cls, L_half, keyitem)

    draw_key_input(cls, context, R_half, keyitem, excludes=["shift_ui", "key_modifier"])

    if keyitem.name != "":
        addtional_row = box.row()
        addtional_row.template_keymap_item_properties(keyitem)


# ----- functions -----------------
def key_to_string(item: KeyMapItem) -> str:
    """	KeyMapItem のキー設定から '[Shift] W' のような文字列を生成する

    item (bpy.types.KeyMapItem) : KeyMapItem
    """
    text = ""
    if item.shift_ui or item.shift == 1:
        text = "[Shift] " 
    if item.ctrl_ui or item.ctrl == 1:
        text += "[Ctrl] "
    if item.alt_ui or item.alt == 1:
        text += "[Alt] "
    if item.oskey_ui or item.oskey == 1:
        text += "[Cmd] "
    return text + item.type


def event_to_string(event: Event) -> str:
    """	Event のキー情報から '[Shift] W' のような文字列を生成する

    item (bpy.types.Event) : Event
    """
    text = ""	
    if event.shift:
        text = "[Shift] " 
    if event.ctrl:
        text += "[Ctrl] "
    if event.alt:
        text += "[Alt] "
    if event.oskey:
        text += "[Cmd] "
    return text + event.type


def reset_groups(context):
    """ OperatorItemGroup および OperatorItem の設定を初期設定に戻す

    context (bpy.types.Context) : context
    """
    prefs = context.preferences.addons[__name__].preferences
    prefs.op_items.clear()

    keymap = context.window_manager.keyconfigs.addon.keymaps.find(__name__)
    if keymap:
        context.window_manager.keyconfigs.addon.keymaps.remove(keymap)

    km_container = context.window_manager.keyconfigs.addon.keymaps.new(__name__)
    for key, angle, ax in [
        ["W", math.pi/4, "Y"], ["E", -math.pi/4, "Y"], ["R", math.pi/4, "Z"], ["T", -math.pi/4, "Z"]
    ]:
        op_item = prefs.op_items.add()
        keyitem = km_container.keymap_items.new('transform.rotate', key, "PRESS")
        op_item.idx = keyitem.id
        keyitem.properties.value = angle
        keyitem.properties.orient_axis = ax
        op_item.exec_context = 'EXEC_DEFAULT'


# ----- property class --------------
class OperatorItem(bpy.types.PropertyGroup):
    """ キー入力とそれに対応するオペレーターの設定

    show_expanded (bool) : 詳細表示の有無
    idx (int) : オペレーターが格納されている KeyMapItem の id. デフォルト -1
    execution_context (enum of Operator Context Items) : 'INVOKE_DEFAULT' など
    """
    show_expanded: BoolProperty( name='Show Details', default=False)
    idx: IntProperty(name="index", default=-1)
    exec_context: EnumProperty(
        name='Execution Context',
        items=[(s, s, '') for s in
               ['INVOKE_DEFAULT', 'INVOKE_REGION_WIN',
                'INVOKE_REGION_CHANNELS', 'INVOKE_REGION_PREVIEW',
                'INVOKE_AREA', 'INVOKE_SCREEN', 'EXEC_DEFAULT',
                'EXEC_REGION_WIN', 'EXEC_REGION_CHANNELS',
                'EXEC_REGION_PREVIEW', 'EXEC_AREA', 'EXEC_SCREEN']],
        default='INVOKE_DEFAULT'
    )

    def draw(self, context:Context, layout:UILayout):
        base = layout.column()
        base.context_pointer_set('group_item', self)
        item = context.window_manager.keyconfigs.addon.keymaps[__name__].keymap_items.from_id(self.idx)
        
        draw_main_row(
            self, context, base, item, use_active=False,
            custom_label=lambda name: name if name != "" else "未設定",
            key_info_first=True,
            custom_remove_fuc=WM_OT_keyitem_manipulate.bl_idname,
            custom_remove_prop={"method":"remove_item"}
        )

        if self.show_expanded:
            def draw_exec_context(self, layout, item):
                row = layout.row()
                row.prop(self, "exec_context", text='')
                row.active = (item.idname != "")

            draw_keymap_detail(self, context, base, item, draw_for_left_blank=draw_exec_context)


# ----- operator ---------------------
class WM_OT_keyitem_manipulate(bpy.types.Operator):
    """ OperatorItem  の追加/削除を行う

    method (str): 行う処理. add_item | remove_item | reset_items
    """
    bl_idname = "wm.keyitem_manipulate"
    bl_label = "Manipulate Key Map Item"

    method : StringProperty(name="Manipulation method", default="")	

    @classmethod
    def description(cls, context, properties):
        if properties.method == "reset_items": return "Reset oprators"
        elif properties.method == "add_item": return "Add new operator"
        elif properties.method == "remove_item": return "Remove this key's operator"


    def execute(self, context):
        keymap = context.window_manager.keyconfigs.addon.keymaps.find(__name__)
        if not keymap:
            return {'CANCELLED'}
        key_items = keymap.keymap_items
        
        if self.method == "add_item":
            keyitem = key_items.new('', "A", "PRESS")
            group_item = context.addon_pref.op_items.add()
            group_item.idx = keyitem.id
            
        elif self.method == "remove_item":
            group_item = context.group_item
            op_items = context.addon_pref.op_items
            i = list(op_items).index(group_item)
            op_items.remove(i)

            keyitem = key_items.from_id(group_item.idx)
            key_items.remove(keyitem)
        
        elif self.method == "reset_items":
            reset_groups(context)
        return {'FINISHED'}


class WM_OT_three_keys_operator(bpy.types.Operator):
    """ モーダルモードでキー入力を監視し、入力に対応するオペレーターを実行する

    handle: draw handler を格納するためのもの
    """
    bl_idname = "wm.three_keys_operator"
    bl_label = "Operator called by 3 keys"
    bl_options = {'REGISTER', 'UNDO'}

    handle = None

    def __init__(self):
        """
        handle : handler
        main_kmi : このオペレーターが登録された KeyMapItem
        name_dict: {str: {"op_item": OperatorItem, "key_item": bpy.types.KeyMapItem}}:
            OperatorItem に登録されているキー入力とそれに対応する KeyMapItem の辞書
        """
        self.handle = None
        self.main_kmi: Union[KeyMapItem, None] = None
        self.name_dict: Union[dict[str,dict[str,Union[OperatorItem, KeyMapItem]]], None] = None


    def my_callback(self, context):
        """ モーダルモードであることを示す表示を描画するためのカスタムの draw 関数
        """
        if (context.area.type == 'VIEW_3D' and context.region.type == 'WINDOW'):
            U = context.preferences
            dpi = U.system.dpi
            font_id = 0
            theme_style = U.ui_styles[0]
            blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
            blf.size(font_id, theme_style.widget.points, dpi)
            blf.position(font_id, 25, 50, 0)
            blf.draw(font_id, "Wait for input...")


    def draw_handler_add(self, context):
        if WM_OT_three_keys_operator.handle is None:
            WM_OT_three_keys_operator.handle = bpy.types.SpaceView3D.draw_handler_add(
                WM_OT_three_keys_operator.my_callback, (self, context), 'WINDOW', 'POST_PIXEL'
            )


    def draw_handler_remove(self, context):
        if WM_OT_three_keys_operator.handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                WM_OT_three_keys_operator.handle, 'WINDOW'
            )
            WM_OT_three_keys_operator.handle = None
            context.region.tag_redraw()


    def modal(self, context, event):
        if event.value == "RELEASE":
            self.draw_handler_remove(context)
            return {'CANCELLED'}
        elif event.value == "PRESS" and event.type == self.main_kmi.type:
            return {'RUNNING_MODAL'}
        elif event.value not in ["PRESS", "CLICK", "DOUBLE_CLICK", "CLICK_DRAG"]:
            return {'RUNNING_MODAL'}
        
        key_item = op_item = None

        anyed = "[Any] "+ event.type
        if anyed in self.name_dict:
            key_item = self.name_dict[anyed]["key_item"]
            op_item = self.name_dict[anyed]["op_item"]

        event_str = event_to_string(event)
        if key_item == None and event_str in self.name_dict:
            key_item = self.name_dict[event_str]["key_item"]
            op_item = self.name_dict[event_str]["op_item"]

        if key_item == None or op_item == None:
            self.draw_handler_remove(context)
            return {'CANCELLED'}
        else:
            split = key_item.idname.split('.')
            operator = None
            if len(split) == 2:
                m, o = split
                if m in dir(bpy.ops):
                    mod = getattr(bpy.ops, m)
                    if o in dir(mod):
                        operator = getattr(mod, o)
            if operator == None:
                self.draw_handler_remove(context)
                return {'CANCELLED'}

            self.draw_handler_remove(context)
            args = [op_item.exec_context, True]
            kwargs = {}
            for arg in dir(key_item.properties):
                if not arg.startswith("_") and arg not in ["bl_rna", "rna_type"]:
                    kwargs[arg] = getattr(key_item.properties, arg)
            retval = operator(*args, **kwargs)
            if 'RUNNING_MODAL' in retval:
                return retval			
            return {'FINISHED'}


    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.draw_handler_add(context)
        prefs:AddonPrefs = context.preferences.addons[__name__].preferences
        self.main_kmi = prefs._main_kmi
        base_key = " ".join(key_to_string(self.main_kmi).split(" ")[:-1])

        key_items = context.window_manager.keyconfigs.addon.keymaps[__name__].keymap_items
        keyname_dict = {}
        for item in prefs.op_items:
            kmi = key_items.from_id(item.idx)
            keyname_dict[f"{base_key} " + key_to_string(kmi)] =  { "op_item": item, "key_item": kmi}
        self.name_dict = keyname_dict
        context.region.tag_redraw()
        return {'RUNNING_MODAL'}


# ----- preference --------------------
class AddonPrefs(bpy.types.AddonPreferences):
    """ アドオン設定

    mode_groups: OperatorItemGroup を要素とする CollectionProperty
    """
    bl_idname = __name__

    op_items: CollectionProperty( name='Items', type=OperatorItem)
    _main_kmi = None

    def draw(self, context):
        layout: UILayout = self.layout.column()
        layout.context_pointer_set('addon_pref', self)
        (_map, item) = addon_keymaps[0]

        draw_main_row(self, context, layout, item, split_factor=0.3,
            use_active=False, expansion_prop=None,
            custom_label= lambda name: "モーダルモード移行キー", show_remove_func=False
        )
        draw_key_input(self, context, layout.box(), item, direction="horizontal")

        layout.separator()
        row = layout.split(factor=0.7)
        [R_label, R_resetbutton] = [row.row() for i in range(2)]
        R_label.label(text="キー設定")
        resetbutton = R_resetbutton.operator(WM_OT_keyitem_manipulate.bl_idname, text='Reset', icon='SHADERFX')
        resetbutton.method = "reset_items"

        for item in self.op_items:
            row = layout.row()
            item.draw(context, row)

        addbutton = layout.split(factor=0.3).operator(WM_OT_keyitem_manipulate.bl_idname, text='Add New', icon='ADD')
        addbutton.method = 'add_item'


#---------------------------------------

classes = [
     WM_OT_three_keys_operator,
    WM_OT_keyitem_manipulate,
    OperatorItem,
    AddonPrefs
]


addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new('3D View', space_type='VIEW_3D', region_type='WINDOW', modal=False)
        kmi = km.keymap_items.new(WM_OT_three_keys_operator.bl_idname, 'Q', 'PRESS', shift=1, head=True)
        addon_keymaps.append((km, kmi))
        AddonPrefs._main_kmi = kmi
    reset_groups(bpy.context)	


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    keymap = bpy.context.window_manager.keyconfigs.addon.keymaps.find(__name__)
    if keymap:
        bpy.context.window_manager.keyconfigs.addon.keymaps.remove(keymap)


if __name__ == "__main__":
    register()