"""
main.py - Railway Station Announcer (English Version)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import List, Dict
import time

from .train_data import generate_train_departures, format_delay_text
from .llm_generator import AnnouncementGenerator
from .tts_engine import SileroTTS


class RailwayAnnouncerApp:
    """Railway Station Announcer Application."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚂 Railway Station Announcer (AI Powered)")
        self.root.geometry("800x700")
        self.root.configure(bg="#1a1a2e")
        
        # App State
        self.trains: List[Dict] = []
        self.llm_generator: AnnouncementGenerator = None
        self.tts_engine: SileroTTS = None
        self.is_speaking = False
        self.should_stop = False
        
        self._setup_styles()
        self._create_widgets()
        self._init_models_async()
        
        # Handle close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _setup_styles(self):
        """Configure app styles."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        bg_dark = "#1a1a2e"
        bg_medium = "#16213e"
        bg_light = "#0f3460"
        accent = "#e94560"
        text_light = "#eaeaea"
        text_dim = "#a0a0a0"
        
        # Buttons
        style.configure(
            "Accent.TButton",
            background=accent,
            foreground=text_light,
            padding=(20, 10),
            font=("Segoe UI", 11, "bold")
        )
        style.map("Accent.TButton",
            background=[("active", "#ff6b6b"), ("disabled", "#555555")]
        )
        
        style.configure(
            "Secondary.TButton",
            background=bg_light,
            foreground=text_light,
            padding=(20, 10),
            font=("Segoe UI", 11)
        )
        style.map("Secondary.TButton",
            background=[("active", "#1a5276"), ("disabled", "#555555")]
        )
        
        # Treeview
        style.configure(
            "Custom.Treeview",
            background=bg_medium,
            foreground=text_light,
            fieldbackground=bg_medium,
            rowheight=30,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=bg_light,
            foreground=text_light,
            font=("Segoe UI", 10, "bold")
        )
        style.map("Custom.Treeview",
            background=[("selected", bg_light)]
        )
        
        # Frames
        style.configure("Dark.TFrame", background=bg_dark)
        style.configure("Card.TFrame", background=bg_medium)
        
    def _create_widgets(self):
        """Create UI widgets."""
        bg_dark = "#1a1a2e"
        bg_medium = "#16213e"
        text_light = "#eaeaea"
        
        # Main Container
        main_frame = ttk.Frame(self.root, style="Dark.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # HEADER
        header_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            header_frame,
            text="🚂 RAILWAY STATION ANNOUNCER",
            font=("Segoe UI", 22, "bold"),
            bg=bg_dark,
            fg=text_light
        )
        title_label.pack(side=tk.LEFT)
        
        # BUTTONS
        button_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.refresh_btn = ttk.Button(
            button_frame,
            text="🔄 Refresh Departures",
            style="Secondary.TButton",
            command=self._on_refresh_click
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.speak_btn = ttk.Button(
            button_frame,
            text="🔊 Read Announcements",
            style="Accent.TButton",
            command=self._on_speak_click
        )
        self.speak_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(
            button_frame,
            text="⏹ STOP",
            style="Secondary.TButton",
            command=self._on_stop_click,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT)
        
        # TRAIN TABLE
        table_label = tk.Label(
            main_frame,
            text="📋 Departures Board",
            font=("Segoe UI", 14, "bold"),
            bg=bg_dark,
            fg=text_light
        )
        table_label.pack(anchor=tk.W, pady=(10, 5))
        
        table_frame = ttk.Frame(main_frame, style="Card.TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        columns = ("train", "route", "time", "delay", "platform")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Custom.Treeview",
            height=8
        )
        
        self.tree.heading("train", text="Train")
        self.tree.heading("route", text="Route")
        self.tree.heading("time", text="Time")
        self.tree.heading("delay", text="Delay")
        self.tree.heading("platform", text="Plat.")
        
        self.tree.column("train", width=100)
        self.tree.column("route", width=280)
        self.tree.column("time", width=80)
        self.tree.column("delay", width=100)
        self.tree.column("platform", width=60)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ANNOUNCEMENT TEXT
        announcement_label = tk.Label(
            main_frame,
            text="💬 Live Announcement",
            font=("Segoe UI", 14, "bold"),
            bg=bg_dark,
            fg=text_light
        )
        announcement_label.pack(anchor=tk.W, pady=(10, 5))
        
        self.announcement_text = tk.Text(
            main_frame,
            height=5,
            bg="#16213e",
            fg=text_light,
            font=("Segoe UI", 11),
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=15,
            pady=10
        )
        self.announcement_text.pack(fill=tk.X, pady=(0, 15))
        self.announcement_text.config(state=tk.DISABLED)
        
        # STATUS BAR
        status_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame,
            text="⏳ Initializing AI models...",
            font=("Segoe UI", 10),
            bg=bg_dark,
            fg="#a0a0a0"
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(side=tk.RIGHT)
        
    def _set_status(self, message: str):
        """Update status bar thread-safely."""
        self.root.after(0, lambda: self.status_label.config(text=message))
        
    def _set_announcement(self, text: str):
        """Update announcement text thread-safely."""
        def update():
            self.announcement_text.config(state=tk.NORMAL)
            self.announcement_text.delete("1.0", tk.END)
            self.announcement_text.insert("1.0", text)
            self.announcement_text.config(state=tk.DISABLED)
        self.root.after(0, update)
    
    def _init_models_async(self):
        """Background initialization."""
        self.progress.start()
        
        def init_thread():
            try:
                self._set_status("⏳ Loading Silero TTS (English)...")
                self.tts_engine = SileroTTS(progress_callback=self._set_status)
                self.tts_engine.load_model()
                
                self._set_status("⏳ Loading LLM (Qwen2.5)...")
                self.llm_generator = AnnouncementGenerator(progress_callback=self._set_status)
                # Don't force load LLM here, let it load on first use or user action if preferred, 
                # but better to load now to show progress.
                if not self.llm_generator.is_model_downloaded():
                     self._set_status("⬇ Downloading Qwen2.5 (~4.7GB)... This will take a while.")
                     
                self.llm_generator.load_model()
                
                self.root.after(0, self._on_models_ready)
                
            except Exception as e:
                self._set_status(f"❌ Init Error: {e}")
                self.root.after(0, lambda: self.progress.stop())
        
        thread = threading.Thread(target=init_thread, daemon=True)
        thread.start()
    
    def _on_models_ready(self):
        self.progress.stop()
        self.progress.pack_forget() # Hide progress bar when done
        self._set_status("✅ System Ready - Click 'Refresh Departures'")
        self._set_announcement("System ready. Waiting for data...")
    
    def _on_refresh_click(self):
        self._set_status("🔄 Generating random train data...")
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.trains = generate_train_departures(8)
        
        delayed_count = 0
        for train in self.trains:
            delay_text = format_delay_text(train["delay_minutes"])
            # Translate delay text to English manually or just keep as is (since train_data.py is Polish-centric)
            # Let's simple-fix display:
            if "minut" in delay_text: 
                delay_text = delay_text.replace("minut", "min").replace("minuta", "min").replace("minuty", "min")
            if "planowo" in delay_text:
                delay_text = "On Time"
                
            platform_text = f"{train['platform']}"
            if train.get("track"): platform_text += f"/{train['track']}"
            
            tag = "delayed" if train["is_delayed"] else "ontime"
            if train["is_delayed"]: delayed_count += 1
            
            self.tree.insert("", tk.END, values=(
                train["train_number"],
                f"{train['origin']} → {train['destination']}",
                train["scheduled_time"],
                delay_text,
                platform_text
            ), tags=(tag,))
        
        self.tree.tag_configure("delayed", foreground="#ff6b6b")
        self.tree.tag_configure("ontime", foreground="#6bff6b")
        
        self._set_status(f"✅ Loaded {len(self.trains)} trains ({delayed_count} delayed)")
    
    def _on_stop_click(self):
        """Immediate stop."""
        self.should_stop = True
        self._set_status("🛑 STOPPING...")
        if self.tts_engine:
            self.tts_engine.stop()
    
    def _check_stop(self) -> bool:
        """Callback to check stop flag."""
        return self.should_stop
        
    def _on_speak_click(self):
        if not self.trains:
            messagebox.showwarning("No Data", "Please refresh departures first!")
            return
            
        if self.is_speaking: return
        
        self.is_speaking = True
        self.should_stop = False
        self.speak_btn.config(state=tk.DISABLED)
        self.refresh_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        def speak_thread():
            try:
                # Announce first 3 trains (as requested)
                trains_to_announce = self.trains[:3]
                
                for i, train in enumerate(trains_to_announce, 1):
                    if self.should_stop: break
                    
                    self._set_status(f"🤖 Generating announcement {i}/{len(trains_to_announce)}...")
                    
                    # Generate with stop checking
                    text = self.llm_generator.generate_announcement(
                        train, 
                        stop_check_callback=self._check_stop
                    )
                    
                    if self.should_stop: break
                    
                    self._set_announcement(text)
                    
                    # TTS
                    self._set_status(f"🔊 Speaking {i}/{len(trains_to_announce)}...")
                    self.tts_engine.speak(text, blocking=True)
                    
                    if self.should_stop: break
                    
                    time.sleep(1.0)
                
                if self.should_stop:
                    self._set_status("🛑 Stopped by user")
                else:
                    self._set_status("✅ All announcements completed")
                    
            except Exception as e:
                self._set_status(f"❌ Error: {e}")
            finally:
                self.is_speaking = False
                self.root.after(0, self._on_speaking_done)
                
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
        
    def _on_speaking_done(self):
        self.speak_btn.config(state=tk.NORMAL)
        self.refresh_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
    def _on_close(self):
        self.should_stop = True
        if self.tts_engine: self.tts_engine.stop()
        self.root.destroy()
        
    def run(self):
        self.root.mainloop()


def main():
    app = RailwayAnnouncerApp()
    app.run()

if __name__ == "__main__":
    main()
