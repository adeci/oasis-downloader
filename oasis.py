import paramiko
import stat
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.ttk import Progressbar
import threading
import time
import os
import sys


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class SFTPClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Oasis")
        self.root.iconbitmap(resource_path('oasis.ico'))

        self.sftp = None
        self.ssh = None

        self.current_path = None
        self.history = []
        self.history_index = -1

        tk.Label(root, text="Server IP:").grid(row=0, column=0, sticky=tk.W)
        self.server_entry = tk.Entry(root, width=30)
        self.server_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(root, text="Port:").grid(row=1, column=0, sticky=tk.W)
        self.port_entry = tk.Entry(root, width=30)
        self.port_entry.insert(0, "22")
        self.port_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(root, text="Username:").grid(row=2, column=0, sticky=tk.W)
        self.username_entry = tk.Entry(root, width=30)
        self.username_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(root, text="Private Key Path:").grid(
            row=3, column=0, sticky=tk.W)
        self.private_key_entry = tk.Entry(root, width=30)
        self.private_key_entry.grid(row=3, column=1, padx=10, pady=5)
        private_key_button = tk.Button(
            root, text="Browse...", command=lambda: self.browse_file(self.private_key_entry))
        private_key_button.grid(row=3, column=2, padx=10, pady=5)

        tk.Label(root, text="Private Key Passphrase:").grid(
            row=4, column=0, sticky=tk.W)
        self.passphrase_entry = tk.Entry(root, width=30, show="*")
        self.passphrase_entry.grid(row=4, column=1, padx=10, pady=5)

        connect_button = tk.Button(
            root, text="Connect", command=self.connect_to_server)
        connect_button.grid(row=5, column=1, pady=10)

        self.heartbeat_label = tk.Label(
            root, text="Connection Status: Disconnected", fg="red")
        self.heartbeat_label.grid(row=6, column=1, pady=5)

        self.file_frame = tk.Frame(root)
        self.file_frame.grid(row=7, column=0, columnspan=3, pady=10)

        self.back_button = tk.Button(
            root, text="Back", command=self.navigate_back, state=tk.DISABLED)
        self.back_button.grid(row=8, column=0, padx=10, pady=5)

        self.file_tree = ttk.Treeview(self.file_frame, columns=(
            "Name", "Type"), show="headings", selectmode="browse")
        self.file_tree.heading("Name", text="Name")
        self.file_tree.heading("Type", text="Type")
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(
            self.file_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.progress_bar = Progressbar(
            root, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress_bar.grid(row=9, column=0, columnspan=3, pady=10)

        self.download_button = tk.Button(
            root, text="Download Selected File", command=self.download_selected_file)
        self.download_button.grid(row=10, column=1, pady=10)
        self.download_button.config(state=tk.DISABLED)

    def browse_file(self, entry):
        filename = filedialog.askopenfilename()
        entry.delete(0, tk.END)
        entry.insert(0, filename)

    def connect_to_server(self):
        try:
            server_ip = self.server_entry.get()
            port = int(self.port_entry.get())

            private_key_path = self.private_key_entry.get()
            passphrase = self.passphrase_entry.get()

            key = paramiko.Ed25519Key.from_private_key_file(
                private_key_path, password=passphrase if passphrase else None)

            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            username = self.username_entry.get()
            self.ssh.connect(server_ip, port=port,
                             username=username, pkey=key)
            print(f"Connected to {server_ip}")

            self.sftp = self.ssh.open_sftp()

            messagebox.showinfo("Connection Successful",
                                f"Connected to {server_ip}")
            self.start_heartbeat()

            home_dir = f"/home/{username}"
            self.current_path = home_dir
            self.history = [home_dir]
            self.history_index = 0
            self.populate_file_tree(home_dir)

            self.download_button.config(state=tk.NORMAL)
            self.update_navigation_buttons()

        except Exception as e:
            messagebox.showerror("Connection Error",
                                 f"Failed to connect to {server_ip}: {e}")

    def start_heartbeat(self):
        self.heartbeat_thread = threading.Thread(
            target=self.heartbeat_check, daemon=True)
        self.heartbeat_thread.start()

    def heartbeat_check(self):
        while True:
            if self.ssh is not None and self.ssh.get_transport().is_active():
                self.update_heartbeat_indicator(True)
            else:
                self.update_heartbeat_indicator(False)
                break
            time.sleep(3)

    def update_heartbeat_indicator(self, is_connected):
        if is_connected:
            self.heartbeat_label.config(
                text="Connection Status: Connected", fg="green")
        else:
            self.heartbeat_label.config(
                text="Connection Status: Disconnected", fg="red")

        self.root.after(100, self.root.update_idletasks)

    def populate_file_tree(self, path):
        # Clear current tree view
        self.file_tree.delete(*self.file_tree.get_children())

        try:
            for file_attr in self.sftp.listdir_attr(path):
                file_name = file_attr.filename

                if file_name.startswith('.'):
                    continue

                file_type = "Directory" if stat.S_ISDIR(
                    file_attr.st_mode) else "File"
                self.file_tree.insert(
                    "", "end", iid=f"{path}/{file_name}", values=(file_name, file_type))

            self.file_tree.bind(
                "<Double-1>", lambda event: self.on_treeview_double_click(path))
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to list directory contents: {e}")

    def on_treeview_double_click(self, current_path):
        selected_item = self.file_tree.selection()
        if selected_item:
            selected_path = selected_item[0]
            item_type = self.file_tree.item(selected_path, "values")[1]
            if item_type == "Directory":
                self.navigate_to(selected_path)

    def navigate_to(self, path):
        self.current_path = path
        self.populate_file_tree(path)

        if self.history_index == len(self.history) - 1:
            self.history.append(path)
            self.history_index += 1
        else:
            self.history = self.history[:self.history_index + 1]
            self.history.append(path)
            self.history_index += 1

        self.update_navigation_buttons()

    def navigate_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_path = self.history[self.history_index]
            self.populate_file_tree(self.current_path)
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.back_button.config(
            state=tk.NORMAL if self.history_index > 0 else tk.DISABLED)

    def download_selected_file(self):
        selected_item = self.file_tree.selection()
        if selected_item:
            remote_path = selected_item[0]
            local_filename = remote_path.split("/")[-1]

            local_path = filedialog.asksaveasfilename(
                initialfile=local_filename)

            if not local_path:
                return

            threading.Thread(target=self.download_file_thread,
                             args=(remote_path, local_path)).start()

    def download_file_thread(self, remote_path, local_path):
        try:
            self.progress_bar['value'] = 0
            self.root.update_idletasks()

            file_size = self.sftp.stat(remote_path).st_size
            with open(local_path, 'wb') as f:
                def file_writer_callback(data, _):
                    if isinstance(data, bytes):
                        f.write(data)
                        self.progress_bar['value'] += len(data) / \
                            file_size * 100
                        self.root.after(10, self.root.update_idletasks)

                self.sftp.getfo(remote_path, f, callback=file_writer_callback)

            messagebox.showinfo(
                "Success", f"File downloaded successfully to {local_path}")
            self.progress_bar['value'] = 0

        except Exception as e:
            messagebox.showerror("Error", f"Failed to download file: {e}")
            self.progress_bar['value'] = 0

    def __del__(self):
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = SFTPClientApp(root)
    root.mainloop()
