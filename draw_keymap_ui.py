from bpy.props import *

from collections.abc import Callable
from typing import Union, Any, Optional, Literal
from bpy.types import Context, UILayout, KeyMapItem

SubKeyTypeType = Union[
	Literal["any"], Literal["shift_ui"], Literal["ctrl_ui"],
	Literal["alt_ui"], Literal["oskey_ui"], Literal["key_modifier"]
]

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
	"""
	キーバインド設定UIにおける、キー設定の詳細部分の表示を作成する

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
	"""
	キーバインド設定UIの第2列である、オペレーターの設定とキー設定の詳細が表示される列を作成する

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

	draw_key_input(cls, context, R_half, keyitem)

	if keyitem.name != "":
		addtional_row = box.row()
		addtional_row.template_keymap_item_properties(keyitem)