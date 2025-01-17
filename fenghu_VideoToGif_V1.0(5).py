import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import re

# 默认输出目录
DEFAULT_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "output")

# 确保默认目录存在
if not os.path.exists(DEFAULT_OUTPUT_DIR):
    os.makedirs(DEFAULT_OUTPUT_DIR)

def sanitize_filename(filename):
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 限制文件名长度（考虑Windows路径长度限制）
    return filename[:200]

def convert_to_gif(input_files, output_dir, fps, scale_width, setpts, dither, bayer_scale, palette_mode, saturation, contrast, brightness, enable_color_adjust):
    os.makedirs(output_dir, exist_ok=True)
    successful_conversions = 0

    for video_path in input_files:
        if not os.path.exists(video_path):
            messagebox.showwarning("警告", f"文件 {video_path} 不存在。")
            continue

        if not (video_path.lower().endswith(".mp4") or video_path.lower().endswith(".mov")):
            messagebox.showwarning("警告", f"文件 {video_path} 不是 MP4 或 MOV 格式，已跳过。")
            continue

        try:
            filename = os.path.basename(video_path)
            name, _ = os.path.splitext(filename)
            
            # 合法化文件名
            sanitized_name = sanitize_filename(name)
            
            # 创建更简洁的输出文件名
            output_suffix = f"_fps{fps}_w{scale_width}_sp{setpts.replace('*', 'x')}"
            base_output_name = os.path.join(output_dir, f"{sanitized_name}{output_suffix}")
            
            palette_path = os.path.join(output_dir, f"{sanitized_name}_palette.png")

            file_index = 1
            while os.path.exists(f"{base_output_name}_{file_index}.gif"):
                file_index += 1

            output_gif = f"{base_output_name}_{file_index}.gif"

            # 生成调色板
            subprocess.run([
                "ffmpeg", "-i", video_path,
                "-vf", f"setpts={setpts},fps={fps},scale={scale_width}:-1:flags=lanczos,palettegen=stats_mode={palette_mode}",
                "-y", palette_path
            ], check=True)

            # 根据复选框状态构建 filter_complex
            if enable_color_adjust:
                filter_complex = (
                    f"setpts={setpts},"
                    f"fps={fps},"
                    f"scale={scale_width}:-1:flags=lanczos,"
                    f"colorbalance=rs={saturation}:gs={saturation}:bs={saturation}:"
                    f"rm={contrast}:gm={contrast}:bm={contrast}:"
                    f"rh={brightness}:gh={brightness}:bh={brightness}[x];"
                    f"[x][1:v]paletteuse=dither={dither}:bayer_scale={bayer_scale}"
                )
            else:
                filter_complex = (
                    f"setpts={setpts},"
                    f"fps={fps},"
                    f"scale={scale_width}:-1:flags=lanczos[x];"
                    f"[x][1:v]paletteuse=dither={dither}:bayer_scale={bayer_scale}"
                )

            # 生成 GIF
            subprocess.run([
                "ffmpeg", "-i", video_path, "-i", palette_path,
                "-filter_complex", filter_complex,
                output_gif
            ], check=True)

            if os.path.exists(palette_path):
                os.remove(palette_path)

            successful_conversions += 1
        except subprocess.CalledProcessError as e:
            messagebox.showerror("错误", f"处理文件 {filename} 时发生错误：{e}")
        except Exception as e:
            messagebox.showerror("未知错误", f"未知错误：{e}")

    if successful_conversions > 0:
        messagebox.showinfo("完成", f"成功转换 {successful_conversions} 个文件。")
    else:
        messagebox.showinfo("完成", "没有成功转换任何文件。")

def browse_output():
    try:
        # 获取当前路径并打印调试信息
        current_path = os.getcwd()
        print(f"当前工作目录: {current_path}")
        
        output_dir = filedialog.askdirectory()
        if output_dir:
            try:
                # 转换为绝对路径
                output_dir = os.path.abspath(output_dir)
                print(f"选择的输出目录: {output_dir}")
                
                # 检查目录是否存在
                if not os.path.exists(output_dir):
                    messagebox.showerror("错误", "所选目录不存在")
                    return None
                
                # 检查写入权限
                if not os.access(output_dir, os.W_OK):
                    messagebox.showerror("错误", "没有写入权限")
                    return None
                
                # 创建output子文件夹
                output_folder = os.path.join(output_dir, "output")
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)
                    print(f"已创建output文件夹: {output_folder}")
                
                # 更新输入框
                output_entry.delete(0, tk.END)
                output_entry.insert(0, output_folder)
                
                return output_folder
                
            except PermissionError:
                messagebox.showerror("错误", "没有权限访问所选目录")
                return None
            except Exception as e:
                messagebox.showerror("错误", f"发生错误: {str(e)}")
                return None
    except Exception as e:
        messagebox.showerror("错误", f"浏览目录时发生错误: {str(e)}")
        return None
        
    return None

def start_conversion():
    output_dir = output_entry.get()
    fps = fps_entry.get()
    scale_width = scale_width_entry.get()
    setpts = setpts_entry.get()
    dither = dither_var.get()
    bayer_scale = bayer_scale_entry.get()
    palette_mode = palette_mode_var.get()
    saturation = saturation_entry.get()
    contrast = contrast_entry.get()
    brightness = brightness_entry.get()
    enable_color_adjust = enable_color_adjust_var.get()

    if not input_files:
        messagebox.showwarning("警告", "请拖放 MP4 或 MOV 文件进行转换。")
        return

    if not output_dir:
        messagebox.showwarning("警告", "请确保输出目录已选择。")
        return

    try:
        fps = int(fps)
        scale_width = int(scale_width)
        bayer_scale = int(bayer_scale)
        saturation = float(saturation)
        contrast = float(contrast)
        brightness = float(brightness)
    except ValueError:
        messagebox.showwarning("警告", "帧速率、宽度、bayer_scale 必须是整数，饱和度、对比度和亮度必须是浮点数。")
        return

    convert_to_gif(input_files, output_dir, fps, scale_width, setpts, dither, bayer_scale, palette_mode, saturation, contrast, brightness, enable_color_adjust)

def drop(event):
    global input_files
    raw_data = event.data.strip()
    if raw_data.startswith("{") and raw_data.endswith("}"):
        new_files = [path.strip("{}") for path in raw_data.split("} {")]
    else:
        new_files = raw_data.split()

    input_files.extend(new_files)
    file_list.delete(0, tk.END)
    for file in input_files:
        file_list.insert(tk.END, file)

def clear_list():
    global input_files
    input_files = []
    file_list.delete(0, tk.END)

def delete_selected():
    global input_files
    selected_indices = file_list.curselection()
    for index in reversed(selected_indices):
        del input_files[index]
        file_list.delete(index)

root = TkinterDnD.Tk()
root.title("MP4/MOV 转 GIF")

input_files = []

frame_top = tk.LabelFrame(root, text="文件列表", padx=10, pady=10)
frame_top.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
file_list = tk.Listbox(frame_top, width=60, height=12)
file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
file_list.drop_target_register(DND_FILES)
file_list.dnd_bind('<<Drop>>', drop)
scrollbar = tk.Scrollbar(frame_top, orient=tk.VERTICAL, command=file_list.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
file_list.config(yscrollcommand=scrollbar.set)

frame_middle = tk.LabelFrame(root, text="输出目录", padx=10, pady=10)
frame_middle.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

output_entry = tk.Entry(frame_middle, width=50)
output_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
output_entry.insert(0, DEFAULT_OUTPUT_DIR)
browse_button = tk.Button(frame_middle, text="浏览", command=browse_output)
browse_button.grid(row=0, column=1, padx=5, pady=5)

frame_params = tk.LabelFrame(root, text="参数设置", padx=10, pady=10)
frame_params.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

params = [
    ("帧速率:", "10"), ("GIF 宽度:", "750"), ("视频加速因子:", "1*PTS"),
    ("抖动模式:", "floyd_steinberg"), ("Bayer Scale:", "3"), ("调色板模式:", "full"),
    ("饱和度:", "0.0"), ("对比度:", "0.0"), ("亮度:", "0.0")
]

entries = []
for i, (label, default) in enumerate(params):
    row, col = divmod(i, 3)
    tk.Label(frame_params, text=label).grid(row=row, column=col * 2, padx=5, pady=5, sticky="e")
    if label in ["抖动模式:", "调色板模式:"]:
        var = tk.StringVar(value=default)
        menu = tk.OptionMenu(frame_params, var, "none", "floyd_steinberg", "sierra2", "bayer") if "抖动" in label else tk.OptionMenu(frame_params, var, "diff", "full")
        menu.grid(row=row, column=col * 2 + 1, padx=5, pady=5, sticky="w")
        entries.append(var)
    else:
        entry = tk.Entry(frame_params)
        entry.grid(row=row, column=col * 2 + 1, padx=5, pady=5, sticky="ew")
        entry.insert(0, default)
        entries.append(entry)

fps_entry, scale_width_entry, setpts_entry, dither_var, bayer_scale_entry, palette_mode_var, saturation_entry, contrast_entry, brightness_entry = entries

# 添加颜色调整启用复选框
enable_color_adjust_var = tk.BooleanVar(value=False)
color_adjust_cb = tk.Checkbutton(frame_params, text="启用颜色调整", variable=enable_color_adjust_var)
color_adjust_cb.grid(row=len(params), column=0, columnspan=2, padx=5, pady=5)

frame_bottom = tk.Frame(root)
frame_bottom.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

clear_button = tk.Button(frame_bottom, text="清空列表", command=clear_list)
clear_button.pack(side=tk.LEFT, padx=10)

delete_button = tk.Button(frame_bottom, text="删除选中文件", command=delete_selected)
delete_button.pack(side=tk.LEFT, padx=10)

start_button = tk.Button(root, text="开始转换", command=start_conversion)
start_button.grid(row=4, column=0, columnspan=4, padx=10, pady=10)

root.mainloop()