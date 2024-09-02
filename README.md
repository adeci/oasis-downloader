# Oasis Download Client
Oasis is a small GUI SFTP client built with Tkinter. It allows users to connect securely to a remote server using SSH keys, browse files and directories, and download files. This was created to simplify file sharing with friends on a private server.

## Features

- **Secure Connection**: Connect to remote servers using SSH with private key authentication.
- **File Browser**: View and navigate directories and files on the remote server.
- **File Download**: Download selected files from the server to your local machine with a progress bar indicator.
- **Heartbeat Indicator**: Real-time connection status indicator to show if the connection is alive.
- **Multithreaded Operations**: GUI remains responsive during file downloads and connection monitoring.


## Requirements

- Python 3.6 or higher
- `paramiko` library for SSH connection
- `tkinter` library for GUI (included with Python)

## Quick Start

Download the latest release .exe from releases compiled using pyInstaller. 

## Manual Setup

1. **Clone the repository**:

    ```bash
    git clone https://github.com/adeci/oasis-downloader.git
    cd oasis-sftp-client
    ```
2. **Create and source Python virtual environment**:
    ```bash
    python3 -m venv env
    source env/bin/activate
    ```
3. **Get the required libraries**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Launch the application**:
    ```bash
    python oasis.py
    ```

5. **Optionally you can create an executable with pyinstaller**:
    ```bash
    pyinstaller --onefile --windowed --icon=oasis.ico oasis.py
    ```
    The executable will be in the dist folder.
