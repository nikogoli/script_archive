import bpy
from bpy.props import *

from bpy.types import Context, UILayout, Event


bl_info = {
	"name": "Animation on Text Editor",
	"author": "nikogoli",
	"version": (0, 1),
	"blender": (3, 3, 0),
	"location": "None",
	"description": "Animation on Text Editor",
	"warning": "",
	"support": "TESTING",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Custom"
}



class WM_OT_puipui_operator(bpy.types.Operator):
	bl_idname = "wm.puipui_operator"
	bl_label = "Start PUI PUI"
	bl_options = {'REGISTER', 'UNDO'}

	textdata_name: StringProperty(name="Name", default="PUI_PUI")
	order : StringProperty(name="next AA", default="LEFT,MIDDLE,RIGHT,MIDDLE")
	win_count: IntProperty(name="window counts", default=1)
	
	_text_area = None
	_timer = None

	def modal(self, context, event):
		if len(context.window_manager.windows) < self.win_count:
			print("end")
			bpy.data.texts[self.textdata_name].clear()
			context.window_manager.event_timer_remove(WM_OT_puipui_operator._timer)
			WM_OT_puipui_operator._timer = None
			return {'FINISHED'}
		if event.type == 'TIMER':
			order_lis = self.order.split(",")
			if order_lis[0] == "LEFT":
				next_aa = LEFT
			elif order_lis[0] == "MIDDLE":
				next_aa = MIDDLE
			else:
				next_aa = RIGHT
			override = context.copy()
			override['area'] = WM_OT_puipui_operator._text_area
			bpy.data.texts[self.textdata_name].clear()
			bpy.data.texts[self.textdata_name].write("\n".join(next_aa))
			bpy.ops.text.jump(override, line=1)
			self.order = ",".join(order_lis[1:] + [order_lis[0]])
		return {'RUNNING_MODAL'}


	def invoke(self, context, event):
		bpy.ops.wm.window_new()
		new_win = context.window_manager.windows[-1]
		text_area = new_win.screen.areas[-1]
		text_area.type = 'TEXT_EDITOR'
		WM_OT_puipui_operator._text_area = text_area

		if self.textdata_name in bpy.data.texts:
			text_area.spaces[0].text = bpy.data.texts[self.textdata_name]
		else:
			text_area.spaces[0].text = bpy.data.texts.new(name=self.textdata_name)
		text_area.spaces[0].text.clear()
		text_area.spaces[0].text.write("\n".join(MIDDLE))
		self.win_count = len(context.window_manager.windows)

		WM_OT_puipui_operator._timer = context.window_manager.event_timer_add(0.5, window=context.window)
		context.window_manager.modal_handler_add(self)
		return {'RUNNING_MODAL'}


class AddonPrefs(bpy.types.AddonPreferences):
	bl_idname = __name__

	def draw(self, context: Context):
		base: UILayout = self.layout.column()
		base.row().operator(WM_OT_puipui_operator.bl_idname)
		

#---------------------------------------------------


classes = [
	WM_OT_puipui_operator,
	AddonPrefs
]


def register():
	for cls in classes:
		bpy.utils.register_class(cls)


def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)


if __name__ == "__main__":
	register()

# r"素材は 'https://seesaawiki.jp/asciiart/d/PUI%20PUI%20%A5%E2%A5%EB%A5%AB%A1%BC'のものを調整
MIDDLE = [
	"",
	"",
	"",
	"",
	"                  ,． ’''二二''’～‐､   /￣￣ Y",
	"            _､‐’’゛／               ＼/::::::}",
	"         /￣ヽ  : !_ ....-----------｀ヾ....ノ",
	"        人 :::Y:｀¨¨´ : __’⌒ヽ｡--､::::’ ,",
	"         /｀¨¨｀`::::::んハ    VＪﾊ::::::’,",
	"        { : ; ::::::::.乂シ    `--' ::::::’,",
	"        { ;:::::::＞’ﾞ´            ｀゛¨¨':}",
	"        { 乂:＞’ﾞ´                     `¨¨:",
	"        {＞’ﾞ´                            ;",
	"        八                   ヽノ        ,",
	"         人_                 _ノ        ／",
	"         /::::＼/￣￣＼__ ィ´_ソﾉﾞ＞‐-´￣Ｙ",
	"         {:::::{:::::::｀Y------く::/:::::/",
	"         乂___ノ乂::::::ノ        ｀乂:::／",
]


RIGHT = [
	"",
	"",
	"",
	"                  ,． ’''二二''’～‐､  |￣￣＼",
	"            _､‐’’゛／               ＼\\::::::\\",
	"      \\￣￣ヽ: :  !_....-----------｀ヾ ....ノ",
	"      人  :::Y: ｀¨¨´ : __’⌒ヽ｡--､::::’ ,",
	"        | ｀¨¨｀`::::::んハ    VＪﾊ::::::’,",
	"        { : ; ::::::::.乂シ    `--' ::::::’,",
	"        { ;:::::::＞’ﾞ´            ｀゛¨¨':}",
	"        { 乂:＞’ﾞ´                     `¨¨:",
	"        {＞’ﾞ´                            ;",
	"        八                   ヽノ        ,",
	"         人                  _ノ       ／",
	"         /::::＼/￣＼___  ィ´_ソﾉﾞ`、_／",
	"         {:::::{:::::::｀Y------く:/:::::＼",
	"         乂___ノ乂::::::ノ       ｀乂::::::}",
	""
]


LEFT= [
	"",
	"",
	"",
	"                    ,． ’''二二''’～‐､   ／￣￣}",
	"              _､‐’’゛／               ＼/:::::/",
	"         /￣￣| : : !_....----------- `ヾ....ノ",
	"         |    Y:｀¨¨´ : __’⌒ヽ｡--､:::::’ ,",
	"         /｀¨¨｀`::::::んハ    VＪﾊ::::::’,",
	"        { : ; ::::::::.乂シ    `--' ::::::’,",
	"        { ;:::::::＞’ﾞ´            ｀゛¨¨':}",
	"        { 乂:＞’ﾞ´                     `¨¨:",
	"        {＞’ﾞ´                            ;",
	"        八                   ヽノ        ,",
	"         人_                 _ノ        ／",
	"        /::::＼  _______  ィ´_ソﾉﾞ`＞‐‐-´￣＼",
	"       / ::::: /{:::::::｀Y------く::/:::::/",
	"       \\ ____ / 乂::::::ノ       ｀乂::::／",
	""
]