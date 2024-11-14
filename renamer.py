# Import Modules
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import font
from datetime import datetime
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import webbrowser  # Import webbrowser to open URLs
import json  # For theme persistence
from PIL import Image, ImageTk  # Import Pillow for image handling

CONFIG_FILE = "config.json"

class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EasyReNamer")
        self.root.geometry("700x710")

        # Set Application Icon
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon", "app_icon.ico")
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Failed to load icon: {e}")

        # Load theme preference
        self.current_theme = self.load_theme()

        # Set ttkbootstrap theme
        self.style = tb.Style(theme=self.current_theme)  # Store as instance variable

        # Custom styles based on theme
        if self.current_theme == 'darkly':
            self.style.configure('Custom.TFrame', background='#2E2E2E')  # Dark gray background
            self.style.configure('Custom.TLabel', background='#2E2E2E', foreground='white')  # White text
        else:
            self.style.configure('Custom.TFrame', background='#F0F8FF')  # Light blue background
            self.style.configure('Custom.TLabel', background='#F0F8FF', foreground='black')  # Black text

        # Define custom style for the toggle label
        self.configure_toggle_label_style()

        self.selected_files = []
        self.sort_option = tk.StringVar(value="Default Sequence")

        # Custom Fonts
        self.title_font = font.Font(family="Segoe UI", size=16, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=10)
        self.button_font = font.Font(family="Segoe UI", size=10, weight="bold")
        self.footer_font = font.Font(family="Segoe UI", size=8)

        # Additional Font for Hyperlink
        self.link_font = font.Font(family="Segoe UI", size=8, underline=True)

        # Load Toggle Images
        try:
            # Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Construct paths to the images
            on_image_path = os.path.join(script_dir, "icon", "night.png")
            off_image_path = os.path.join(script_dir, "icon", "day.png")
            
            # Debugging prints (optional, remove in production)
            print(f"On Image Path: {on_image_path} Exists: {os.path.exists(on_image_path)}")
            print(f"Off Image Path: {off_image_path} Exists: {os.path.exists(off_image_path)}")
            
            # Desired size for the toggle images
            desired_size = (53, 25)  # Increased size for better visibility
            
            # Handle Pillow's ANTIALIAS deprecation
            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.ANTIALIAS  # For older Pillow versions
            
            # Open and resize the images using Pillow
            on_image_full = Image.open(on_image_path).resize(desired_size, resample_filter)
            self.on_image = ImageTk.PhotoImage(on_image_full)
            
            off_image_full = Image.open(off_image_path).resize(desired_size, resample_filter)
            self.off_image = ImageTk.PhotoImage(off_image_full)

            # Load animation frames (optional)
            # Uncomment and ensure these images exist if you plan to use animations
            # self.toggle_animation_on = [
            #     ImageTk.PhotoImage(Image.open(os.path.join(script_dir, "icon", f"toggle_on_{i}.png")).resize(desired_size, resample_filter)) for i in range(1, 6)
            # ]
            # self.toggle_animation_off = [
            #     ImageTk.PhotoImage(Image.open(os.path.join(script_dir, "icon", f"toggle_off_{i}.png")).resize(desired_size, resample_filter)) for i in range(1, 6)
            # ]
        except Exception as e:
            messagebox.showerror("Image Loading Error", f"Error loading toggle images: {e}")
            self.on_image = None
            self.off_image = None
            self.toggle_animation_on = []
            self.toggle_animation_off = []

        # GUI Elements
        self.create_widgets()

    def configure_toggle_label_style(self):
        self.style.configure(
            'Custom.TLabel',
            borderwidth=0,  # Removes any border
            padding=0,      # Removes padding
            background=self.style.lookup('Custom.TFrame', 'background'),  # Match frame background
            foreground=self.style.lookup('Custom.TLabel', 'foreground')   # Match label foreground
        )

    def create_widgets(self):
        # Main Frame with Custom Background
        main_frame = tb.Frame(self.root, padding=20, style='Custom.TFrame')
        main_frame.pack(fill='both', expand=True)

        # Top Frame for Title and Theme Switch
        top_frame = tb.Frame(main_frame, style='Custom.TFrame')
        top_frame.pack(fill='x')

        # Title Label with Custom Style, centered if needed
        self.title_label = tb.Label(top_frame, text="EasyReNamer", font=self.title_font, style='Custom.TLabel')
        self.title_label.pack(side='left', padx=(55,0), expand=True)  # Adjust padding as needed

        # Spacer to push the switch to the right
        top_frame.columnconfigure(1, weight=1)

         # Toggle Switch for Theme Switching using Label
        if self.on_image and self.off_image:
            self.theme_toggle = tb.Label(
                top_frame,
                image=self.on_image if self.current_theme == 'darkly' else self.off_image,
                cursor='hand2',  # Changes cursor to hand on hover
                style='Custom.TLabel'  # Use custom label style
            )
            self.theme_toggle.pack(side='right', pady=0)  # Align right, top
            self.theme_toggle.bind("<Button-1>", lambda e: self.toggle_theme())  # Bind click event
        else:
            # Fallback if images are not loaded
            self.theme_toggle = tb.Button(
                top_frame,
                text="Toggle Theme",
                command=self.toggle_theme,
                bootstyle="info-outline"
            )
            self.theme_toggle.pack(side='right', pady=10)  # Retain some padding for text button


        # Select Files Button
        self.select_button = tb.Button(main_frame, text="Select Files", command=self.select_files, bootstyle="primary-gradient")
        self.select_button.pack(pady=(10,10))

        # Sorting Options
        self.sort_label = tb.Label(main_frame, text="Sort Files By:", font=self.label_font, style='Custom.TLabel')
        self.sort_label.pack(pady=(10, 10))

        self.sort_frame = tb.Frame(main_frame, style='Custom.TFrame')
        self.sort_frame.pack()

        # Radiobuttons
        self.sort_default = tb.Radiobutton(
            self.sort_frame,
            text="Default Sequence",
            variable=self.sort_option,
            value="Default Sequence",
            command=self.update_file_list,
            bootstyle="info",
        )
        self.sort_creation = tb.Radiobutton(
            self.sort_frame,
            text="Creation Time",
            variable=self.sort_option,
            value="Creation Time",
            command=self.update_file_list,
            bootstyle="info",
        )
        self.sort_size = tb.Radiobutton(
            self.sort_frame,
            text="File Size",
            variable=self.sort_option,
            value="File Size",
            command=self.update_file_list,
            bootstyle="info",
        )

        self.sort_default.pack(side="left", padx=5)
        self.sort_creation.pack(side="left", padx=5)
        self.sort_size.pack(side="left", padx=5)

        # File List Treeview with Scrollbar
        tree_frame = tb.Frame(main_frame, style='Custom.TFrame')
        tree_frame.pack(pady=10, fill='both', expand=True)

        self.tree = tb.Treeview(
            tree_frame,
            columns=("Original Filename", "New Filename"),
            show='headings',
            selectmode='none',
            bootstyle="info",
        )
        self.tree.heading("Original Filename", text="Original Filename")
        self.tree.heading("New Filename", text="New Filename")
        self.tree.column("Original Filename", width=300, anchor='w')
        self.tree.column("New Filename", width=300, anchor='w')

        # Scrollbar for Treeview
        tree_scrollbar = tb.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview,
            bootstyle="info-round",
        )
        self.tree.configure(yscrollcommand=tree_scrollbar.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scrollbar.grid(row=0, column=1, sticky='ns')

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # New Extension Entry
        self.extension_label = tb.Label(main_frame, text="Enter New Extension (e.g., txt):", font=self.label_font, style='Custom.TLabel')
        self.extension_label.pack(pady=(10, 0))
        self.extension_entry = tb.Entry(main_frame, font=self.label_font, bootstyle="info")
        self.extension_entry.pack(pady=5, fill='x')
        self.extension_entry.bind("<KeyRelease>", self.update_file_list)

        # Rename Base Name Entry
        self.basename_label = tb.Label(main_frame, text="Enter Base Name for Renaming:", font=self.label_font, style='Custom.TLabel')
        self.basename_label.pack(pady=(10, 0))
        self.basename_entry = tb.Entry(main_frame, font=self.label_font, bootstyle="info")
        self.basename_entry.pack(pady=5, fill='x')
        self.basename_entry.bind("<KeyRelease>", self.update_file_list)

        # Separator Entry
        self.separator_label = tb.Label(main_frame, text="Enter Separator (optional) (e.g., _, -, or space):", font=self.label_font, style='Custom.TLabel')
        self.separator_label.pack(pady=(10, 0))
        self.separator_entry = tb.Entry(main_frame, font=self.label_font, bootstyle="info")
        self.separator_entry.pack(pady=5, fill='x')
        self.separator_entry.bind("<KeyRelease>", self.update_file_list)

        # Apply Changes Button
        self.apply_button = tb.Button(
            main_frame,
            text="Apply Changes",
            command=self.apply_changes,
            bootstyle="success-gradient",
        )
        self.apply_button.pack(pady=20)

        # Developer Label with Hyperlink
        self.developer_frame = tb.Frame(main_frame, style='Custom.TFrame')
        self.developer_frame.pack(side="bottom", pady=10)

        # "Developed by" Label
        self.developer_text = tb.Label(self.developer_frame, text="Developed by ", font=self.footer_font, style='Custom.TLabel')
        self.developer_text.pack(side="left")

        # Developer Name Label styled as Hyperlink
        self.developer_link = tb.Label(
            self.developer_frame,
            text="Hasindu Nimesh",
            font=self.link_font,  # Use the underline font
            foreground="blue",
            cursor="hand2",
            style='Custom.TLabel'
        )
        self.developer_link.pack(side="left")
        self.developer_link.bind("<Button-1>", lambda e: self.open_link("http://hasindunimesh.me/"))  # Replace with your URL

    def load_theme(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get("theme", "litera")
            except json.JSONDecodeError:
                return "litera"
        return "litera"

    def save_theme(self):
        config = {"theme": self.current_theme}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)

    def toggle_theme(self):
        # Toggle the theme
        if self.current_theme == 'darkly':
            # Switch to Light Theme
            self.style.theme_use('litera')
            self.current_theme = 'litera'
            # Update custom styles for Light Theme
            self.style.configure('Custom.TFrame', background='#F0F8FF')  # Light blue background
            self.style.configure('Custom.TLabel', background='#F0F8FF', foreground='black')  # Black text
            # Update Toggle Label image
            if self.off_image:
                self.theme_toggle.config(image=self.off_image)
        else:
            # Switch to Dark Theme
            self.style.theme_use('darkly')
            self.current_theme = 'darkly'
            # Update custom styles for Dark Theme
            self.style.configure('Custom.TFrame', background='#2E2E2E')  # Dark gray background
            self.style.configure('Custom.TLabel', background='#2E2E2E', foreground='white')  # White text
            # Update Toggle Label image
            if self.on_image:
                self.theme_toggle.config(image=self.on_image)
        
        # Reconfigure the toggle label style after changing the theme
        self.configure_toggle_label_style()

        # Save the current theme
        self.save_theme()

    def open_link(self, url):
        webbrowser.open(url)

    def select_files(self):
        files = filedialog.askopenfilenames(title="Select Files")
        if files:
            self.selected_files = list(files)
            self.update_file_list()
            messagebox.showinfo("Files Selected", f"{len(self.selected_files)} files selected.")

    def update_file_list(self, event=None):
        # Clear the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.selected_files:
            return

        # Get the sorting option
        sort_option = self.sort_option.get()

        # Sort the files accordingly
        if sort_option == "Creation Time":
            self.selected_files.sort(key=lambda x: os.path.getctime(x))
        elif sort_option == "File Size":
            self.selected_files.sort(key=lambda x: os.path.getsize(x))

        new_extension = self.extension_entry.get().strip()
        base_name = self.basename_entry.get().strip()
        separator = self.separator_entry.get()

        # Group files by directory for numbering
        files_by_directory = {}
        for file_path in self.selected_files:
            directory = os.path.dirname(file_path)
            files_by_directory.setdefault(directory, []).append(file_path)

        # Prepare data for the treeview
        tree_data = []

        for directory, files in files_by_directory.items():
            existing_numbers = []

            if base_name:
                # Find existing files that match the base name pattern
                pattern = re.compile(rf"^{re.escape(base_name)}{re.escape(separator)}?(\d+)?")
                for fname in os.listdir(directory):
                    match = pattern.match(fname)
                    if match:
                        num_str = match.group(1)
                        if num_str:
                            existing_numbers.append(int(num_str))

                # Determine starting index
                if existing_numbers:
                    start_index = max(existing_numbers) + 1
                else:
                    start_index = 1

            for i, file_path in enumerate(files):
                directory, original_filename = os.path.split(file_path)
                name, ext = os.path.splitext(original_filename)

                # Change Extension
                if new_extension:
                    ext = f".{new_extension}"
                else:
                    ext = os.path.splitext(original_filename)[1]  # Keep original extension

                # Rename with Base Name and Index
                if base_name:
                    if len(files) == 1 and not existing_numbers:
                        new_name = f"{base_name}{ext}"
                    else:
                        index = start_index + i
                        new_name = f"{base_name}{separator}{str(index).zfill(2)}{ext}"
                else:
                    new_name = f"{name}{ext}"

                tree_data.append((original_filename, new_name))

        # Insert data into the treeview
        for original, new in tree_data:
            self.tree.insert('', 'end', values=(original, new))

    def apply_changes(self):
        if not self.selected_files:
            messagebox.showwarning("No Files Selected", "Please select files first.")
            return

        new_extension = self.extension_entry.get().strip()
        base_name = self.basename_entry.get().strip()
        separator = self.separator_entry.get()

        if not new_extension and not base_name:
            messagebox.showwarning("No Changes Specified", "Please enter a new extension or base name.")
            return

        # Get the sorting option
        sort_option = self.sort_option.get()

        # Sort the files accordingly
        if sort_option == "Creation Time":
            self.selected_files.sort(key=lambda x: os.path.getctime(x))
        elif sort_option == "File Size":
            self.selected_files.sort(key=lambda x: os.path.getsize(x))

        # Group files by directory
        files_by_directory = {}
        for file_path in self.selected_files:
            directory = os.path.dirname(file_path)
            files_by_directory.setdefault(directory, []).append(file_path)

        for directory, files in files_by_directory.items():
            existing_numbers = []

            if base_name:
                # Find existing files that match the base name pattern
                pattern = re.compile(rf"^{re.escape(base_name)}{re.escape(separator)}?(\d+)?")
                for fname in os.listdir(directory):
                    match = pattern.match(fname)
                    if match:
                        num_str = match.group(1)
                        if num_str:
                            existing_numbers.append(int(num_str))

                # Determine starting index
                if existing_numbers:
                    start_index = max(existing_numbers) + 1
                else:
                    start_index = 1

            for i, file_path in enumerate(files):
                directory, original_filename = os.path.split(file_path)
                name, ext = os.path.splitext(original_filename)

                # Change Extension
                if new_extension:
                    ext = f".{new_extension}"
                else:
                    ext = os.path.splitext(original_filename)[1]  # Keep original extension

                # Rename with Base Name and Index
                if base_name:
                    if len(files) == 1 and not existing_numbers:
                        new_name = f"{base_name}{ext}"
                    else:
                        index = start_index + i
                        new_name = f"{base_name}{separator}{str(index).zfill(2)}{ext}"
                else:
                    new_name = f"{name}{ext}"

                new_path = os.path.join(directory, new_name)

                try:
                    os.rename(file_path, new_path)
                except Exception as e:
                    messagebox.showerror("Error Renaming File", f"Could not rename {file_path}:\n{e}")
                    continue

        messagebox.showinfo("Operation Completed", "Files have been renamed successfully.")
        self.selected_files = []

        # Clear the entries
        self.extension_entry.delete(0, tk.END)
        self.basename_entry.delete(0, tk.END)
        self.separator_entry.delete(0, tk.END)

        # Clear the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    # Initialize ttkbootstrap Window
    root = tb.Window(themename="litera")
    app = FileRenamerApp(root)
    app.run()
