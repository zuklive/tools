#!/usr/bin/env python3

import requests
import asyncio
import aiohttp
import dns.asyncresolver
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import init, Fore, Back, Style
import pyfiglet
import signal
from datetime import datetime
import shutil
import json
import threading

init(autoreset=True)

# ============== GLOBAL REAL-TIME WRITER ==============
class RealTimeWriter:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.thread_lock = threading.Lock()
        self.files = {}
    
    def init_file(self, tool_name, domain=None):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if tool_name == "reverse":
            filename = f"reverse_ip_live_{timestamp}.txt"
        else:
            filename = f"subdomains_live_{timestamp}.txt"
        
        with self.thread_lock:
            self.files[tool_name] = filename
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {tool_name.upper()} SCAN RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("#" + "="*80 + "\n\n")
                f.flush()
        
        return filename
    
    def write_reverse_result(self, domain):
        with self.thread_lock:
            filename = self.files.get("reverse", "reverse_results.txt")
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(f"{domain}\n")
                f.flush()
                os.fsync(f.fileno())
    
    async def write_subdomain_result(self, subdomain):
        async with self.lock:
            filename = self.files.get("subdomain", "subdomain_results.txt")
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(f"{subdomain}\n")
                f.flush()
                os.fsync(f.fileno())
    
    def write_summary(self, tool_name, total, time_elapsed):
        with self.thread_lock:
            filename = self.files.get(tool_name)
            if filename:
                with open(filename, 'a', encoding='utf-8') as f:
                    f.write(f"\n# {'='*80}\n")
                    f.write(f"# SCAN COMPLETED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# TOTAL FOUND: {total}\n")
                    f.write(f"# TIME: {time_elapsed:.2f} seconds\n")
                    f.write(f"# {'='*80}\n")

writer = RealTimeWriter()

# ============== EPIC BANNER ==============
def show_epic_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    terminal_width = shutil.get_terminal_size().columns
    
    # ASCII Art Header
    banner = """
                                            ▒     ░                                       
                                           ▓▓     ▓▓▒                                     
                                         ▒▓▒▓    ▒▓▓▓                                     
                                         ▓ ▓▓▒   ▓▒▒▓▓                                    
                                      ▒▓▓▒ ▓▒▓▓▓▓▓  ▓▓▓▒                                  
                                ▒▓▓▓▓▓▓▓▓  ▒▒▓   ▓  ▒▒▓▓▓▓▓▓▓▒                            
                             ▓▓▓▓▓▒    ▓░  ░▓▒▓ ░▒   ▓▒▓   ▒▓▓▓▓▓▒                        
                ░░░░░░    ▓▓▓▓▒   ▒░▒ ▓▒░  ░▒▓▓░░▒   ░▓▒▒░▒▒▒  ▒▓▓▓▓    ░░░░░             
                ░░░░░░ ▒▓▓▓▒ ░░░  ░░░▒▓▒░    ▒▒▓▒▒    ░▓▓▓░░  ░░░ ▒▓▓▓▒ ░░░▒░░            
                 ░░░░░░░▒░ ░░ ░░   ░ ▒▓ ▒     ▓░▒▒     ▒▒▓▒   ░░ ░  ▒▓░░░░░░░             
             ░░░    ░░░ ░░░░░░░ ░░   ▒▓░░      ▓░  ▒░   ▓▒▓  ░  ░░░░░░ ░░░    ░░          
          ░░░░ ░░▒ ▓▓▓         ░░░ ▒▓▒▓▒ ░     ░░▒  ░░▒░▓░▓ ░░░         ▒▓▓░░░░ ░░░       
          ░░░░           ░░░  ▒░  ▓▒▒▓░░  ░       ░ ░ ░░░ ▓▒  ░▒  ░░░           ░ ░░      
          ░      ▓▓   ░░░ ░░  ░ ▒▓░▓▓▒░            ░▒▒  ░▒▒▒▓░ ░  ░░ ░░░   ▓▓             
           ░░   ▓▓░░░▒  ░░░    ░▓ ▓▓▒░       ▒▒▒░  ░▒▒▒▓▓░▓▒▒▓ ░   ░░   ▒░░░▓▓   ░░░      
             ░░ ▓▓   ░ ░░ ░ ░  ▓ ▓▓▒░        ░░▒  ░▒   ░▒  ▒▓▒ ░ ░ ░ ░░ ░   ▓▓  ░         
             ░░▒▓▒▒▒ ░ ░░     ▓░▓▒░            ░▒▒▒▒▒░  ░▒▓░▓▓       ░░ ░ ▒▒░▓▓ ░         
             ░░▓▓░░  ░ ░░    ▓░░░   ░░     ░ ░        ░   ░▒▓░▒▓▒    ░░ ░  ░ ▓▒ ░         
            ░░▒▒▓ ░  ░░░    ░▒ ▒▒░░░░      ▒  ░               ░▒▒░▓   ░░  ░░ ▒▒░░         
            ░░ ░░ ░░    ░░  ▓ ▓▓▒▒░        ▓     ░░     ░░       ▒▒ ░░    ░░ ▒▒ ░         
             ░░ ▒░░░░░░░░  ▒░░▒▒░   ░░     ▒░                   ▓░    ░░░░░░ ▒░ ░         
             ░░ ▒░ ░      ░▒ ░░  ░░░░      ░▒   ░ ░  ░▓ ▒▓▓░▒▓▓░            ░▒  ░         
             ░░ ▒▒ ░░  ░░ ▓ ░▒▒▒▒░    ░     ▓        ░▒▒  ░     ░  ░ ░   ░░ ░▒  ░         
                 ░░  ░    ▓▒     ░░░░       ▒▒    ░  ░▒▓     ░  ░  ░ ░  ░   ░  ░          
          ░░░░░░     ░    ▒▒         ░░      ▓        ░▒▓    ░  ░  ░   ░░       ░░░       
           ░░░                       ░   ░   ░▓    ░   ░▒▓                      ░░        
            ░░  ░▒▒▒▒▒▒▒░░░░                  ░▓        ░▒▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░░░ ░░         
             ░░     ░▓▓   ▒▓▒ ▓▓▓▓▓▓▓▓▓▓░      ░▒     ░▓▓▓▓▓▓▒ ▒▓▓▓▓▓▓▓▓▓     ░░░         
                ░░    ▓▓░▓▓▒     ▒▓    ▓▓░  ▒▓▒▒▓▓   ▒▓▒    ░▓▓    ▓▓░      ░░            
                 ░░    ▓▓▓░     ▒▓     ▓▓░ ▓░ ░░  ▓▓ ▓▓░     ▓▓    ▓▓     ░░              
                 ░░   ░▓▓▓▓    ▒▓░ ▓▓▓▓▓▒  ▓ ░    ▒▓ ▓▓░     ▓▓    ▓▓     ░░              
                 ░░  ▒▓▓ ▒▓▓   ▒▓░   ░▓▓░  ▓▓▓▒░▓▓▓▓ ▓▓░     ▓▓    ▓▓     ░░              
                 ░░░           ▒▓░     ▓▓▒   ▒▓░▓     ▒▓▓▓▓▓▓▒            ░░              
                     ░░░░▒░        ░░                              ░▒░░░░                 
                            ░░░░▒░       ░ ░  ░    ░░       ░▒░░░░                        
                                  ░░░░░░░░░        ░░░░░░░░░                              
                                          ░░░░░░░░░░                                      
"""
    
    print(Fore.CYAN + banner)
    
    # Animated subtitle
    subtitle = "⚡ X7ROOT - REVERSE IP & SUBDOMAIN SCANNER ⚡"
    padding = (terminal_width - len(subtitle)) // 2
    print(Fore.YELLOW + " " * padding + subtitle)
    
    # Stats line
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    print(Fore.GREEN + "\n" + " " * (padding-10) + f"⚡ Telegram channel | https://t.me/x7rootv3 ⚡")
    
    print(Fore.MAGENTA + "\n" + "─" * terminal_width + Style.RESET_ALL)

def show_tool_banner(tool_name):
    os.system('cls' if os.name == 'nt' else 'clear')
    terminal_width = shutil.get_terminal_size().columns
    
    if "REVERSE" in tool_name.upper():
        banner = f"""
{Fore.CYAN}╔{'═'*70}╗
{Fore.CYAN}║{Fore.YELLOW}{' ' * 25}🔍 REVERSE IP LOOKUP 🔍{Fore.CYAN}{' ' * 24}║
{Fore.CYAN}╠{'═'*70}╣
{Fore.CYAN}║{Fore.WHITE}  • Find all domains hosted on same IP     • Mass scanning supported     {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}  • Real-time results saving                • Multi-threaded engine       {Fore.CYAN}║
{Fore.CYAN}╚{'═'*70}╝{Style.RESET_ALL}
"""
    else:
        banner = f"""
{Fore.CYAN}╔{'═'*70}╗
{Fore.CYAN}║{Fore.GREEN}{' ' * 25}🌐 SUBDOMAIN SCANNER 🌐{Fore.CYAN}{' ' * 25}║
{Fore.CYAN}╠{'═'*70}╣
{Fore.CYAN}║{Fore.WHITE}  • Discover hidden subdomains              • 1000+ wordlist             {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}  • Instant DNS resolution                  • Clean output - one per line {Fore.CYAN}║
{Fore.CYAN}╚{'═'*70}╝{Style.RESET_ALL}
"""
    
    print(banner)

# ============== REVERSE IP ==============
import threading

class ReverseIPScanner:
    def __init__(self):
        self.results = set()
        self.processed = set()
        self.found_count = 0
        self.lock = threading.Lock()
        self.start_time = 0
    
    def reverse_ip_lookup(self, ip_or_domain):
        url = f"https://api.webscan.cc/?action=query&ip={ip_or_domain}"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            if response.text.strip() == "":
                return []
            
            try:
                data = response.json()
            except:
                return []
            
            valid_domains = []
            for item in data:
                domain = item.get("domain")
                if domain and domain != "defacer.net":
                    if domain.startswith("www."):
                        domain = domain[4:]
                    valid_domains.append(domain)
            
            return valid_domains
        
        except:
            return []
    
    def process_file(self, input_file, max_threads=30):
        with open(input_file, 'r') as f:
            items = [line.strip() for line in f if line.strip()]
        
        total_items = len(items)
        self.found_count = 0
        self.processed = set()
        self.start_time = time.time()
        
        output_file = writer.init_file("reverse")
        
        # Progress bar setup
        bar_width = 50
        completed = 0
        
        with ThreadPoolExecutor(max_threads) as executor:
            futures = {}
            for item in items:
                futures[executor.submit(self.reverse_ip_lookup, item)] = item
            
            for future in as_completed(futures):
                item = futures[future]
                result = future.result()
                completed += 1
                
                # Calculate progress
                progress = completed / total_items
                filled = int(bar_width * progress)
                bar = '█' * filled + '░' * (bar_width - filled)
                
                # Clear line and print progress
                sys.stdout.write('\033[K')
                
                if result:
                    self.found_count += len(result)
                    for domain in result:
                        if domain not in self.processed:
                            self.processed.add(domain)
                            writer.write_reverse_result(domain)
                    
                    elapsed = time.time() - self.start_time
                    speed = completed / elapsed if elapsed > 0 else 0
                    
                    print(f"\r{Fore.CYAN}[{bar}] {Fore.YELLOW}{progress*100:>5.1f}% {Fore.WHITE}| "
                          f"{Fore.GREEN}Found: {self.found_count:>4} {Fore.WHITE}| "
                          f"{Fore.BLUE}{item:<20} {Fore.WHITE}| "
                          f"{Fore.MAGENTA}{len(result)} domains{Fore.WHITE} | "
                          f"{Fore.CYAN}{speed:.1f}/s    ", end='', flush=True)
                else:
                    elapsed = time.time() - self.start_time
                    speed = completed / elapsed if elapsed > 0 else 0
                    
                    print(f"\r{Fore.CYAN}[{bar}] {Fore.YELLOW}{progress*100:>5.1f}% {Fore.WHITE}| "
                          f"{Fore.GREEN}Found: {self.found_count:>4} {Fore.WHITE}| "
                          f"{Fore.RED}{item:<20} {Fore.WHITE}| "
                          f"{Fore.RED}0 domains{Fore.WHITE}    | "
                          f"{Fore.CYAN}{speed:.1f}/s    ", end='', flush=True)
        
        print("\n")
        return output_file, self.found_count, total_items

# ============== SUBDOMAIN ==============
class SubdomainScanner:
    def __init__(self):
        self.found = 0
        self.results = {}
        self.start_time = 0
        self.resolvers = ['8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1', '9.9.9.9']
        
        self.subs = [
            'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1',
            'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'ns3', 'test',
            'staging', 'dev', 'api', 'admin', 'administrator', 'blog', 'shop',
            'store', 'support', 'help', 'forum', 'docs', 'portal', 'app',
            'mobile', 'm', 'secure', 'vpn', 'remote', 'exchange', 'owa',
            'cloud', 'crm', 'erp', 'backup', 'git', 'svn', 'jenkins', 'jira',
            'wiki', 'media', 'cdn', 'static', 'assets', 'images', 'img',
            'video', 'live', 'chat', 'community', 'social', 'network',
            'analytics', 'metrics', 'stats', 'status', 'monitor', 'tracking',
            'auth', 'login', 'signin', 'register', 'signup', 'account',
            'my', 'beta', 'alpha', 'demo', 'sandbox', 'develop', 'testing',
            'qa', 'stage', 'preprod', 'prod', 'production', 'release',
            'corp', 'internal', 'private', 'public', 'external', 'partner',
            'customer', 'user', 'member', 'staff', 'employee', 'hr',
            'billing', 'payment', 'checkout', 'cart', 'order', 'shipping',
            'track', 'delivery', 'download', 'upload', 'file', 'data',
            'database', 'db', 'mysql', 'postgres', 'redis', 'search',
            'api-docs', 'swagger', 'graphql', 'rest', 'websocket',
            'proxy', 'gateway', 'firewall', 'security', 'backup',
            'archive', 'storage', 'printer', 'camera', 'iot', 'smart',
            'conference', 'meet', 'zoom', 'teams', 'slack', 'github',
            'gitlab', 'docker', 'kubernetes', 'jenkins', 'grafana',
            'devops', 'ci', 'cd', 'pipeline', 'build', 'deploy',
            'stage', 'prod', 'dev', 'test', 'staging', 'production',
            'admin1', 'admin2', 'admin3', 'backup1', 'backup2',
            'server1', 'server2', 'server3', 'node1', 'node2',
            'cluster1', 'cluster2', 'db1', 'db2', 'cache1', 'cache2',
            'redis1', 'redis2', 'mongo1', 'mongo2', 'mysql1', 'mysql2',
            'postgres1', 'postgres2', 'kafka1', 'kafka2', 'rabbit1', 'rabbit2'
        ]
    
    async def check_subdomain(self, sub, domain, sem, found_counter):
        async with sem:
            fqdn = f"{sub}.{domain}"
            
            try:
                resolver = dns.asyncresolver.Resolver()
                resolver.nameservers = self.resolvers
                resolver.timeout = 1.5
                resolver.lifetime = 2
                
                answers = await resolver.resolve(fqdn, 'A')
                
                if answers:
                    ips = [str(x) for x in answers[:2]]
                    
                    async with found_counter['lock']:
                        found_counter['count'] += 1
                        total = found_counter['count']
                        
                        elapsed = time.time() - self.start_time
                        speed = total / elapsed if elapsed > 0 else 0
                        
                        # Clear line and print
                        sys.stdout.write('\033[K')
                        print(f"\r{Fore.GREEN}► {Fore.WHITE}{fqdn:<45} "
                              f"{Fore.BLUE}{', '.join(ips):<25} "
                              f"{Fore.YELLOW}[{total} found] "
                              f"{Fore.CYAN}[{speed:.1f}/s]{Style.RESET_ALL}", flush=True)
                    
                    await writer.write_subdomain_result(fqdn)
                    
                    if domain not in self.results:
                        self.results[domain] = []
                    self.results[domain].append(fqdn)
                    
                    return fqdn
            except:
                pass
            return None
    
    async def scan_domain(self, domain, sem, found_counter):
        tasks = []
        for sub in self.subs:
            task = asyncio.create_task(self.check_subdomain(sub, domain, sem, found_counter))
            tasks.append(task)
            await asyncio.sleep(0.005)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        found = len([r for r in results if r])
        return found
    
    async def scan_file(self, input_file, threads):
        with open(input_file, 'r') as f:
            domains = [line.strip().lower() for line in f if line.strip()]
        
        if not domains:
            return None, 0, []
        
        writer.init_file("subdomain")
        sem = asyncio.Semaphore(threads)
        
        self.start_time = time.time()
        self.found = 0
        self.results = {}
        
        found_counter = {'count': 0, 'lock': asyncio.Lock()}
        
        print(f"\n{Fore.CYAN}╔{'═'*80}╗")
        print(f"{Fore.CYAN}║{Fore.WHITE}{' ' * 30}⚡ LIVE SUBDOMAIN DISCOVERY ⚡{Fore.CYAN}{' ' * 30}║")
        print(f"{Fore.CYAN}╚{'═'*80}╝{Style.RESET_ALL}\n")
        
        for i, domain in enumerate(domains, 1):
            print(f"{Fore.MAGENTA}┌─[{Fore.YELLOW}{i}/{len(domains)}{Fore.MAGENTA}]─[{Fore.CYAN}{domain}{Fore.MAGENTA}]")
            print(f"{Fore.MAGENTA}└─{'─'*60}")
            
            await self.scan_domain(domain, sem, found_counter)
            
            # Show domain summary
            domain_found = len(self.results.get(domain, []))
            print(f"\n{Fore.GREEN}  ✓ Found {Fore.YELLOW}{domain_found}{Fore.GREEN} subdomains for {Fore.CYAN}{domain}{Style.RESET_ALL}\n")
            
            await asyncio.sleep(0.3)
        
        return writer.files.get("subdomain"), found_counter['count'], domains

# ============== EPIC MENU ==============
def show_epic_menu():
    terminal_width = shutil.get_terminal_size().columns
    
    menu_frame = f"""
{Fore.CYAN}╔{'═'*70}╗
{Fore.CYAN}║{Fore.YELLOW}{' ' * 28}⚡ MAIN MENU ⚡{Fore.CYAN}{' ' * 29}║
{Fore.CYAN}╠{'═'*70}╣
{Fore.CYAN}║{Fore.WHITE}                                                                      {Fore.CYAN}║
{Fore.CYAN}║{Fore.GREEN}     [1] 🔍 REVERSE IP LOOKUP                                         {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}         • Find all domains hosted on same IP                         {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}         • Real-time saving | Mass scan | Threading                   {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}                                                                      {Fore.CYAN}║
{Fore.CYAN}║{Fore.GREEN}     [2] 🌐 SUBDOMAIN SCANNER                                         {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}         • Discover hidden subdomains                                 {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}         • 1000+ wordlist | DNS brute | Instant saving                {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}                                                                      {Fore.CYAN}║
{Fore.CYAN}║{Fore.RED}     [0] ❌ EXIT                                                       {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}                                                                      {Fore.CYAN}║
{Fore.CYAN}╚{'═'*70}╝{Style.RESET_ALL}
"""
    print(menu_frame)

# ============== MAIN ==============
def reverse_ip_mode():
    show_tool_banner("REVERSE IP")
    
    while True:
        input_file = input(f"{Fore.YELLOW}[?] Enter domains/IPs file: {Fore.WHITE}")
        if input_file.strip():
            if os.path.exists(input_file):
                break
            else:
                print(f"{Fore.RED}✗ File not found!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ File required!{Style.RESET_ALL}")
    
    while True:
        try:
            threads = input(f"{Fore.YELLOW}[?] Threads (1-30) [30]: {Fore.WHITE}")
            if not threads.strip():
                threads = 30
                break
            threads = int(threads)
            if 1 <= threads <= 30:
                break
            else:
                print(f"{Fore.RED}✗ Use 1-30{Style.RESET_ALL}")
        except:
            print(f"{Fore.RED}✗ Enter a number{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}▶ Initializing Reverse IP Scan...")
    print(f"{Fore.WHITE}  • Input: {Fore.YELLOW}{input_file}")
    print(f"{Fore.WHITE}  • Threads: {Fore.GREEN}{threads}")
    print(f"{Fore.WHITE}  • Output: {Fore.MAGENTA}{writer.init_file('reverse')}{Style.RESET_ALL}\n")
    
    confirm = input(f"{Fore.YELLOW}[?] Launch scan? (y/n): {Fore.WHITE}")
    
    if confirm.lower() in ['y', 'yes', '']:
        scanner = ReverseIPScanner()
        output_file, total, processed = scanner.process_file(input_file, threads)
        
        elapsed = time.time() - scanner.start_time
        
        print(f"\n\n{Fore.GREEN}╔{'═'*50}╗")
        print(f"{Fore.GREEN}║{' ' * 18}✓ SCAN COMPLETE ✓{' ' * 18}║")
        print(f"{Fore.GREEN}╚{'═'*50}╝{Style.RESET_ALL}")
        print(f"\n{Fore.WHITE}  📁 Input file: {Fore.CYAN}{input_file}")
        print(f"{Fore.WHITE}  🔍 IPs/Domains scanned: {Fore.YELLOW}{processed}")
        print(f"{Fore.WHITE}  🌐 Total domains found: {Fore.GREEN}{total}")
        print(f"{Fore.WHITE}  ⏱️  Time elapsed: {Fore.MAGENTA}{elapsed:.2f} seconds")
        print(f"{Fore.WHITE}  💾 Results saved: {Fore.GREEN}{output_file}{Style.RESET_ALL}")
        
        writer.write_summary("reverse", total, elapsed)
    else:
        print(f"{Fore.RED}✗ Scan cancelled{Style.RESET_ALL}")
    
    input(f"\n{Fore.YELLOW}[?] Press Enter to continue...{Style.RESET_ALL}")

def subdomain_mode():
    show_tool_banner("SUBDOMAIN")
    
    while True:
        input_file = input(f"{Fore.YELLOW}[?] Enter domains file: {Fore.WHITE}")
        if input_file.strip():
            if os.path.exists(input_file):
                break
            else:
                print(f"{Fore.RED}✗ File not found!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ File required!{Style.RESET_ALL}")
    
    while True:
        try:
            threads = input(f"{Fore.YELLOW}[?] Threads (1-500) [150]: {Fore.WHITE}")
            if not threads.strip():
                threads = 150
                break
            threads = int(threads)
            if 1 <= threads <= 500:
                break
            else:
                print(f"{Fore.RED}✗ Use 1-500{Style.RESET_ALL}")
        except:
            print(f"{Fore.RED}✗ Enter a number{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}▶ Initializing Subdomain Scanner...")
    print(f"{Fore.WHITE}  • Input: {Fore.YELLOW}{input_file}")
    print(f"{Fore.WHITE}  • Threads: {Fore.GREEN}{threads}")
    print(f"{Fore.WHITE}  • Wordlist: {Fore.BLUE}{len(SubdomainScanner().subs)} entries")
    print(f"{Fore.WHITE}  • Output: {Fore.MAGENTA}subdomains_live_[timestamp].txt{Style.RESET_ALL}\n")
    
    confirm = input(f"{Fore.YELLOW}[?] Launch scan? (y/n): {Fore.WHITE}")
    
    if confirm.lower() in ['y', 'yes', '']:
        scanner = SubdomainScanner()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        filename, total, domains = loop.run_until_complete(scanner.scan_file(input_file, threads))
        loop.close()
        
        elapsed = time.time() - scanner.start_time
        
        print(f"\n\n{Fore.GREEN}╔{'═'*50}╗")
        print(f"{Fore.GREEN}║{' ' * 18}✓ SCAN COMPLETE ✓{' ' * 18}║")
        print(f"{Fore.GREEN}╚{'═'*50}╝{Style.RESET_ALL}")
        print(f"\n{Fore.WHITE}  📁 Input file: {Fore.CYAN}{input_file}")
        print(f"{Fore.WHITE}  🌐 Domains scanned: {Fore.YELLOW}{len(domains)}")
        print(f"{Fore.WHITE}  🔍 Subdomains found: {Fore.GREEN}{total}")
        print(f"{Fore.WHITE}  ⏱️  Time elapsed: {Fore.MAGENTA}{elapsed:.2f} seconds")
        print(f"{Fore.WHITE}  💾 Results saved: {Fore.GREEN}{filename}{Style.RESET_ALL}")
        
        writer.write_summary("subdomain", total, elapsed)
    else:
        print(f"{Fore.RED}✗ Scan cancelled{Style.RESET_ALL}")
    
    input(f"\n{Fore.YELLOW}[?] Press Enter to continue...{Style.RESET_ALL}")

def main():
    while True:
        show_epic_banner()
        show_epic_menu()
        
        choice = input(f"{Fore.YELLOW}[?] SELECT OPTION [0-2]: {Fore.WHITE}").strip()
        
        if choice == '1':
            reverse_ip_mode()
        elif choice == '2':
            subdomain_mode()
        elif choice == '0':
            print(f"\n{Fore.GREEN}╔{'═'*50}╗")
            print(f"{Fore.GREEN}║{' ' * 16}👋 GOODBYE! HAPPY HACKING 👋{' ' * 16}║")
            print(f"{Fore.GREEN}╚{'═'*50}╝{Style.RESET_ALL}")
            sys.exit(0)
        else:
            print(f"{Fore.RED}✗ Invalid option!{Style.RESET_ALL}")
            time.sleep(1)

def signal_handler(sig, frame):
    print(f"\n\n{Fore.RED}╔{'═'*50}╗")
    print(f"{Fore.RED}║{' ' * 18}⚠ INTERRUPTED ⚠{' ' * 19}║")
    print(f"{Fore.RED}╚{'═'*50}╝{Style.RESET_ALL}")
    sys.exit(0)

if __name__ == "__main__":
    try:
        import threading
        import shutil
        import psutil
    except ImportError:
        print(f"{Fore.RED}[!] Installing required packages...{Style.RESET_ALL}")
        os.system("pip install psutil shutil")
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}╔{'═'*50}╗")
        print(f"{Fore.RED}║{' ' * 18}⚠ INTERRUPTED ⚠{' ' * 19}║")
        print(f"{Fore.RED}╚{'═'*50}╝{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
