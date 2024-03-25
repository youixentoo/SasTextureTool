
import customtkinter as cus_tk
import zipfile
import os
# from os import getenv
import threading
import cv2
import numpy as np
from lxml import etree
import pyminizip
from shutil import copy2, rmtree
from tkinter import messagebox, END
from time import sleep
# from PIL import Image
import re
import passw
import rpack

cus_tk.set_appearance_mode("system")
cus_tk.set_default_color_theme("blue")
        
class SpriteSheet():
    # Modified https://stackoverflow.com/a/45527493
    def __init__(self, xml_file, spritesheet):
        # self._data_path = xml_file
        if xml_file:
            self.tree = etree.parse(xml_file)
            self.map = {}
            for node in self.tree.iter():
                if node.attrib.get('name'):
                    if node.attrib.get('type'):
                        self.file_name = node.attrib.get('name')
                        if isinstance(xml_file, str):
                            self._data_path = xml_file.replace(f"/{self.file_name}.xml","")
                        elif isinstance(xml_file, zipfile.ZipExtFile):
                            self._data_path = xml_file.name.replace(f"/{self.file_name}.xml","")
                        self.file_type = node.attrib.get('type')
                    else:
                        name = node.attrib.get('name')
                        self.map[name] = {}
                        self.map[name]['x'] = int(node.attrib.get('x'))
                        self.map[name]['y'] = int(node.attrib.get('y'))
                        self.map[name]['w'] = int(node.attrib.get('w'))
                        self.map[name]['h'] = int(node.attrib.get('h'))
                        self.map[name]['ax'] = int(node.attrib.get('ax'))
                        self.map[name]['ay'] = int(node.attrib.get('ay'))
                        self.map[name]['aw'] = int(node.attrib.get('aw'))
                        self.map[name]['ah'] = int(node.attrib.get('ah'))
            if isinstance(spritesheet, str):
                self.spritesheet = cv2.imread(spritesheet, cv2.IMREAD_UNCHANGED)
            else:
                self.spritesheet = spritesheet

        else:
            print("else")
            return None

    def get_image_rect(self, x, y, w, h):
        return self.spritesheet[y:y+h, x:x+w]
    
    def get_sprite_info(self, name):
        return self.map.get(name)

    def get_image_name(self, name):
        return self.spritesheet[self.map[name]['y']:self.map[name]['y']+self.map[name]['h'], self.map[name]['x']:self.map[name]['x']+self.map[name]['w']]
    
    def get_sprite_names(self):
        return list(self.map.keys())
    
    def get_sheet_name(self):
        return self.file_name
    
    def write_img_to_dir(self, name, output_dir):
        cv2.imwrite(f"{output_dir}/{name}.{self.file_type}", self.get_image_name(name))

    def xml_to_dir(self, output_dir):
        self.tree.write(f"{output_dir}/{self.file_name}.xml", pretty_print=True)

    def save_spritesheet(self, output_dir):
        cv2.imwrite(f"{output_dir}/{self.file_name}.{self.file_type}", self.spritesheet)


class SpriteSheet_jet(SpriteSheet):
    # Modified https://stackoverflow.com/a/45527493
    def __init__(self, data_file, files, pwd):
        xml_file = files.open(data_file, pwd=pwd.encode())
        if xml_file:
            # Lack of motivation to do it better
            try:
                file_data = files.open(f"{xml_file.name[:-4]}.png", pwd=pwd.encode())
            except KeyError:
                file_data = files.open(f"{xml_file.name[:-4]}.jpg", pwd=pwd.encode())

            cv2_decoded = cv2.imdecode(np.frombuffer(file_data.read(), np.uint8), cv2.IMREAD_UNCHANGED)
            super().__init__(xml_file, cv2_decoded)
        else:
            print("else")
            return None


class App(cus_tk.CTk):
    def __init__(self):
        super().__init__()
        self.filepath = "" 
        self.script_out = "STTOut"
        self._init_width = 500
        self._init_height = 400
        self._split_checkvar = cus_tk.StringVar(value=False)
        self.wtt_stop = False
        self._sll_value = False
        # >>>>> Replace when building TODO: <<<<<
        self._pas_value = passw.passw()

        #  pady=12, padx=10
        # configure window
        self.title("SAS4 Texture Tool")
        self.resizable(False, False)
        # self.geometry(f"{self._init_width}x{self._init_height}")
        self.iconbitmap("STTInternal/Data/logo.ico")

        # configure grid layout
        self.grid_columnconfigure((0,2), weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure((1, 4), weight=1)

        self.label = cus_tk.CTkLabel(master=self, text="SAS4 Texture Tool", font=("Roboto", 24))
        self.label.grid(row=0, column=0, columnspan=5, pady=20)

        self.jet_frame = cus_tk.CTkFrame(master=self, width=200, height=110)
        self.jet_frame.grid(row=1, column=0, rowspan=4, sticky="nw", padx=(20, 10), pady=(10, 2))
        self.jet_frame.grid_propagate(False)

        self.jet_label = cus_tk.CTkLabel(master=self.jet_frame, text=".jet", font=("Roboto", 12))
        self.jet_label.grid(row=2, column=0, sticky="nw", padx=12)

        self.open_button = cus_tk.CTkButton(master=self.jet_frame, text="Split", width=85, command=self.extract)
        self.open_button.grid(row=3, column=0, padx=(12, 10), pady=(6, 0))

        self.open_checkbox = cus_tk.CTkCheckBox(master=self.jet_frame, text="As sheets",
                                                variable=self._split_checkvar, onvalue=True, offvalue=False)
        self.open_checkbox.grid(row=3, column=1, pady=(6, 0))

        self.compile_button = cus_tk.CTkButton(master=self.jet_frame, text="Compile", width=85, command=self.compile)
        self.compile_button.grid(row=4, column=0, padx=(12, 10), pady=(6,15))

        self.sheet_frame = cus_tk.CTkFrame(master=self, width=200, height=145)
        self.sheet_frame.grid(row=5, column=0, rowspan=4, sticky="nw", padx=(20, 10), pady=10)
        self.sheet_frame.grid_propagate(False)

        self.sheet_label = cus_tk.CTkLabel(master=self.sheet_frame, text="Spritesheets", font=("Roboto", 12))
        self.sheet_label.grid(row=2, column=0, sticky="nw", padx=12)

        self.sheet_open_button = cus_tk.CTkButton(master=self.sheet_frame, text="Split", width=85, command=self.sheet_extract)
        self.sheet_open_button.grid(row=3, column=0, padx=(12, 10), pady=(6, 0))

        self.sheet_combine_button = cus_tk.CTkButton(master=self.sheet_frame, text="Combine", width=85, command=self.sheet_combine)
        self.sheet_combine_button.grid(row=4, column=0, padx=(12, 10), pady=(6,0))

        self.sheet_compile_button = cus_tk.CTkButton(master=self.sheet_frame, text="Generate", width=85, command=self.sheet_generate)
        self.sheet_compile_button.grid(row=5, column=0, padx=(12, 10), pady=(6,12))



        self.text = cus_tk.CTkTextbox(self)
        self.text.configure(state="disabled")
        self.text.grid(row=1, column=2, rowspan=10, sticky="nsew", padx=20, pady=(10,10))


    def clear_textbox(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", END)
        self.text.configure(state="disable")


    def write_to_textbox(self, text, dot_progress=False):
        if dot_progress:
            sets = [f"{text}.", f"{text}..", f"{text}..."]
            self.wtt_thread = threading.Thread(target=self._write_dot_progress, args=(sets, ))
            self.wtt_thread.start()
        else:
            self.text.configure(state="normal")
            self.text.insert(1.0, text+"\n")
            self.text.configure(state="disable")


    # This doesn't work as well as I want it to, but it's better than nothing
    def _write_dot_progress(self, sets):
        for item in loop_list(sets):
            self.text.configure(state="normal")
            self.text.delete("1.0", END)
            self.text.insert(1.0, item)
            self.text.configure(state="disable")
            sleep(0.5)
            if self.wtt_stop:
                self.wtt_stop = False
                break



    # Main function for spritesheet split button
    def sheet_extract(self):
        filename = cus_tk.filedialog.askopenfilename(filetypes=[("PNG file", "*.png"), ("JPG file", "*.jpg")]) # TODO: fix this to show both at once
        if filename.endswith(".png") or filename.endswith(".jpg"):
            try:
                self.sheet_split_intermediate(filename)
            except Exception as exc:
                messagebox.showerror("SAS4 Texture Tool - single sheet ext", f"Unexpected {exc.__class__.__name__}:\n\n{str(exc)}")
        else:
            if not filename == "":
                messagebox.showinfo("SAS4 Texture Tool", "Only .png or .jpg can be selected")
            return
        
        
    def sheet_split_intermediate(self, filename):
        filepath = os.path.abspath(filename)
        t3 = threading.Thread(target=self.sheet_split, args=(filepath, ))
        t3.start()

    
    def sheet_split(self, filename):
        self.clear_textbox()
        result = re.search(r"\\(?:.(?!\\))+$", filename)
        if result:
            self.write_to_textbox("Splitting spritesheet...")
            sheet_name = result.group()[1:-4]
            if os.path.isfile(f"{filename[:-4]}.xml"):
                sprite_sheet = SpriteSheet(f"{filename[:-4]}.xml", filename)
                sprites_output = f"{self.script_out}/SpritesheetSplit/{sheet_name}"
                try:
                    os.makedirs(sprites_output)
                except Exception as exc:
                    pass
                names = sprite_sheet.get_sprite_names()
                for name in names:
                    # if name == "store_Blue_Innerr":
                    #     print(sprite_sheet.get_image_name(name))
                    sprite_sheet.write_img_to_dir(name, sprites_output)
                sprite_sheet.xml_to_dir(sprites_output)
                self.write_to_textbox("Finished\n")

            else:
                messagebox.showinfo("SAS4 Texture Tool", f"No xml file found for spritesheet: {sheet_name}")



    # Main function for spritesheet combine button
    def sheet_combine(self):
        selected_folder = cus_tk.filedialog.askdirectory(title="Select Split Textures Folder")
        if selected_folder:
            t4 = threading.Thread(target=self.sheet_combine_determine, args=(selected_folder, ))
            t4.start()


    def sheet_combine_determine(self, selected_folder, generate_sheet=False):
        self.clear_textbox()
        # Determine file structure, for both combine and generate buttons
        self.write_to_textbox("Checking folder...")

        filenames = next(os.walk(selected_folder), (None, None, []))[2]
        xml_file_search = [s for s in filenames if s.endswith(".xml")]
        if len(xml_file_search) > 1:
            self.write_to_textbox("Aborting (multiple .xml files)")
        elif len(xml_file_search) == 0:
            self.write_to_textbox("Aborting (no .xml file)")
        else:
            if generate_sheet:
                self.generate_new_spritesheet(selected_folder, filenames, xml_file_search[0])
            else:
                self.combine_single_sheet(selected_folder, filenames, xml_file_search[0])


    def combine_single_sheet(self, selected_folder, filenames, xml_file):
        self.write_to_textbox("Combining sprites...")
        xml_data = etree.parse(os.path.join(selected_folder, xml_file))

        for node in xml_data.iter():
            if node.attrib.get('name'):
                if node.attrib.get('type'):
                    sheet_name = node.attrib.get('name')
                    file_type = node.attrib.get('type')
                    background_img = np.zeros((int(node.attrib.get('texh')), int(node.attrib.get('texw')), 4), dtype=np.uint8)
                    background_img[0,0,0:3] = 255
                else:
                    name = node.attrib.get('name')
                    sprite_file = f"{name}.{file_type}"
                    if not sprite_file in filenames:
                        self.write_to_textbox("Aborting (sprite not found)")
                        messagebox.showinfo("SAS4 Texture Tool", f"Sprite not found: {name}.{file_type}")
                        return
                    
                    sprite_data = cv2.imread(os.path.join(selected_folder, sprite_file), cv2.IMREAD_UNCHANGED)
                    sprite_xml_width = int(node.attrib.get('w'))
                    sprite_xml_height = int(node.attrib.get('h'))
                    sprite_height, sprite_width, sprite_depth = sprite_data.shape

                    if sprite_height != sprite_xml_height or sprite_width != sprite_xml_width:
                        self.write_to_textbox("Aborting (shape mismatch)")
                        messagebox.showinfo("SAS4 Texture Tool", f"Sprite mismatch found for:\n{name}.{file_type}\nExpected: ({sprite_xml_width}, {sprite_xml_height}), found: ({sprite_width}, {sprite_width})\n\nUse generate if you want to make a new sheet")
                        return
                    
                    sheet_x = int(node.attrib.get("x"))
                    sheet_y = int(node.attrib.get("y"))
                    background_img[sheet_y:sheet_y+sprite_height, sheet_x:sheet_x+sprite_width, 0:sprite_depth] = sprite_data
        
        try:
            os.makedirs(os.path.join(self.script_out, "Spritesheets", sheet_name))
        except Exception:
            pass

        copy2(os.path.join(selected_folder, xml_file), os.path.join(self.script_out, "Spritesheets", sheet_name))
        cv2.imwrite(os.path.join(self.script_out, "Spritesheets", sheet_name, f"{sheet_name}.{file_type}"), background_img)
        self.write_to_textbox("Finished\n")


    # Main function for spritesheet generate button
    def sheet_generate(self):
        selected_folder = cus_tk.filedialog.askdirectory(title="Select Split Textures Folder")
        if selected_folder:
            t5 = threading.Thread(target=self.sheet_combine_determine, args=(selected_folder, True, ))
            t5.start()


    # Generate an all new spritesheet
    def generate_new_spritesheet(self, selected_folder, filenames, xml_file):
        self.clear_textbox()
        self.write_to_textbox("Combining sprites", True)
        xml_data = etree.parse(os.path.join(selected_folder, xml_file))
        nodes = []
        sizes = []

        for node in xml_data.iter():
            if node.attrib.get('name'):
                if node.attrib.get('type'):
                    sheet_name = node.attrib.get('name')
                    file_type = node.attrib.get('type')
                else:
                    name = node.attrib.get('name')
                    sprite_file = f"{name}.{file_type}"
                    # if not sprite_file in filenames:
                    #     self.write_to_textbox("Aborting (sprite not found)\n")
                    #     messagebox.showinfo("SAS4 Texture Tool", f"Sprite not found: {name}.{file_type}")
                    #     return
                    
                    initial_sprite_data = cv2.imread(os.path.join(selected_folder, sprite_file), cv2.IMREAD_UNCHANGED)
                    # Only used for placements, the image on disk remains the original size
                    sprite_data = cv2.copyMakeBorder(initial_sprite_data, 1,0,1,0, borderType=cv2.BORDER_CONSTANT, value=(0,0,0,0))
                    # sprite_xml_width = int(node.attrib.get('w'))
                    # sprite_xml_height = int(node.attrib.get('h'))
                    sprite_height, sprite_width, sprite_depth = sprite_data.shape
                    nodes.append(node)
                    sizes.append((sprite_width, sprite_height))
        
        positions = rpack.pack(sizes)
        bounding_box = rpack.bbox_size(sizes, positions)
        # print(f"Sheet size: {bounding_box[0]} width, {bounding_box[1]} height")

        background_img = np.zeros((bounding_box[1], bounding_box[0], 4), dtype=np.uint8)
        background_img[0,0,0:3] = 255
        x_pos_ms1 = 0
        x_pos_ms2 = 0
        y_pos_ms1 = 0
        y_pos_ms2 = 0

        gen_sheet_out = f"{self.script_out}/SpritesheetGenerated"
        try:
            os.makedirs(gen_sheet_out)
        except Exception as exc:
            pass

        
        with open(os.path.join(gen_sheet_out, f"{sheet_name}.xml"), "w") as out_xml_file:
            out_xml_file.write("<SpriteInformation>")
            out_xml_file.write(f"""\t<FrameInformation name="{sheet_name}" texw="{bounding_box[0]}" texh="{bounding_box[1]}" type="{file_type}">""")
            for index, node in enumerate(nodes):
                x_pos, y_pos = positions[index]
                name = node.attrib.get('name')
                sprite_file = f"{name}.{file_type}"

                sprite_data = cv2.imread(os.path.join(selected_folder, sprite_file), cv2.IMREAD_UNCHANGED)
                sprite_height, sprite_width, sprite_depth = sprite_data.shape
                if sprite_depth < 4:
                    print("not 4 depth")
                    print(name, sprite_depth)

                initial_aw = int(node.attrib['aw'])
                initial_w = int(node.attrib['w'])
                initial_ah = int(node.attrib['ah'])
                initial_h = int(node.attrib['h'])
                w_to_aw_ratio = initial_aw/initial_w
                h_to_ah_ratio = initial_ah/initial_h
                
                # print(f"Name: {name} - Width Ratio: {w_to_aw_ratio}, Width: {sprite_width} Adjusted: {sprite_width*w_to_aw_ratio}")
                background_img[y_pos:y_pos+sprite_height, x_pos:x_pos+sprite_width, 0:sprite_depth] = sprite_data
                # TODO: fix x/y values --> can't be fixed, nk uses dumb "the sprite used is larger than the xml xy" bs
                node.attrib['x'] = str(x_pos)
                node.attrib['y'] = str(y_pos)
                node.attrib['w'] = str(sprite_width)
                node.attrib['h'] = str(sprite_height)
                node.attrib['aw'] = str(round(sprite_width*w_to_aw_ratio))
                node.attrib['ah'] = str(round(sprite_height*h_to_ah_ratio))
                out_xml_file.write(f"""\t\t{etree.tostring(node).decode()}""")

                # if name == "store_Blue_Innerr" or name == "news_red_Inner":
                #     print("### YES ###")
                #     print(name, y_pos, x_pos, sprite_data.shape, sprite_file)
                    # x_pos_ms1 = x_pos
                    # x_pos_ms2 = x_pos+sprite_width
                    # y_pos_ms1 = y_pos
                    # y_pos_ms2 = y_pos+sprite_height
                    # print(background_img[y_pos_ms1:y_pos_ms2, x_pos_ms1:x_pos_ms2])

            
            out_xml_file.write("\t</FrameInformation>")
            out_xml_file.write("</SpriteInformation>")
            

        # print("##", background_img[y_pos_ms1:y_pos_ms2, x_pos_ms1:x_pos_ms2])
        # cv2.imshow("image", background_img)
        # cv2.waitKey()
        # cv2.imwrite(os.path.join(self.script_out, "Spritesheets", sheet_name, f"{sheet_name}.{file_type}"), background_img)
        # bordered_background = cv2.copyMakeBorder(background_img, 1,1,1,1, borderType=cv2.BORDER_CONSTANT, value=(0,0,0,0))
        cv2.imwrite(os.path.join(gen_sheet_out, f"{sheet_name}.{file_type}"), background_img)
        self.wtt_stop = True
        self.write_to_textbox("Finished\n")
        # print(os.path.join(self.script_out, f"{sheet_name}.{file_type}"))




    # Main function for .jet compile button
    def compile(self):
            self._is_compressable = True
            selected_folder = cus_tk.filedialog.askdirectory(title="Select Split Textures Folder")
            if selected_folder:
                t2 = threading.Thread(target=self.determine_structure, args=(selected_folder, ))
                t2.start()
            # self.zip_sheets(selected_folder)

                
    def determine_structure(self, selected_folder):
        self.clear_textbox()
        self._sprite_compile_spriteInfo_path = ""
        # Determine file structure
        self.write_to_textbox("Checking folder...")
        for subdir, dirs, files in os.walk(selected_folder):
            if subdir.endswith("High") and len(files) > 0:
                pass
            elif len(files) > 1:
                self._is_compressable = False
            else:
                # SpriteInfo and empty folders
                if len(files) == 1:
                    self._jet_output_name = files[0].replace("_SpriteInfo.xml", "") 
                    self._sprite_compile_spriteInfo_path = os.path.normpath(os.path.join(os.getcwd(), subdir))

        if self._is_compressable:
            try:
                self.zip_sheets(selected_folder)
            except Exception as exc:
                messagebox.showerror("SAS4 Texture Tool - compile sheets", f"Unexpected {exc.__class__.__name__}:\n\n{str(exc)}")
        else:
            try:
                temp_output_folder = self.create_sheets(selected_folder)
                self.zip_sheets(os.path.join(os.getcwd(), temp_output_folder))
            except OSError as OSexc:
                faulty_file = re.findall("'{1}.+'{1}", str(OSexc))[0].strip("'")
                messagebox.showinfo("SAS4 Texture Tool - compile pngs", f"There was a problem with the following file:\n\n{faulty_file}")
            except Exception as exc:
                messagebox.showerror("SAS4 Texture Tool - compile pngs", f"Unexpected {exc.__class__.__name__}:\n\n{str(exc)}")

            _delete_cache_files(os.path.join(os.getcwd(), "STTInternal", "Cache", self._jet_output_name))

        self.write_to_textbox("Finished\n")
                
    
    def zip_sheets(self, folder):
        self.write_to_textbox("Zipping files...")
        file_div_path_to_file = []
        for subdir, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith("_SpriteInfo.xml"):
                    internal_zip_path = "Assets/Textures"
                else:
                    internal_zip_path = "Assets/Textures/High"

                file_div_path_to_file.append([os.path.join(os.path.normpath(subdir), file),internal_zip_path])

        files_to_zip, path_to_file_temp = map(list, zip(*file_div_path_to_file))
        try:
            os.remove(f"{self._jet_output_name}.jet")
        except FileNotFoundError:
            pass
        except Exception as exc:
            messagebox.showerror("SAS4 Texture Tool - zip sheets", f"Unexpected {exc.__class__.__name__}:\n\n{str(exc)}")

        pyminizip.compress_multiple(files_to_zip, path_to_file_temp, f"{self._jet_output_name}.jet", self._pas_value, 0)


    def create_sheets(self, selected_folder):
        self.write_to_textbox("Combining sprites...")
        temp_output_folder = os.path.join(os.getcwd(), "STTInternal", "Cache", self._jet_output_name) #os.path.join(os.getcwd(), "STTcache", self._jet_output_name, "Assets", "Textures", "High")
        _create_temp_to_zip(os.path.join(temp_output_folder, "Assets", "Textures", "High"))
        
        sprite_tree = etree.parse(f"{os.path.join(self._sprite_compile_spriteInfo_path, self._jet_output_name)}_SpriteInfo.xml")
        sprite_info_list = sprite_tree.findall(".//SpriteInfoXml")
        copy2(f"{os.path.join(self._sprite_compile_spriteInfo_path, self._jet_output_name)}_SpriteInfo.xml", 
              os.path.join(temp_output_folder, "Assets", "Textures"))
        
        for sprite_info_entry in sprite_info_list:
            si_name = sprite_info_entry.attrib.get("name")
            sprite_filepath = os.path.join(self._sprite_compile_spriteInfo_path, "High", si_name)

            self.compile_spritesheet(f"{si_name}.xml", sprite_filepath, os.path.join(temp_output_folder, "Assets", "Textures", "High"))
        
        return os.path.join("STTInternal", "Cache", self._jet_output_name)
            

    def compile_spritesheet(self, xml_file, folder_path, temp_out):
        xml_tree = etree.parse(os.path.join(folder_path, xml_file))
        
        frameInfo = xml_tree.find(".//FrameInformation")
        output_png_Height = int(frameInfo.attrib.get("texh"))
        output_png_Width = int(frameInfo.attrib.get("texw"))
        output_png_type = frameInfo.attrib.get("type")
        output_name = frameInfo.attrib.get("name")
        sprite_cells = xml_tree.findall(".//Cell")

        background_img = np.zeros((output_png_Height, output_png_Width, 4), dtype=np.uint8)
        background_img[0,0,0:3] = 255

        for sprite_cell in sprite_cells:
            sprite_name = sprite_cell.attrib.get("name")
            sprite_image = cv2.imread(f"{os.path.join(folder_path, sprite_name)}.{output_png_type}", cv2.IMREAD_UNCHANGED)
            sprite_height, sprite_width, sprite_depth = sprite_image.shape
            sheet_x = int(sprite_cell.attrib.get("x"))
            sheet_y = int(sprite_cell.attrib.get("y"))

            background_img[sheet_y:sheet_y+sprite_height, sheet_x:sheet_x+sprite_width, 0:sprite_depth] = sprite_image

        copy2(os.path.join(folder_path, xml_file), temp_out)
        cv2.imwrite(os.path.join(temp_out, f"{output_name}.{output_png_type}"), background_img)
        

    # Main function for .jet split button
    def extract(self):
        filename = cus_tk.filedialog.askopenfilename(filetypes=[("Compressed Textures", "*.jet")])
        # print("filename: ", filename)
        if filename.endswith(".jet"):
            try:
                self.extract_files_intermediate(filename)
            except Exception as exc:
                messagebox.showerror("SAS4 Texture Tool - extract jets", f"Unexpected {exc.__class__.__name__}:\n\n{str(exc)}")
        else:
            if not filename == "":
                messagebox.showinfo("SAS4 Texture Tool", "Only .jet can be selected")
            return
        

    def extract_files_intermediate(self, filename):
        filepath = os.path.abspath(filename)
        t1 = threading.Thread(target=self.extract_files, args=(filepath, ))
        t1.start()
        

    def extract_files(self, filename):
        self.clear_textbox()
        self.write_to_textbox("Unzipping files", True)
        with zipfile.ZipFile(filename) as files:
            sprite_sheets = []
            for name in files.namelist():
                if name.startswith(f"Assets/Textures"):
                    if name.endswith(".xml"):
                        if not name.endswith("SpriteInfo.xml"):
                            sprite_sheets.append(SpriteSheet_jet(name, files, self._pas_value))
                            # return
                        else:
                            self.prefix = f"{self.script_out}/Jets/{name.replace("Assets/Textures/", "").replace("_SpriteInfo.xml", "")}"
                            self.write_spriteInfo_make_mainDir("/Assets/Textures/", files.read(name, pwd=self._pas_value.encode()), name.replace("/Assets/Textures/", ""))

        self.wtt_stop = True                   
        self.write_to_textbox("Exporting files...") 

        if self._split_checkvar.get() == "1":  
            self.extract_sheets(sprite_sheets, "High")              
        else:
            self.extract_pngs(sprite_sheets, "High")

        self.write_to_textbox("Finished\n")


    def write_spriteInfo_make_mainDir(self, output_folder, xml_file, xml_name):
        try:
            os.makedirs(f"{self.prefix}{output_folder}")
        except Exception:
            pass

        with open(f"{self.prefix}/{xml_name}", "w") as o_xml:
            o_xml.write(xml_file.decode()) 


    def extract_pngs(self, sprite_sheets, output_folder):
        
        for sprite_sheet in sprite_sheets:
            sprites_output = f"{self.prefix}/Assets/Textures/{output_folder}/{sprite_sheet.file_name}"
            try:
                os.makedirs(sprites_output)
            except Exception as exc:
                pass
            names = sprite_sheet.get_sprite_names()
            for name in names:
                sprite_sheet.write_img_to_dir(name, sprites_output)
            sprite_sheet.xml_to_dir(sprites_output)


    def extract_sheets(self, sprite_sheets, output_folder):
        
        for sprite_sheet in sprite_sheets:
            sprites_output = f"{self.prefix}/Assets/Textures/{output_folder}"
            try:
                os.makedirs(sprites_output)
            except Exception as exc:
                pass
            sprite_sheet.save_spritesheet(sprites_output)
            sprite_sheet.xml_to_dir(sprites_output)


def loop_list(input_list):
    while True:
        for item in input_list:
            yield item


def _create_temp_to_zip(cache_loc):
    try:
        os.makedirs(cache_loc)
    except Exception:
        pass


def _delete_cache_files(cache_jet):
    try:
        rmtree(cache_jet)
    except Exception as exc:
        messagebox.showerror("SAS4 Texture Tool - Delete cache", f"Unexpected {exc.__class__.__name__}:\n\n{str(exc)}")


def __create_folders():
    #   STTInternal
    #       |- Cache                
    #       |- Data

    try:
        os.makedirs(os.path.join(os.getcwd(), "STTInternal", "Cache"))
    except FileExistsError:
        pass
    except Exception as exc:
        messagebox.showerror("SAS4 Texture Tool - Create internal", f"Unexpected {exc.__class__.__name__}:\n\n{str(exc)}")


if __name__ == "__main__":
    __create_folders()
    app = App()
    app.mainloop()