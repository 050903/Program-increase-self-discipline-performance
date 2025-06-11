import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- CONSTANTS ---
CONFIG_FILE = 'config.json'
# <<< NÂNG CẤP 1: Chuyển sang file log để lưu lịch sử >>>
ACTIVITY_LOG_FILE = 'activity_log.json' 
INITIAL_SCORE = 30.0
APP_TITLE = "Trợ Lý Hiệu Suất Cá Nhân v2.0"
WINDOW_GEOMETRY = "1200x700"

# Set font for Matplotlib to support Vietnamese
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'Tahoma']
plt.rcParams['axes.unicode_minus'] = False


class PerformanceAI:
    """
    Handles advanced business logic, including historical analysis and feedback.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.categories = list(config.keys())

    def calculate_improvement(self, category_key: str, activity_key: str, quantity: float) -> float:
        try:
            activity = self.config[category_key]['activities'][activity_key]
            return quantity * activity['impact_per_unit']
        except KeyError:
            return 0.0

    def calculate_scores_from_log(self, log: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculates current scores by processing the entire activity log."""
        scores = {cat: INITIAL_SCORE for cat in self.categories}
        for entry in log:
            cat = entry.get('category')
            points = entry.get('points', 0)
            if cat in scores:
                scores[cat] = min(100.0, scores[cat] + points)
        return scores

    def get_historical_scores(self, log: List[Dict[str, Any]]) -> Dict[str, List[Tuple[datetime, float]]]:
        """Processes the log to generate time-series data for the trend chart."""
        history = {cat: [(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30), INITIAL_SCORE)] for cat in self.categories}
        
        # Sort log by date to ensure correct chronological processing
        sorted_log = sorted(log, key=lambda x: x['timestamp'])
        
        temp_scores = {cat: INITIAL_SCORE for cat in self.categories}

        for entry in sorted_log:
            cat = entry.get('category')
            points = entry.get('points', 0)
            timestamp = datetime.fromisoformat(entry['timestamp'])
            
            if cat in temp_scores:
                temp_scores[cat] = min(100.0, temp_scores[cat] + points)
                history[cat].append((timestamp, temp_scores[cat]))
        
        return history

    # <<< NÂNG CẤP 2: Phương thức AI đưa ra nhận xét >>>
    def get_ai_feedback(self, scores: Dict[str, float], log: List[Dict[str, Any]]) -> str:
        """Generates intelligent feedback based on current scores and activity history."""
        feedback = []
        
        # 1. Find best and worst performing categories
        if scores:
            best_cat = max(scores, key=scores.get)
            worst_cat = min(scores, key=scores.get)
            feedback.append(f"🚀 Phong độ cao nhất: '{self.config[best_cat]['name']}' ({scores[best_cat]:.1f}/100).")
            if scores[worst_cat] < 50:
                feedback.append(f"🤔 Cần chú ý: '{self.config[worst_cat]['name']}' ({scores[worst_cat]:.1f}/100). Hãy thử một hoạt động nhỏ nhé!")

        # 2. Check for inactivity
        last_activity_dates = {cat: None for cat in self.categories}
        for entry in reversed(log):
            cat = entry['category']
            if cat in last_activity_dates and last_activity_dates[cat] is None:
                 last_activity_dates[cat] = datetime.fromisoformat(entry['timestamp'])
        
        for cat, last_date in last_activity_dates.items():
            if last_date:
                days_since = (datetime.now() - last_date).days
                if days_since >= 7:
                    feedback.append(f"⚠️ Cảnh báo: Đã {days_since} ngày bạn chưa có hoạt động cho '{self.config[cat]['name']}'.")
        
        if not feedback:
            return "Mọi thứ đang tiến triển tốt. Hãy tiếp tục duy trì!"
            
        return "\n\n".join(feedback)

    # <<< NÂNG CẤP 3: Phương thức tính chuỗi ngày hoạt động >>>
    def calculate_streak(self, log: List[Dict[str, Any]]) -> int:
        """Calculates the current continuous activity streak."""
        if not log:
            return 0
        
        # Get unique days the user was active, ignoring time
        active_dates = sorted(list(set(datetime.fromisoformat(entry['timestamp']).date() for entry in log)), reverse=True)
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # If last activity was not today or yesterday, streak is broken
        if not active_dates or (active_dates[0] != today and active_dates[0] != yesterday):
            return 0
            
        streak = 0
        # Start checking from today (or yesterday if no activity today)
        current_day = active_dates[0]
        
        for i, day in enumerate(active_dates):
            if current_day - timedelta(days=i) == day:
                streak += 1
            else:
                break # Streak is broken
        return streak


class DataManager:
    """Handles loading and saving of the activity log."""
    def __init__(self, log_path: str):
        self.log_path = log_path

    def get_full_log(self) -> List[Dict[str, Any]]:
        """Loads the entire activity log from the file."""
        if not os.path.exists(self.log_path):
            return []
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, TypeError):
            messagebox.showwarning("Cảnh báo", "File log bị lỗi. Sẽ tạo lại file mới.")
            return []

    def log_activity(self, category: str, activity: str, quantity: float, points: float):
        """Adds a new entry to the activity log."""
        log = self.get_full_log()
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "activity": activity,
            "quantity": quantity,
            "points": points
        }
        log.append(new_entry)
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2, ensure_ascii=False)

    def reset_log(self):
        """Deletes the log file."""
        if os.path.exists(self.log_path):
            os.remove(self.log_path)


class Application(tk.Tk):
    """The main GUI application class."""
    def __init__(self, ai: PerformanceAI, data_manager: DataManager):
        super().__init__()
        self.ai = ai
        self.data_manager = data_manager
        
        self._setup_window()
        self._load_data_and_init_ai()
        self._setup_ui()
        self.update_all_components()

    def _setup_window(self):
        self.title(APP_TITLE)
        self.geometry(WINDOW_GEOMETRY)

    def _load_data_and_init_ai(self):
        """Loads data and calculates initial state."""
        self.activity_log = self.data_manager.get_full_log()
        self.scores = self.ai.calculate_scores_from_log(self.activity_log)

    def _setup_ui(self):
        """Creates and arranges all UI widgets."""
        # Main PanedWindow to split left (pie) and right (tabs)
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Left Frame (Pie Chart and Controls) ---
        left_frame = ttk.Frame(paned_window, width=500)
        paned_window.add(left_frame, weight=2)

        self.streak_label = ttk.Label(left_frame, text="🔥 Chuỗi: 0 ngày", font=("Arial", 16, "bold"), foreground="orange")
        self.streak_label.pack(pady=5)

        self.fig_pie = plt.Figure(figsize=(5, 5), dpi=100)
        self.ax_pie = self.fig_pie.add_subplot(111)
        self.canvas_pie = FigureCanvasTkAgg(self.fig_pie, master=left_frame)
        self.canvas_pie.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.fig_pie.canvas.mpl_connect('button_press_event', self._on_pie_click)
        
        reset_button = ttk.Button(left_frame, text="Reset Toàn Bộ Dữ Liệu", command=self._handle_reset)
        reset_button.pack(pady=10)

        # --- Right Frame (Tabs for Trends and AI Feedback) ---
        right_frame = ttk.Frame(paned_window, width=400)
        paned_window.add(right_frame, weight=3)
        
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Trend Chart Tab
        trend_tab = ttk.Frame(notebook)
        notebook.add(trend_tab, text="📈 Phân Tích Xu Hướng")
        self.fig_trend = plt.Figure(figsize=(6, 5), dpi=100)
        self.ax_trend = self.fig_trend.add_subplot(111)
        self.canvas_trend = FigureCanvasTkAgg(self.fig_trend, master=trend_tab)
        self.canvas_trend.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # AI Feedback Tab
        feedback_tab = ttk.Frame(notebook)
        notebook.add(feedback_tab, text="🤖 Trợ Lý A.I.")
        feedback_header = ttk.Label(feedback_tab, text="Nhận Xét & Gợi Ý", font=("Arial", 14, "bold"))
        feedback_header.pack(pady=10)
        self.feedback_text = tk.Text(feedback_tab, wrap=tk.WORD, height=10, width=50, font=("Arial", 11), relief="flat", bg=self.cget('bg'))
        self.feedback_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def update_all_components(self):
        """A single method to refresh all parts of the UI."""
        self.activity_log = self.data_manager.get_full_log()
        self.scores = self.ai.calculate_scores_from_log(self.activity_log)
        
        self._update_pie_chart()
        self._update_trend_chart()
        self._update_ai_feedback()
        self._update_streak_counter()

    def _update_pie_chart(self):
        self.ax_pie.clear()
        labels = [self.ai.config[key]['name'] for key in self.ai.categories]
        values = [self.scores[key] for key in self.ai.categories]
        
        # Calculate overall score based on current scores
        overall_score = sum(s * self.ai.config[c].get('weight', 0) for c, s in self.scores.items())

        wedges, _, _ = self.ax_pie.pie(
            values, autopct='%1.1f%%', startangle=140, pctdistance=0.85,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1}
        )
        self.wedges = wedges
        
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        self.ax_pie.add_artist(centre_circle)
        self.ax_pie.text(0, 0, f"{overall_score:.1f}\nTổng thể", ha='center', va='center', fontsize=20, color='#33a02c', weight='bold')
        self.ax_pie.axis('equal')
        self.ax_pie.set_title("Hiệu Suất Hiện Tại", fontsize=14)
        self.fig_pie.tight_layout()
        self.canvas_pie.draw()

    def _update_trend_chart(self):
        self.ax_trend.clear()
        historical_data = self.ai.get_historical_scores(self.activity_log)
        for category, data_points in historical_data.items():
            if len(data_points) > 1:
                dates, scores = zip(*data_points)
                self.ax_trend.plot(dates, scores, marker='o', linestyle='-', markersize=4, label=self.ai.config[category]['name'])
        
        self.ax_trend.set_title("Lịch Sử Tiến Bộ", fontsize=14)
        self.ax_trend.set_ylabel("Điểm số")
        self.ax_trend.legend(fontsize='small')
        self.ax_trend.tick_params(axis='x', rotation=30)
        self.fig_trend.tight_layout()
        self.canvas_trend.draw()

    def _update_ai_feedback(self):
        feedback = self.ai.get_ai_feedback(self.scores, self.activity_log)
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete('1.0', tk.END)
        self.feedback_text.insert(tk.END, feedback)
        self.feedback_text.config(state=tk.DISABLED)

    def _update_streak_counter(self):
        streak = self.ai.calculate_streak(self.activity_log)
        self.streak_label.config(text=f"🔥 Chuỗi: {streak} ngày")

    def _on_pie_click(self, event):
        # (This function remains largely the same as before)
        if event.inaxes != self.ax_pie: return
        for i, wedge in enumerate(self.wedges):
            if wedge.contains(event)[0]:
                category_key = self.ai.categories[i]
                self._open_log_activity_window(category_key)
                break

    def _open_log_activity_window(self, category_key: str):
        # (This function remains largely the same as before)
        log_window = tk.Toplevel(self)
        log_window.title(f"Ghi nhận: {self.ai.config[category_key]['name']}")
        log_window.geometry("350x200")
        log_window.transient(self)
        log_window.grab_set()

        frame = ttk.Frame(log_window, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Chọn hoạt động:").pack(anchor='w')
        activities = self.ai.config[category_key]['activities']
        activity_names = [act['name'] for act in activities.values()]
        activity_keys = list(activities.keys())
        
        activity_combo = ttk.Combobox(frame, values=activity_names, state="readonly")
        activity_combo.pack(fill=tk.X, pady=5)
        if activity_names: activity_combo.current(0)

        unit_label = ttk.Label(frame, text="")
        unit_label.pack(anchor='w', pady=(10, 0))
        quantity_entry = ttk.Entry(frame)
        quantity_entry.pack(fill=tk.X)
        
        def update_unit_label(*args):
            idx = activity_combo.current()
            unit = activities[activity_keys[idx]]['unit']
            unit_label.config(text=f"Số lượng ({unit}):")
        activity_combo.bind("<<ComboboxSelected>>", update_unit_label)
        update_unit_label() # Initial call

        log_button = ttk.Button(frame, text="Ghi nhận", command=lambda: self._handle_log_submission(
            log_window, category_key, activity_keys[activity_combo.current()], quantity_entry.get()
        ))
        log_button.pack(pady=15)

    def _handle_log_submission(self, window: tk.Toplevel, cat_key: str, act_key: str, quantity_str: str):
        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                messagebox.showerror("Lỗi", "Số lượng phải là một số dương.", parent=window)
                return
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập một số hợp lệ.", parent=window)
            return

        improvement = self.ai.calculate_improvement(cat_key, act_key, quantity)
        self.data_manager.log_activity(cat_key, act_key, quantity, improvement)
        
        window.destroy()
        self.update_all_components() # Refresh everything
        messagebox.showinfo("Thành công!", f"Đã ghi nhận thành công!")

    def _handle_reset(self):
        if messagebox.askyesno("Xác nhận Reset", "Hành động này sẽ XÓA TOÀN BỘ LỊCH SỬ hoạt động của bạn và không thể hoàn tác. Bạn có chắc chắn?"):
            self.data_manager.reset_log()
            self.update_all_components()
            messagebox.showinfo("Hoàn tất", "Đã reset toàn bộ dữ liệu.")


def main():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        messagebox.showerror("Lỗi nghiêm trọng", f"Không thể tải hoặc đọc file '{CONFIG_FILE}'. Vui lòng kiểm tra lại file và chạy chương trình.")
        return

    ai = PerformanceAI(config)
    data_manager = DataManager(ACTIVITY_LOG_FILE)
    app = Application(ai, data_manager)
    app.mainloop()


if __name__ == "__main__":
    main()