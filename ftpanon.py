#!/usr/bin/env python3
import ftplib
import argparse
import logging
import time
import json
import socket
from colorama import Fore, Style
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

# Setup logging
def setup_logging(log_level):
    logging.basicConfig(
        filename='ftp_anonymous_login.log',
        level=log_level,
        format='%(asctime)s - %(message)s'
    )

def print_banner():
    orange = '\033[33m'  # ANSI escape code for orange
    reset = '\033[0m'    # ANSI escape code to reset color
    print(f"""{orange}
    ________________     ___    _   ______  _   __
   / ____/_  __/ __ \   /   |  / | / / __ \/ | / /
  / /_    / / / /_/ /  / /| | /  |/ / / / /  |/ / 
 / __/   / / / ____/  / ___ |/ /|  / /_/ / /|  /  
/_/     /_/ /_/      /_/  |_/_/ |_/\____/_/ |_/   
                                              
           Created by Lokii

    Description:
    This script checks for anonymous FTP login capabilities on a list of IP addresses.
    It performs the following tasks:
    - Checks if the IP address is reachable and accepting connections.
    - Optionally attempts to log in to the FTP service using anonymous credentials.
    - Logs and prints results for each IP address, including successes and failures.
    - Allows for configuration of timeout, retry attempts, and logging levels.

    Usage:
      -f, --file      File containing the list of IP addresses (default: iplist.txt)
      -t, --timeout   FTP connection timeout in seconds (default: 5)
      -r, --retries   Number of retries for failed connections (default: 3)
      --log-level     Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL; default: INFO)
      --check-only    Only check connectivity, do not attempt anonymous logins (default: False)

    Example:
      python script.py -f iplist.txt -t 10 -r 5 --log-level DEBUG --check-only

    {reset}""")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Check for anonymous FTP logins.')
    parser.add_argument('-f', '--file', default='iplist.txt', help='File containing list of IP addresses')
    parser.add_argument('-t', '--timeout', type=int, default=5, help='FTP connection timeout in seconds')
    parser.add_argument('-r', '--retries', type=int, default=3, help='Number of retries for failed connections')
    parser.add_argument('--log-level', default='INFO', help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('--check-only', action='store_true', help='Only check connectivity, do not attempt anonymous logins')
    args = parser.parse_args()
    
    if args.timeout <= 0:
        parser.error("Timeout must be a positive integer.")
    if args.retries < 0:
        parser.error("Retries must be a non-negative integer.")
    
    return args

def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(Fore.RED + "Configuration file not found." + Style.RESET_ALL)
        return {}

def print_progress_bar(current, total):
    bar_length = 40
    progress = int((current / total) * bar_length)
    bar = f"[{'#' * progress}{'.' * (bar_length - progress)}]"
    print(f'\rProgress: {bar} {current}/{total}', end='')

def check_connectivity(hostname, port=21, timeout=5):
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def anonLogin(hostname, timeout, retries):
    for attempt in range(retries):
        try:
            ftp = ftplib.FTP(hostname, timeout=timeout)
            ftp.login('anonymous', 'ilove@you.com')
            print(Fore.GREEN + '\n[*] ' + str(hostname) + ' FTP Anonymous Logon Succeeded.' + Style.RESET_ALL)
            logging.info(f'{hostname} FTP Anonymous Logon Succeeded.')
            ftp.quit()
            return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retrying
            else:
                print(Fore.RED + '\n[-] ' + str(hostname) + ' FTP Anonymous Logon Failed.' + Style.RESET_ALL)
                logging.info(f'{hostname} FTP Anonymous Logon Failed. Reason: {e}')
    return False

def process_host(host, timeout, retries, check_only):
    host = strip_url_prefix(host)
    if check_connectivity(host):
        if not check_only:
            anonLogin(host, timeout, retries)
    else:
        print(Fore.RED + f'[-] {host} is not reachable or does not accept connections.' + Style.RESET_ALL)
        logging.info(f'{host} is not reachable or does not accept connections.')

def strip_url_prefix(url):
    parsed_url = urlparse(url)
    return parsed_url.hostname if parsed_url.hostname else url

def confirm_action(prompt):
    response = input(prompt).lower()
    return response in ('y', 'yes')

def load_hosts(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read().strip()
            if not content:
                print(Fore.RED + "Error: IP list is empty." + Style.RESET_ALL)
                print("Instructions for Adding IP Addresses:")
                print("1. Open the file specified with -f or --file.")
                print("2. Add each IP address on a new line or separate them with commas.")
                print("   Example:")
                print("   192.168.1.1")
                print("   192.168.1.2, 192.168.1.3")
                print("3. Save the file and re-run the script.")
                return []
            
            # Handle IPs with URL prefixes and various delimiters
            hosts = [strip_url_prefix(ip.strip()) for ip in content.replace('\n', ',').split(',') if ip.strip()]
            if not hosts:
                print(Fore.RED + "Error: IP list is empty." + Style.RESET_ALL)
                print("Instructions for Adding IP Addresses:")
                print("1. Open the file specified with -f or --file.")
                print("2. Add each IP address on a new line or separate them with commas.")
                print("   Example:")
                print("   192.168.1.1")
                print("   192.168.1.2, 192.168.1.3")
                print("3. Save the file and re-run the script.")
            return hosts
    except FileNotFoundError:
        print(Fore.RED + "Error: File not found." + Style.RESET_ALL)
        print("Instructions for Adding IP Addresses:")
        print("1. Create a file named 'iplist.txt' or specify a different file with -f or --file.")
        print("2. Add each IP address on a new line or separate them with commas.")
        print("   Example:")
        print("   192.168.1.1")
        print("   192.168.1.2, 192.168.1.3")
        print("3. Save the file and re-run the script.")
        return []

def main():
    args = parse_arguments()
    setup_logging(getattr(logging, args.log_level.upper(), logging.INFO))
    
    print_banner()
    
    config = load_config('config.json')
    file_path = config.get('file', args.file)
    timeout = config.get('timeout', args.timeout)
    retries = config.get('retries', args.retries)
    check_only = args.check_only

    if not confirm_action('Do you want to proceed with the scan? (y/n): '):
        print("Scan aborted.")
        return

    Hosts = load_hosts(file_path)
    if not Hosts:
        return

    total_hosts = len(Hosts)
    print("Processing IPs...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_host, host, timeout, retries, check_only) for host in Hosts]
        for index, future in enumerate(tqdm(futures, desc="Progress", unit="host", ncols=100)):
            future.result()  # Ensure any exceptions are raised

    print(Fore.GREEN + "\nProcessing complete." + Style.RESET_ALL)
    logging.info('Script completed.')

if __name__ == "__main__":
    main()
