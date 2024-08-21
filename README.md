# FTP Anonymous Login Checker

## Overview
![2024-08-21 13_03_36-kali-linux-2024 2-virtualbox-amd64  Running  - Oracle VM VirtualBox](https://github.com/user-attachments/assets/8a4edf09-f398-4dc2-ac4f-c9974dce6cba)

The FTP Anonymous Login Checker is a Python script that verifies anonymous FTP login capabilities on a list of IP addresses. The script checks connectivity and attempts anonymous logins to FTP servers. It also provides options for custom timeouts, retry attempts, and logging levels.

## Features

- **Check Connectivity:** Verify if an IP address is reachable and accepting connections.
- **Anonymous Login Attempt:** Optionally attempt to log in to FTP servers using anonymous credentials.
- **Configurable Settings:** Set custom timeouts, retry attempts, and logging levels.
- **Progress Tracking:** Monitor the progress of IP processing with a progress bar.
- **Error Handling:** Provides detailed error messages and instructions if the IP list is empty or improperly formatted.

## Requirements

- Python 3.x
- `colorama` package for colored output
- `tqdm` package for progress bar
- `concurrent.futures` for parallel processing

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/lokii-git/ftpanon.git
   cd ftpanon
