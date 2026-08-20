#!/usr/bin/env python3
"""
Cosmos Science Fact-Checking CLI
A command-line interface for submitting and viewing scientific claims and debunked myths
"""

import requests
import json
import sys
from datetime import datetime
from typing import Optional, List
import os

# ANSI color codes
class Colors:
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CosmosAPI:
    """CLI client for Cosmos API"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
    
    def print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}🌌 {text}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}\n")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.RED}✗ {text}{Colors.RESET}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")
    
    def check_connection(self) -> bool:
        """Check if API is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_input(self, prompt: str, required: bool = True) -> str:
        """Get user input with validation"""
        while True:
            user_input = input(f"{Colors.CYAN}➜ {prompt}{Colors.RESET} ").strip()
            if user_input or not required:
                return user_input
            print(f"{Colors.RED}This field is required.{Colors.RESET}")
    
    def get_multiline_input(self, prompt: str) -> str:
        """Get multiline input from user"""
        print(f"{Colors.CYAN}{prompt} (press Enter twice to finish):{Colors.RESET}")
        lines = []
        empty_count = 0
        while True:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)
        return "\n".join(lines)
    
    def get_choice(self, prompt: str, options: List[tuple]) -> str:
        """Get choice from user"""
        print(f"\n{Colors.CYAN}{prompt}{Colors.RESET}")
        for i, (key, label) in enumerate(options, 1):
            print(f"  {Colors.BOLD}{i}{Colors.RESET}) {label}")
        
        while True:
            try:
                choice = int(input(f"{Colors.CYAN}➜ Select (1-{len(options)}): {Colors.RESET}"))
                if 1 <= choice <= len(options):
                    return options[choice - 1][0]
                print(f"{Colors.RED}Invalid choice. Please select 1-{len(options)}.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}Please enter a number.{Colors.RESET}")
    
    def submit_claim(self):
        """Submit a new claim for fact-checking"""
        self.print_header("Submit a Claim")
        
        title = self.get_input("Claim Title")
        description = self.get_input("Brief Description", required=False)
        claim_text = self.get_multiline_input("Full Claim Text")
        
        status = self.get_choice(
            "Verification Status:",
            [
                ("pending", "Pending Review"),
                ("verified", "Verified True"),
                ("false", "Verified False")
            ]
        )
        
        sources = self.get_input("Sources (comma-separated URLs)", required=False)
        author = self.get_input("Your Name", required=False)
        
        payload = {
            "title": title,
            "description": description,
            "claim_text": claim_text,
            "verification_status": status,
            "sources": sources,
            "author": author or "Anonymous"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/claims",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 201:
                self.print_success("Claim submitted successfully!")
                print(f"\n{Colors.GRAY}Claim ID: {response.json().get('id', 'N/A')}{Colors.RESET}")
            else:
                self.print_error(f"Failed to submit claim: {response.json().get('message', 'Unknown error')}")
        except Exception as e:
            self.print_error(f"Connection error: {str(e)}")
    
    def submit_myth(self):
        """Submit a new myth to debunk"""
        self.print_header("Submit a Myth to Debunk")
        
        title = self.get_input("Myth Title")
        description = self.get_input("Myth Description", required=False)
        debunked = self.get_multiline_input("Debunked Explanation")
        evidence = self.get_multiline_input("Scientific Evidence")
        sources = self.get_input("Sources (comma-separated URLs)", required=False)
        author = self.get_input("Your Name", required=False)
        
        payload = {
            "myth_title": title,
            "myth_description": description,
            "debunked_explanation": debunked,
            "scientific_evidence": evidence,
            "sources": sources,
            "author": author or "Anonymous"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/myths",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 201:
                self.print_success("Myth submitted successfully!")
                print(f"\n{Colors.GRAY}Myth ID: {response.json().get('id', 'N/A')}{Colors.RESET}")
            else:
                self.print_error(f"Failed to submit myth: {response.json().get('message', 'Unknown error')}")
        except Exception as e:
            self.print_error(f"Connection error: {str(e)}")
    
    def display_claim(self, claim: dict):
        """Display a formatted claim"""
        status_color = Colors.GREEN
        status_icon = "✓"
        
        if claim.get('verification_status') == 'false':
            status_color = Colors.RED
            status_icon = "✗"
        elif claim.get('verification_status') == 'pending':
            status_color = Colors.YELLOW
            status_icon = "⏳"
        
        print(f"\n{Colors.BOLD}{claim.get('title', 'Untitled')}{Colors.RESET}")
        print(f"{status_color}{status_icon} {claim.get('verification_status', 'unknown').upper()}{Colors.RESET}")
        print(f"{Colors.GRAY}By {claim.get('author', 'Anonymous')} • {claim.get('created_at', 'N/A')}{Colors.RESET}")
        
        if claim.get('description'):
            print(f"{Colors.WHITE}{claim.get('description')}{Colors.RESET}")
        
        print(f"\n{Colors.CYAN}Claim:{Colors.RESET} {claim.get('claim_text', 'N/A')}")
        
        if claim.get('sources'):
            print(f"{Colors.CYAN}Sources:{Colors.RESET} {claim.get('sources')}")
        
        print(f"{Colors.GRAY}{'-' * 60}{Colors.RESET}")
    
    def display_myth(self, myth: dict):
        """Display a formatted myth"""
        print(f"\n{Colors.BOLD}{myth.get('myth_title', 'Untitled Myth')}{Colors.RESET}")
        print(f"{Colors.RED}✗ DEBUNKED{Colors.RESET}")
        print(f"{Colors.GRAY}By {myth.get('author', 'Anonymous')} • {myth.get('created_at', 'N/A')}{Colors.RESET}")
        
        if myth.get('myth_description'):
            print(f"{Colors.WHITE}{myth.get('myth_description')}{Colors.RESET}")
        
        print(f"\n{Colors.RED}The Myth:{Colors.RESET} {myth.get('myth_title')}")
        print(f"\n{Colors.GREEN}Why It's False:{Colors.RESET} {myth.get('debunked_explanation')}")
        
        if myth.get('scientific_evidence'):
            print(f"\n{Colors.CYAN}Scientific Evidence:{Colors.RESET} {myth.get('scientific_evidence')}")
        
        if myth.get('sources'):
            print(f"\n{Colors.CYAN}Sources:{Colors.RESET} {myth.get('sources')}")
        
        print(f"{Colors.GRAY}{'-' * 60}{Colors.RESET}")
    
    def view_claims(self, filter_status: Optional[str] = None):
        """View all claims"""
        self.print_header("All Claims")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/claims",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                claims = data.get('data', [])
                
                if filter_status:
                    claims = [c for c in claims if c.get('verification_status') == filter_status]
                
                if not claims:
                    self.print_info("No claims found.")
                    return
                
                print(f"{Colors.BOLD}Total Claims: {len(claims)}{Colors.RESET}\n")
                
                for claim in claims[:10]:  # Show first 10
                    self.display_claim(claim)
                
                if len(claims) > 10:
                    print(f"\n{Colors.GRAY}... and {len(claims) - 10} more claims. Use API for full list.{Colors.RESET}")
            else:
                self.print_error("Failed to retrieve claims")
        except Exception as e:
            self.print_error(f"Connection error: {str(e)}")
    
    def view_myths(self):
        """View all myths"""
        self.print_header("Debunked Myths")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/myths",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                myths = data.get('data', [])
                
                if not myths:
                    self.print_info("No myths found.")
                    return
                
                print(f"{Colors.BOLD}Total Myths: {len(myths)}{Colors.RESET}\n")
                
                for myth in myths[:10]:  # Show first 10
                    self.display_myth(myth)
                
                if len(myths) > 10:
                    print(f"\n{Colors.GRAY}... and {len(myths) - 10} more myths. Use API for full list.{Colors.RESET}")
            else:
                self.print_error("Failed to retrieve myths")
        except Exception as e:
            self.print_error(f"Connection error: {str(e)}")
    
    def view_claim(self, claim_id: int):
        """View a specific claim"""
        try:
            response = requests.get(
                f"{self.base_url}/api/claims/{claim_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.print_header(f"Claim #{claim_id}")
                claim = response.json().get('data', {})
                self.display_claim(claim)
            else:
                self.print_error("Claim not found")
        except Exception as e:
            self.print_error(f"Connection error: {str(e)}")
    
    def view_myth(self, myth_id: int):
        """View a specific myth"""
        try:
            response = requests.get(
                f"{self.base_url}/api/myths/{myth_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.print_header(f"Myth #{myth_id}")
                myth = response.json().get('data', {})
                self.display_myth(myth)
            else:
                self.print_error("Myth not found")
        except Exception as e:
            self.print_error(f"Connection error: {str(e)}")
    
    def show_stats(self):
        """Show API statistics"""
        self.print_header("Statistics")
        
        try:
            claims_res = requests.get(f"{self.base_url}/api/claims", timeout=10)
            myths_res = requests.get(f"{self.base_url}/api/myths", timeout=10)
            
            claims_data = claims_res.json()
            myths_data = myths_res.json()
            
            claims = claims_data.get('data', [])
            myths = myths_data.get('data', [])
            
            verified = len([c for c in claims if c.get('verification_status') == 'verified'])
            false = len([c for c in claims if c.get('verification_status') == 'false'])
            pending = len([c for c in claims if c.get('verification_status') == 'pending'])
            
            print(f"{Colors.BOLD}Claims:{Colors.RESET}")
            print(f"  {Colors.GREEN}✓ Verified: {verified}{Colors.RESET}")
            print(f"  {Colors.RED}✗ False: {false}{Colors.RESET}")
            print(f"  {Colors.YELLOW}⏳ Pending: {pending}{Colors.RESET}")
            print(f"  {Colors.BOLD}Total: {len(claims)}{Colors.RESET}")
            
            print(f"\n{Colors.BOLD}Myths:{Colors.RESET}")
            print(f"  {Colors.RED}✗ Debunked: {len(myths)}{Colors.RESET}")
            
            print(f"\n{Colors.BOLD}Overall:{Colors.RESET}")
            print(f"  Total Discoveries: {len(claims) + len(myths)}")
            
        except Exception as e:
            self.print_error(f"Failed to fetch statistics: {str(e)}")
    
    def show_help(self):
        """Show help menu"""
        self.print_header("Help & Commands")
        
        commands = [
            ("1", "Submit a Claim", "Add a new scientific claim to verify"),
            ("2", "Submit a Myth", "Add a new myth to debunk"),
            ("3", "View Claims", "Browse all submitted claims"),
            ("4", "View Myths", "Browse all debunked myths"),
            ("5", "View Claim", "View a specific claim by ID"),
            ("6", "View Myth", "View a specific myth by ID"),
            ("7", "Statistics", "View API statistics"),
            ("8", "Help", "Show this help menu"),
            ("0", "Exit", "Close the CLI"),
        ]
        
        for cmd, title, desc in commands:
            print(f"{Colors.BOLD}{cmd}{Colors.RESET}. {title}")
            print(f"   {Colors.GRAY}{desc}{Colors.RESET}\n")
    
    def run(self):
        """Main CLI loop"""
        # Clear screen and show header
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}")
        print("""
        ╔═══════════════════════════════════════╗
        ║  🌌 COSMOS SCIENCE FACT-CHECKING 🌌   ║
        ║          CLI Version 1.0.0             ║
        ╚═══════════════════════════════════════╝
        """)
        print(Colors.RESET)
        
        # Check connection
        print("Checking connection to API...")
        if not self.check_connection():
            self.print_error("Cannot connect to API at " + self.base_url)
            self.print_info("Make sure the Flask app is running: python App.py")
            sys.exit(1)
        
        self.print_success("Connected to Cosmos API!")
        
        # Main loop
        while True:
            print(f"\n{Colors.CYAN}{Colors.BOLD}What would you like to do?{Colors.RESET}")
            print(f"  {Colors.BOLD}1{Colors.RESET}) Submit Claim")
            print(f"  {Colors.BOLD}2{Colors.RESET}) Submit Myth")
            print(f"  {Colors.BOLD}3{Colors.RESET}) View Claims")
            print(f"  {Colors.BOLD}4{Colors.RESET}) View Myths")
            print(f"  {Colors.BOLD}5{Colors.RESET}) View Claim by ID")
            print(f"  {Colors.BOLD}6{Colors.RESET}) View Myth by ID")
            print(f"  {Colors.BOLD}7{Colors.RESET}) Statistics")
            print(f"  {Colors.BOLD}8{Colors.RESET}) Help")
            print(f"  {Colors.BOLD}0{Colors.RESET}) Exit")
            
            choice = input(f"\n{Colors.CYAN}➜ Your choice: {Colors.RESET}").strip()
            
            if choice == "1":
                self.submit_claim()
            elif choice == "2":
                self.submit_myth()
            elif choice == "3":
                self.view_claims()
            elif choice == "4":
                self.view_myths()
            elif choice == "5":
                try:
                    claim_id = int(input(f"{Colors.CYAN}➜ Enter Claim ID: {Colors.RESET}"))
                    self.view_claim(claim_id)
                except ValueError:
                    self.print_error("Invalid ID. Please enter a number.")
            elif choice == "6":
                try:
                    myth_id = int(input(f"{Colors.CYAN}➜ Enter Myth ID: {Colors.RESET}"))
                    self.view_myth(myth_id)
                except ValueError:
                    self.print_error("Invalid ID. Please enter a number.")
            elif choice == "7":
                self.show_stats()
            elif choice == "8":
                self.show_help()
            elif choice == "0":
                self.print_info("Thanks for using Cosmos CLI! Goodbye! 👋")
                sys.exit(0)
            else:
                self.print_error("Invalid choice. Please try again.")

def main():
    """Entry point"""
    # Allow custom API URL via environment variable
    api_url = os.getenv('COSMOS_API_URL', 'http://localhost:5000')
    
    cli = CosmosAPI(base_url=api_url)
    cli.run()

if __name__ == "__main__":
    main()
