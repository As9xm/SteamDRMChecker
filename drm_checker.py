import tkinter as tk
from tkinter import ttk, messagebox, font
import requests
import urllib.parse
import re
import time

class SteamDRMChecker:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam DRM Checker")
        self.root.geometry("800x500")
        self.root.resizable(True, True)
        self.root.configure(bg="#f5f5f5")
        
        # Custom fonts
        self.title_font = font.Font(family="Segoe UI", size=16, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=10)
        self.result_font = font.Font(family="Consolas", size=9)
        
        # Header
        header_frame = tk.Frame(root, bg="#2c3e50", pady=10)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(header_frame, text="Steam DRM Checker", 
                              font=self.title_font, fg="white", bg="#2c3e50")
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, text="Check if a game uses Steam DRM, Denuvo, or No protection",
                                 font=("Segoe UI", 9), fg="#ecf0f1", bg="#2c3e50")
        subtitle_label.pack()
        
        # Search frame
        search_frame = tk.Frame(root, bg="#f5f5f5", pady=15)
        search_frame.pack(fill=tk.X, padx=20)
        
        tk.Label(search_frame, text="Game Name:", font=self.label_font, bg="#f5f5f5").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=50, font=self.label_font)
        self.search_entry.pack(side=tk.LEFT, padx=10)
        self.search_entry.bind("<Return>", self.search_game)
        
        self.search_btn = tk.Button(search_frame, text="🔍 Search", command=self.search_game, 
                                   bg="#3498db", fg="white", font=self.label_font, padx=10)
        self.search_btn.pack(side=tk.LEFT)
        
        # Result area
        result_frame = tk.Frame(root, bg="#ffffff", padx=20, pady=15)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(result_frame, text="📊 DRM Protection Details:", 
                font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(anchor="w")
        
        # Scrollable result box
        self.result_canvas = tk.Canvas(result_frame, bg="#ffffff", highlightthickness=0)
        self.result_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.result_scrollbar = tk.Scrollbar(self.result_canvas, orient=tk.VERTICAL, command=self.result_canvas.yview)
        self.result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_inner_frame = tk.Frame(self.result_canvas, bg="#ffffff")
        self.result_canvas.create_window((0, 0), window=self.result_inner_frame, anchor="nw")
        self.result_canvas.configure(yscrollcommand=self.result_scrollbar.set)
        
        # Bind resize to update canvas scroll region
        self.result_inner_frame.bind("<Configure>", lambda e: self.result_canvas.configure(scrollregion=self.result_canvas.bbox("all")))
        
        # Info footer
        info_frame = tk.Frame(root, bg="#f5f5f5", pady=5)
        info_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        info_label = tk.Label(info_frame, text="Data from PCGamingWiki.com • May not be 100% real-time", 
                             font=("Segoe UI", 8), fg="gray", bg="#f5f5f5")
        info_label.pack()
        
    def search_game(self, event=None):
        game_name = self.search_var.get().strip()
        if not game_name:
            messagebox.showwarning("Input Error", "Please enter a game name!")
            return
            
        # Clear previous results
        for widget in self.result_inner_frame.winfo_children():
            widget.destroy()
            
        # Show loading
        loading_label = tk.Label(self.result_inner_frame, text="⏳ Searching... (this may take a few seconds)",
                                font=self.result_font, bg="#ffffff", fg="gray")
        loading_label.pack(pady=10)
        self.root.update()
        
        try:
            drm_info = self.get_drm_info(game_name)
            self.display_results(drm_info, game_name)
        except Exception as e:
            self.clear_results()
            error_label = tk.Label(self.result_inner_frame, text=f"⚠️ Error: {str(e)}\n\nCheck internet connection or try again later.",
                                  font=self.result_font, bg="#ffffff", fg="red", justify=tk.LEFT)
            error_label.pack(pady=10, padx=10, anchor="w")
    
    def display_results(self, drm_info, original_name):
        self.clear_results()
        
        if isinstance(drm_info, dict) and "suggestions" in drm_info:
            
            title_label = tk.Label(self.result_inner_frame, text="🔍 Did you mean?", 
                                  font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#2c3e50")
            title_label.pack(anchor="w", pady=(10, 5))
            
            for suggestion in drm_info['suggestions']:
                suggestion_label = tk.Label(self.result_inner_frame, text=f"  • {suggestion}",
                                           font=self.result_font, bg="#ffffff", fg="#3498db", cursor="hand2")
                suggestion_label.pack(anchor="w", padx=10, pady=2)
                suggestion_label.bind("<Button-1>", lambda e, s=suggestion: self.fill_search_box(s))
            
            note_label = tk.Label(self.result_inner_frame, text="\n💡 Click any suggestion to search for it!",
                                 font=("Segoe UI", 9), bg="#ffffff", fg="gray")
            note_label.pack(anchor="w", padx=10, pady=5)
            
        elif drm_info:
            # Show detailed results
            game_title = tk.Label(self.result_inner_frame, text=f"🎮 {drm_info['game']}",
                                 font=("Segoe UI", 14, "bold"), bg="#ffffff", fg="#2c3e50")
            game_title.pack(anchor="w", pady=(10, 5))
            
            # Protection status with color coding
            protection = drm_info['protection']
            color = "#27ae60" if protection == "No protection" else "#e74c3c" if protection == "Denuvo" else "#3498db"
            
            protection_label = tk.Label(self.result_inner_frame, text=f"🛡️ Protection: {protection}",
                                       font=("Segoe UI", 11, "bold"), bg="#ffffff", fg=color)
            protection_label.pack(anchor="w", pady=5)
            
            # Show availability table if available
            if 'availability' in drm_info and drm_info['availability']:
                tk.Label(self.result_inner_frame, text="\n📦 Availability:", 
                        font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#2c3e50").pack(anchor="w", pady=(10, 5))
                
                for entry in drm_info['availability']:
                    source = entry.get('source', 'Unknown')
                    drm_status = entry.get('drm', 'N/A')
                    notes = entry.get('notes', '')
                    os_list = entry.get('os', [])
                    
                    entry_frame = tk.Frame(self.result_inner_frame, bg="#ffffff")
                    entry_frame.pack(anchor="w", fill=tk.X, padx=10, pady=3)
                    
                    
                    source_label = tk.Label(entry_frame, text=f"• {source}", 
                                           font=self.result_font, bg="#ffffff", fg="#2c3e50", width=20)
                    source_label.pack(side=tk.LEFT)
                    
                    # DRM status
                    drm_label = tk.Label(entry_frame, text=drm_status, 
                                        font=self.result_font, bg="#ffffff", fg=color, width=15)
                    drm_label.pack(side=tk.LEFT, padx=5)
                    
                    
                    os_text = ""
                    if "Windows" in os_list:
                        os_text += "indows "
                    if "Mac" in os_list:
                        os_text += "ac "
                    if "Linux" in os_list:
                        os_text += "inux "
                    
                    if os_text:
                        os_label = tk.Label(entry_frame, text=os_text.strip(), 
                                           font=self.result_font, bg="#ffffff", fg="gray")
                        os_label.pack(side=tk.LEFT, padx=5)
                    
                    # Notes
                    if notes:
                        notes_label = tk.Label(entry_frame, text=f"→ {notes}", 
                                              font=self.result_font, bg="#ffffff", fg="gray", wraplength=400)
                        notes_label.pack(side=tk.LEFT, padx=10)
            
            # Add more info if available
            if 'additional_info' in drm_info:
                tk.Label(self.result_inner_frame, text="\nℹ️ Additional Info:", 
                        font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#2c3e50").pack(anchor="w", pady=(10, 5))
                
                info_label = tk.Label(self.result_inner_frame, text=drm_info['additional_info'],
                                     font=self.result_font, bg="#ffffff", fg="gray", wraplength=600, justify=tk.LEFT)
                info_label.pack(anchor="w", padx=10, pady=5)
            
            # Show similar games (excluding exact match)
            similar_games = self.get_similar_games(original_name)
            if similar_games:
                tk.Label(self.result_inner_frame, text="\n🔍 Similar Games:", 
                        font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#2c3e50").pack(anchor="w", pady=(15, 5))
                
                for suggestion in similar_games[:5]:  # Show top 5
                    suggestion_label = tk.Label(self.result_inner_frame, text=f"  • {suggestion}",
                                               font=self.result_font, bg="#ffffff", fg="#3498db", cursor="hand2")
                    suggestion_label.pack(anchor="w", padx=10, pady=2)
                    suggestion_label.bind("<Button-1>", lambda e, s=suggestion: self.fill_search_box(s))
                
                note_label = tk.Label(self.result_inner_frame, text="💡 Click any suggestion to search for it!",
                                     font=("Segoe UI", 9), bg="#ffffff", fg="gray")
                note_label.pack(anchor="w", padx=10, pady=5)
                
        else:
            # Game not found
            not_found_label = tk.Label(self.result_inner_frame, text=f"❌ Game '{original_name}' not found.",
                                      font=("Segoe UI", 12, "bold"), bg="#ffffff", fg="#e74c3c")
            not_found_label.pack(anchor="w", pady=10)
            
            note_label = tk.Label(self.result_inner_frame, text="Try:\n• Using exact title\n• Checking spelling\n• Using first letter uppercase\n• Searching PCGamingWiki directly",
                                 font=self.result_font, bg="#ffffff", fg="gray", justify=tk.LEFT)
            note_label.pack(anchor="w", padx=10, pady=5)
    
    def clear_results(self):
        for widget in self.result_inner_frame.winfo_children():
            widget.destroy()
    
    def fill_search_box(self, suggestion):
        self.search_var.set(suggestion)
        self.search_game()
    
    def get_drm_info(self, game_name):
        # Step 1: Try original input
        result = self.try_get_drm_info(game_name)
        if result:
            return result
        
        
        title_case = game_name.title()
        if title_case != game_name:
            result = self.try_get_drm_info(title_case)
            if result:
                return result
        
       
        suggestions = self.search_suggestions(game_name)
        if suggestions:
            return {"suggestions": suggestions}
        
        return None
    
    def try_get_drm_info(self, game_name):
        """Try to get DRM info for a specific game name"""
        wiki_page = game_name.replace(" ", "_")
        encoded_page = urllib.parse.quote(wiki_page)
        
        url = f"https://www.pcgamingwiki.com/w/api.php?action=parse&format=json&page={encoded_page}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return None
                
            data = response.json()
            if "error" in data:
                return None
                
            html_content = data["parse"]["text"]["*"]
            
            
            page_title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
            actual_game_name = page_title_match.group(1).strip() if page_title_match else game_name
            
            # Extract DRM info
            drm_result = self.extract_drm_from_html(html_content)
            if not drm_result:
                # Fallback: Check for Steam logo in availability table
                availability = self.extract_availability_table(html_content)
                if availability:
                    for entry in availability:
                        if entry.get('source', '').lower() == 'steam':
                            # Check if there's a Steam logo in DRM column
                            if 'steam' in entry.get('drm', '').lower() or 'logo' in entry.get('drm', '').lower():
                                drm_result = "Steamworks DRM"
                            else:
                                # If no specific DRM info but it's on Steam, assume Steamworks DRM
                                drm_result = "Steamworks DRM"
                else:
                    drm_result = "Not specified"
            
            
            availability = self.extract_availability_table(html_content)
            
            additional_info = self.extract_additional_info(html_content)
            
            return {
                'game': actual_game_name,
                'protection': drm_result,
                'availability': availability,
                'additional_info': additional_info
            }
                
        except Exception as e:
            print(f"Error fetching {game_name}: {e}")
            return None
    
    def extract_drm_from_html(self, html_content):
        
        drm_match = re.search(r'<tr[^>]*>\s*<th[^>]*>DRM\s*</th>\s*<td[^>]*>([^<]+)</td>', html_content, re.IGNORECASE)
        if drm_match:
            drm_text = drm_match.group(1).strip()
            if "steam" in drm_text.lower():
                return "Steamworks DRM"
            elif "denuvo" in drm_text.lower():
                return "Denuvo"
            elif "none" in drm_text.lower() or "no drm" in drm_text.lower() or "drm-free" in drm_text.lower():
                return "No protection"
            else:
                return drm_text  # Return raw if unknown
        
        
        notes_matches = re.findall(r'<td[^>]*>([^<]*drm[^<]*)</td>', html_content, re.IGNORECASE)
        for note in notes_matches:
            if "drm-free" in note.lower() or "no drm" in note.lower() or "can be run drm-free" in note.lower():
                return "No protection"
            elif "steam drm" in note.lower():
                return "Steamworks DRM"
            elif "denuvo" in note.lower():
                return "Denuvo"
        
        #Look for Steam logo in availability table
        availability = self.extract_availability_table(html_content)
        if availability:
            for entry in availability:
                if entry.get('source', '').lower() == 'steam':
                    # Check if there's a Steam logo in DRM column
                    drm_cell = entry.get('drm', '')
                    # Look for Steam logo image
                    if 'src=' in drm_cell and ('steam' in drm_cell.lower() or 'logo' in drm_cell.lower()):
                        return "Steamworks DRM"
                    # Look for Steam text in DRM column
                    if 'steam' in drm_cell.lower() or 'logo' in drm_cell.lower():
                        return "Steamworks DRM"
                    # If no specific DRM info but it's on Steam, assume Steamworks DRM
                    return "Steamworks DRM"
        
        #Fallback - look for any DRM-related text in whole page
        if "drm-free" in html_content.lower():
            return "No protection"
        elif "steam drm" in html_content.lower():
            return "Steamworks DRM"
        elif "denuvo" in html_content.lower():
            return "Denuvo"
        elif "no drm" in html_content.lower():
            return "No protection"
        
        # Handle stub pages (incomplete data)
        if "This page is a stub" in html_content:
            # Try to extract any available DRM info from availability table
            availability = self.extract_availability_table(html_content)
            if availability:
                for entry in availability:
                    if entry.get('source', '').lower() == 'steam':
                        return "Steamworks DRM"
        
        return "Not specified"
    
    def extract_availability_table(self, html_content):
        """Extract availability table data"""
        availability = []
        
        # Look for the availability table (usually under "Availability" heading)
        table_match = re.search(r'<table[^>]*class="wikitable"[^>]*>(.*?)</table>', html_content, re.DOTALL | re.IGNORECASE)
        if not table_match:
            return availability
        
        table_html = table_match.group(1)
        
        # Find all rows
        row_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        
        for row in row_matches[1:]:  # Skip header row
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) >= 3:  # Should have at least Source, DRM, Notes
                source = self.clean_html(cells[0])
                drm = self.clean_html(cells[1])
                notes = self.clean_html(cells[2])
                
                # Extract OS info from last column
                os_info = []
                if len(cells) > 5:
                    os_cell = cells[5]
                    if "Windows" in os_cell:
                        os_info.append("Windows")
                    if "Mac" in os_cell:
                        os_info.append("Mac")
                    if "Linux" in os_cell:
                        os_info.append("Linux")
                
                availability.append({
                    'source': source,
                    'drm': drm,
                    'notes': notes,
                    'os': os_info
                })
        
        return availability
    
    def extract_additional_info(self, html_content):
        """Extract general info about the game"""
        # Look for summary paragraph
        summary_match = re.search(r'<p>([^<]*?)(?:<br|</p>)', html_content, re.IGNORECASE)
        if summary_match:
            return summary_match.group(1).strip()
        
        return None
    
    def clean_html(self, html_text):
        """Remove HTML tags and clean text"""
        # Remove HTML tags
        cleaned = re.sub(r'<[^>]*>', '', html_text)
        # Clean whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def search_suggestions(self, game_name):
        """Search PCGamingWiki for similar game names"""
        # Use their search API
        search_url = f"https://www.pcgamingwiki.com/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(game_name)}&format=json&srlimit=10"
        
        try:
            response = requests.get(search_url, timeout=10)
            if response.status_code != 200:
                return []
                
            data = response.json()
            if "query" not in data or "search" not in data["query"]:
                return []
                
            suggestions = []
            for item in data["query"]["search"]:
                title = item["title"]
                # Clean up title 
                if "(" in title and ")" in title:
                    title = title.split("(")[0].strip()
                suggestions.append(title)
                
            return suggestions
        except Exception as e:
            print(f"Search suggestions failed: {e}")
            return []
    
    def get_similar_games(self, game_name):
        """Get similar games (excluding exact match)"""
        # Get suggestions
        suggestions = self.search_suggestions(game_name)
        
        if not suggestions:
            return []
        
        # Filter out exact matches 
        exact_match = game_name.strip().lower()
        similar_games = []
        
        for suggestion in suggestions:
            # Skip if it's an exact match 
            if suggestion.lower() == exact_match:
                continue
            # Skip if it's very similar (e.g., "Game" vs "Game 2")
            if len(suggestion) > 0 and len(exact_match) > 0:
                # Simple similarity check: if suggestion contains the game name or vice versa
                if (exact_match in suggestion.lower() or suggestion.lower() in exact_match) and abs(len(suggestion) - len(exact_match)) <= 3:
                    continue
            similar_games.append(suggestion)
        
        # If we have too many similar games, limit to 5
        return similar_games[:5] if similar_games else []

if __name__ == "__main__":
    root = tk.Tk()
    app = SteamDRMChecker(root)
    root.mainloop()