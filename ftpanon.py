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
      -r, --retries   Number of retries for failed connections (default: 1)
      --log-level     Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL; default: INFO)
      --check-only    Only check connectivity, do not attempt anonymous logins (default: False)

    Example:
      python script.py -f iplist.txt -t 10 -r 5 --log-level DEBUG --check-only

    {reset}""")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Check for anonymous FTP logins.')
    parser.add_argument('-f', '--file', default='iplist.txt', help='File containing list of IP addresses')
    parser.add_argument('-t', '--timeout', type=int, default=5, help='FTP connection timeout in seconds')
    parser.add_argument('-r', '--retries', type=int, default=1, help='Number of retries for failed connections')  # Default set to 1
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
            config = json.load(file)
            return {
                'file': config.get('file', 'iplist.txt'),
                'timeout': config.get('timeout', 5),
                'retries': config.get('retries', 1)  # Default set to 1
            }
    except FileNotFoundError:
        print(Fore.RED + "Configuration file not found." + Style.RESET_ALL)
        return {
            'file': 'iplist.txt',
            'timeout': 5,
            'retries': 1  # Default set to 1
        }

def print_progress_bar(current, total):
    bar_length = 40
    progress = int((current / total) * bar_length)
    bar = f"[{'#' * progress}{'.' * (bar_length - progress)}]"
    print(f'\r{bar} {current}/{total}', end='')

def check_connectivity(hostname, port=21, timeout=5):
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            print(Fore.GREEN + f'[+] {hostname} is reachable.' + Style.RESET_ALL)
            return True
    except (socket.timeout, ConnectionRefusedError) as e:
        print(Fore.RED + f'[-] {hostname} is not reachable: {e}' + Style.RESET_ALL)
        return False

def anonLogin(hostname, timeout, retries):
    attempt = 0
    while attempt < retries:
        try:
            ftp = ftplib.FTP(hostname, timeout=timeout)
            ftp.login('anonymous', 'ilove@you.com')
            
            # Capture and print the server response after login attempt
            response = ftp.getresp()
            print(Fore.GREEN + f'\n[*] {hostname} FTP Anonymous Logon Succeeded. Server response: {response}' + Style.RESET_ALL)
            logging.info(f'{hostname} FTP Anonymous Logon Succeeded. Server response: {response}')
            
            ftp.quit()
            return True
        except ftplib.all_errors as e:
            attempt += 1
            if attempt < retries:
                print(Fore.YELLOW + f'[!] Attempt {attempt}/{retries} failed for {hostname}. Retrying...' + Style.RESET_ALL)
                time.sleep(2)  # Wait before retrying
            else:
                # Capture and print server response if available
                if hasattr(e, 'args') and len(e.args) > 1:
                    response = e.args[1]
                else:
                    response = str(e)
                print(Fore.RED + f'\n[-] {hostname} FTP Anonymous Logon Failed: {response}' + Style.RESET_ALL)
                logging.info(f'{hostname} FTP Anonymous Logon Failed. Reason: {response}')
    return False

def process_host(host, timeout, retries, check_only, results):
    host = strip_url_prefix(host)
    if check_connectivity(host):
        results['reachable'].append(host)
        if not check_only:
            if anonLogin(host, timeout, retries):
                results['anon_login'].append(host)
            else:
                results['anon_failures'].append(host)
    else:
        results['unreachable'].append(host)
    print()  # Ensure each result is printed on a new line

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
            else:
                hosts = [host.strip() for host in content.replace(',', '\n').splitlines()]
                # Handle URLs with prefixes
                return [strip_url_prefix(host) for host in hosts]
    except FileNotFoundError:
        print(Fore.RED + f"Error: File {file_path} not found." + Style.RESET_ALL)
        return []

def save_summary(results):
    with open('summary.txt', 'w') as file:
        file.write("Summary of FTP Anonymous Login Scan\n")
        file.write("="*40 + "\n\n")

        file.write(Fore.GREEN + "Reachable IPs:\n" + Style.RESET_ALL)
        for ip in results['reachable']:
            file.write(f'[+] {ip}\n')
        
        file.write(Fore.RED + "\nUnreachable IPs:\n" + Style.RESET_ALL)
        for ip in results['unreachable']:
            file.write(f'[-] {ip}\n')
        
        file.write(Fore.GREEN + "\nIPs with Successful Anonymous Logins:\n" + Style.RESET_ALL)
        for ip in results['anon_login']:
            file.write(f'[+] {ip}\n')
        
        file.write(Fore.RED + "\nIPs with Failed Anonymous Logins:\n" + Style.RESET_ALL)
        for ip in results['anon_failures']:
            file.write(f'[-] {ip}\n')

    print(Fore.GREEN + "Summary saved to 'summary.txt'" + Style.RESET_ALL)

def main():
    args = parse_arguments()
    setup_logging(args.log_level.upper())
    print_banner()

    if not confirm_action("Do you want to proceed with the scan? (y/n): "):
        print("Exiting...")
        return

    hosts = load_hosts(args.file)
    if not hosts:
        return

    results = {
        'reachable': [],
        'unreachable': [],
        'anon_login': [],
        'anon_failures': []
    }

    print("Processing IPs...")
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_host, host, args.timeout, args.retries, args.check_only, results) for host in hosts]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Progress"):
            pass

    print(Fore.GREEN + "\nProcessing complete." + Style.RESET_ALL)
    save_summary(results)

if __name__ == '__main__':
    main()
