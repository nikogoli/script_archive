import bpy
from bpy.props import *

from bpy.types import Context, UILayout, Event


bl_info = {
    "name": "Experimtents",
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


class ExperimentItem(bpy.types.PropertyGroup):
    text: StringProperty(name="Text", default="")
    
    def draw(self, context:Context, layout:UILayout):
        base = layout.column()
        base.context_pointer_set('exp_item', self) # .text 変更のために self へのアクセスを提供する

        R1 = base.split(factor=0.7)
        R1.prop(self, "text")
        R1.operator(WM_OT_expreimental_operator.bl_idname, text="Change", icon="GREASEPENCIL")


class WM_OT_expreimental_operator(bpy.types.Operator):
    bl_idname = "wm.expreimental_operator"
    bl_label = "Experiment operator"
    bl_options = {'REGISTER', 'UNDO'}

    win_count: IntProperty(name="window counts", default=1)
    textdata_name: StringProperty(name="Name", default="temporal_text")
    
    exp_item = None

    def modal(self, context: Context, event: Event):
        # ウィンドウの数が減っていた場合はテキストデータの中身を exp_item.text に書き込む
        if len(context.window_manager.windows) < self.win_count:
            text_d = bpy.data.texts[self.textdata_name]
            text_lines = [line.body for line in text_d.lines]
            self.exp_item.text = "\n".join([l for l in text_lines if not l.startswith("#")])
            
            # テキストデータを初期化 (データは ExperimentItem.text で保有し、テキストデータには保有させない)
            text_d.clear()
            self.win_count = 0
            self.exp_item = None
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


    def invoke(self, context: Context, event: Event):
        context.window_manager.modal_handler_add(self)

        # 新しいウィンドウを開き、それを取得し、その area をテキストエディタに変更する
        bpy.ops.wm.window_new()
        new_win = context.window_manager.windows[-1]
        text_area = new_win.screen.areas[-1]
        text_area.type = 'TEXT_EDITOR'

        self.win_count = len(context.window_manager.windows) # ウィンドウが増えた状態で数を記録
        self.exp_item = context.exp_item # modal() には context を持ち越せないので、self に退避させる

        if self.textdata_name in bpy.data.texts:
            text_area.spaces[0].text = bpy.data.texts[self.textdata_name]
        else:
            text_area.spaces[0].text = bpy.data.texts.new(name=self.textdata_name)
        
        # デフォルトおよび既存の text があればそれを書き込む
        text_area.spaces[0].text.write("# 記述終了後、このウィンドウを閉じてください\n")
        if self.exp_item.text != "":
            text_area.spaces[0].text.write(self.exp_item.text)
        return {'RUNNING_MODAL'}


class AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __name__

    text: StringProperty(name="text", default="")
    exp_items: CollectionProperty( name='Items', type=ExperimentItem)

    def draw(self, context: Context):
        base: UILayout = self.layout.column()
        for item in self.exp_items:
            item.draw(context, base)
        

#---------------------------------------------------


classes = [
    ExperimentItem,
    WM_OT_expreimental_operator,
    AddonPrefs
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    prefs = bpy.context.preferences.addons[__name__].preferences
    items = prefs.exp_items
    for i in range(3):
        items.add()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()