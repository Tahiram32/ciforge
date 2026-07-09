import os
import sys

def launch_gui(repo_path):
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except ImportError:
        print("Error: tkinter is not installed. Please install python3-tk.")
        sys.exit(1)

    def select_folder():
        folder_selected = filedialog.askdirectory(initialdir=repo_path)
        if folder_selected:
            path_var.set(folder_selected)

    def run_scan():
        folder = path_var.get()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Error", "Invalid folder selected!")
            return
        
        status_var.set("Scanning... please wait.")
        root.update()
        
        # Run ciforge scan generating html
        cmd = f"ciforge --repo {folder} --vuln-scan --format html --badge"
        res = os.system(cmd)
        
        if res == 0 or res == 256: # 256 is exit code 1
            status_var.set("Scan complete! Check ciforge-report.html")
            messagebox.showinfo("Success", "Security Dashboard generated!\nOpen ciforge-report.html in your browser.")
        else:
            status_var.set("Scan failed.")
            messagebox.showerror("Error", "An error occurred during the scan.")

    root = tk.Tk()
    root.title("CI Forge - Developer Security Hub")
    root.geometry("500x300")
    root.configure(bg="#0f111a")

    # Styling
    bg_color = "#0f111a"
    fg_color = "#f8fafc"
    btn_color = "#3b82f6"

    # Header
    tk.Label(root, text="CI Forge", font=("Helvetica", 24, "bold"), bg=bg_color, fg="#a78bfa").pack(pady=(20, 5))
    tk.Label(root, text="Drag & Drop or Select a Codebase to Scan", font=("Helvetica", 12), bg=bg_color, fg=fg_color).pack(pady=(0, 20))

    # Path selection
    path_frame = tk.Frame(root, bg=bg_color)
    path_frame.pack(fill="x", padx=40)
    
    path_var = tk.StringVar(value=os.path.abspath(repo_path))
    tk.Entry(path_frame, textvariable=path_var, font=("Helvetica", 10), width=35).pack(side="left", padx=(0, 10))
    tk.Button(path_frame, text="Browse", command=select_folder, bg="#334155", fg=fg_color, relief="flat").pack(side="left")

    # Scan Button
    tk.Button(root, text="Run Security Scan", command=run_scan, font=("Helvetica", 14, "bold"), bg=btn_color, fg=fg_color, relief="flat", activebackground="#2563eb", activeforeground="white", width=20, pady=10).pack(pady=30)

    # Status
    status_var = tk.StringVar(value="Ready.")
    tk.Label(root, textvariable=status_var, font=("Helvetica", 10), bg=bg_color, fg="#94a3b8").pack()

    root.mainloop()
