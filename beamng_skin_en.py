import os
import shutil
import json
import re
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- BEAMNG THEME CONFIG ---
BNG_ORANGE = "#ff6600"
BNG_BG_DARK = "#1c1c1c"
BNG_BG_CARD = "#2a2a2a"
BNG_TEXT = "#e2e2e2"
BNG_TEXT_DIM = "#999999"
BNG_WHITE = "#ffffff"

VEHICLES = {
    "Gavril D-Series (Pickup)": "pickup",
    "Bruckell Bastion": "bastion",
    "Bruckell LeGran": "legran",
    "Bruckell Moonhawk": "moonhawk",
    "Cherrier Vivace / Tograc": "vivace",
    "Civetta Bolide": "bolide",
    "Civetta Scintilla": "scintilla",
    "ETK 800 Series": "etk800",
    "ETK I-Series": "etki",
    "Gavril Grand Marshal": "fullsize",
    "Gavril Roamer": "roamer",
    "Hirochi Sunburst": "sunburst",
    "Ibishu 200BX": "coupe",
    "Ibishu Covet": "hatch",
    "Soliad Wendover": "wendover"
}

def sanitize(text):
    """Cleans name for technical IDs (no quotes, no spaces)"""
    text = text.replace("'", "").replace('"', "").lower()
    text = re.sub(r'[^a-z0-9]', '_', text)
    return re.sub(r'_+', '_', text).strip('_')

def select_image():
    path = filedialog.askopenfilename(title="Select Image", filetypes=[("Images", "*.dds *.png")])
    if path:
        entry_image.delete(0, tk.END)
        entry_image.insert(0, path)

def generate():
    # Validation
    mod_raw = entry_mod.get()
    skin_raw = entry_skin.get()
    author_raw = entry_author.get()
    img_src = entry_image.get()
    v_display = combo_v.get()

    if not all([mod_raw, skin_raw, author_raw, img_src]):
        messagebox.showwarning("Warning", "Please fill in all fields.")
        return
    
    mod_id = sanitize(mod_raw)
    skin_id = sanitize(skin_raw)
    v_id = VEHICLES[v_display]
    
    # Folder Creation
    out_dir = os.path.join(os.getcwd(), "OUTPUT_MODS", mod_id)
    v_path = os.path.join(out_dir, "vehicles", v_id, skin_id)
    
    try:
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(v_path)
        
        # Image Handling
        dds_name = f"{v_id}_skin_{skin_id}.dds"
        target_path = os.path.join(v_path, dds_name)
        
        if img_src.lower().endswith(".dds"):
            shutil.copy(img_src, target_path)
        else:
            # Convert via ImageMagick
            cmd = ["magick"] if shutil.which("magick") else ["convert"]
            subprocess.run(cmd + [img_src, "-flip", "-alpha", "Set", "-define", "dds:compression=dxt5", target_path], check=True)

        # Materials (Legacy Miku Format)
        prefix = f"vehicles/common/{v_id}/{v_id}" if v_id == "pickup" else f"vehicles/{v_id}/{v_id}"
        game_dds = f"vehicles/{v_id}/{skin_id}/{dds_name}"
        mat_id = f"{v_id}.skin.{skin_id}"
        
        cs_content = f"""singleton Material("{mat_id}")
{{
    mapTo = "{mat_id}";
    colorPaletteMap[2] = "{game_dds}";
    overlayMap[2] = "{game_dds}";
    diffuseMap[2] = "{prefix}_c.dds";
    specularMap[2] = "{prefix}_s.dds";
    normalMap[2] = "{prefix}_n.dds";
    diffuseMap[1] = "{prefix}_d.dds";
    specularMap[1] = "{prefix}_s.dds";
    normalMap[1] = "{prefix}_n.dds";
    diffuseMap[0] = "vehicles/common/null.dds";
    specularMap[0] = "vehicles/common/null.dds";
    normalMap[0] = "{prefix}_n.dds";
    specularPower[2] = "128"; pixelSpecular[2] = "1";
    useAnisotropic[2] = "1"; castShadows = "1"; translucent = "1"; dynamicCubemap = true; instanceDiffuse[2] = true;
    materialTag0 = "beamng"; materialTag1 = "vehicle";
}};"""

        with open(os.path.join(v_path, "materials.cs"), "w", encoding="utf-8") as f:
            f.write(cs_content)
        
        # JBeam
        jbm = {
            f"{v_id}_skin_{skin_id}": {
                "information": {"authors": author_raw, "name": skin_raw, "value": 200},
                "slotType": "paint_design",
                "globalSkin": skin_id
            }
        }
        with open(os.path.join(v_path, f"{skin_id}.jbeam"), "w", encoding="utf-8") as f:
            json.dump(jbm, f, indent=4)
        
        messagebox.showinfo("Success", f"Mod '{mod_id}' successfully generated in OUTPUT_MODS folder!")
    except Exception as e:
        messagebox.showerror("Error", f"Generation failed: {e}")

# --- UI ---
root = tk.Tk()
root.title("BEAMNG SKIN MAKER - EN")
root.geometry("500x750")
root.configure(bg=BNG_BG_DARK)

tk.Label(root, text="SKIN CONFIGURATION", font=("Arial", 18, "bold"), bg=BNG_BG_DARK, fg=BNG_ORANGE).pack(pady=(30,5))
tk.Label(root, text="AUTOMATED MODDING UTILITY", font=("Arial", 8), bg=BNG_BG_DARK, fg=BNG_TEXT_DIM).pack()

# Form
frame = tk.Frame(root, bg=BNG_BG_DARK)
frame.pack(fill=tk.BOTH, padx=40, pady=20)

def create_field(txt, default=""):
    tk.Label(frame, text=txt.upper(), font=("Arial", 9, "bold"), bg=BNG_BG_DARK, fg=BNG_TEXT_DIM).pack(anchor="w", pady=(15,0))
    e = tk.Entry(frame, font=("Arial", 11), bg=BNG_BG_CARD, fg=BNG_WHITE, relief="flat", bd=8)
    e.insert(0, default)
    e.pack(fill=tk.X, pady=5)
    return e

entry_mod = create_field("Mod Name (Folder)")
entry_skin = create_field("Skin Name (In-game Menu)")
entry_author = create_field("Author", "Slapush")

tk.Label(frame, text="TARGET VEHICLE", font=("Arial", 9, "bold"), bg=BNG_BG_DARK, fg=BNG_TEXT_DIM).pack(anchor="w", pady=(15,0))
combo_v = ttk.Combobox(frame, values=list(VEHICLES.keys()), state="readonly", font=("Arial", 10))
combo_v.pack(fill=tk.X, pady=5)
combo_v.set(list(VEHICLES.keys())[0])

tk.Label(frame, text="SOURCE IMAGE (DDS / PNG)", font=("Arial", 9, "bold"), bg=BNG_BG_DARK, fg=BNG_TEXT_DIM).pack(anchor="w", pady=(15,0))
f_img = tk.Frame(frame, bg=BNG_BG_DARK)
f_img.pack(fill=tk.X, pady=5)
entry_image = tk.Entry(f_img, font=("Arial", 11), bg=BNG_BG_CARD, fg=BNG_WHITE, relief="flat", bd=8)
entry_image.pack(side=tk.LEFT, fill=tk.X, expand=True)
tk.Button(f_img, text="...", bg=BNG_ORANGE, fg=BNG_WHITE, relief="flat", command=select_image, width=5).pack(side=tk.RIGHT, padx=(10,0))

# Action Button
tk.Button(root, text="GENERATE SKIN", font=("Arial", 12, "bold"), bg=BNG_ORANGE, fg=BNG_WHITE, relief="flat", command=generate, height=2).pack(fill=tk.X, padx=40, pady=30)

# Footer
footer = tk.Frame(root, bg="#111111")
footer.pack(fill=tk.X, side=tk.BOTTOM)
tk.Label(footer, text="Developed in France by Slapush", font=("Arial", 9, "bold"), bg="#111111", fg=BNG_ORANGE).pack(pady=(10,0))
tk.Label(footer, text="DISCLAIMER: The author is not responsible for any technical issues.\nUse this script at your own risk.", font=("Arial", 7), bg="#111111", fg=BNG_TEXT_DIM, justify="center").pack(pady=(0,15))

root.mainloop()