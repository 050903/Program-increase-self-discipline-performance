import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- CONSTANTS ---
CONFIG_FILE = 'config.json'
DATA_FILE = 'performance_data.json'
INITIAL_SCORE = 30.0
APP_TITLE = "Trình Theo Dõi Hiệu Suất Cá Nhân"
WINDOW_GEOMETRY = "900x650"

# Set font for Matplotlib to support Vietnamese
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'Tahoma']
plt.rcParams['axes.unicode_minus'] = False


class PerformanceAI:
    """
    Handles the business logic of performance calculation.
    It is completely decoupled from the UI.
    """
    def __init__(self, config_path: str):
        self.config = self._load_json(config_path)
        if not self.config:
            messagebox.showerror("Lỗi", f"Không thể tải file cấu hình '{config_path}'. Chương trình sẽ thoát.")
            exit()
        self.categories = list(self.config.keys())

    def _load_json(self, file_path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def calculate_improvement(self, category_key: str, activity_key: str, quantity: float) -> float:
        """Calculates the score improvement for a given activity."""
        try:
            activity = self.config[category_key]['activities'][activity_key]
            impact = activity['impact_per_unit']
            return quantity * impact
        except KeyError:
            return 0.0

    def get_overall_performance(self, scores: Dict[str, float]) -> float:
        """Calculates the weighted overall performance score."""
        total_weighted_score = 0.0
        for cat_key, cat_config in self.config.items():
            weight = cat_config.get('weight', 0)
            score = scores.get(cat_key, 0)
            total_weighted_score += score * weight
        return total_weighted_score


class DataManager:
    """Handles loading and saving of user performance data."""
    def __init__(self, data_path: str, categories: List[str]):
        self.data_path = data_path
        self.categories = categories

    def load_scores(self) -> Dict[str, float]:
        """Loads scores from the data file, or returns initial scores if not found."""
        if not os.path.exists(self.data_path):
            return {cat: INITIAL_SCORE for cat in self.categories}
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, TypeError):
            messagebox.showwarning("Cảnh báo", "File dữ liệu bị lỗi. Sẽ tạo lại dữ liệu ban đầu.")
            return {cat: INITIAL_SCORE for cat in self.categories}

    def save_scores(self, scores: Dict[str, float]) -> None:
        """Saves the scores to the data file."""
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(scores, f, indent=4, ensure_ascii=False)


class Application(tk.Tk):
    """
    The main GUI application class.
    It acts as the Controller, connecting the UI (View) with the data and logic (Model).
    """
    def __init__(self, ai: PerformanceAI, data_manager: DataManager):
        super().__init__()
        self.ai = ai
        self.data_manager = data_manager
        self.scores = self.data_manager.load_scores()
        self.wedges: List[plt.Artist] = []

        self._setup_window()
        self._setup_ui()
        self.update_chart()

    def _setup_window(self):
        """Configures the main application window."""
        self.title(APP_TITLE)
        self.geometry(WINDOW_GEOMETRY)

    def _setup_ui(self):
        """Creates and arranges all the UI widgets."""
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title Label
        title_label = ttk.Label(main_frame, text="Biểu Đồ Hiệu Suất Cá Nhân", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 10))

        # Matplotlib Figure and Canvas
        self.fig = plt.Figure(figsize=(7, 5.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Connect the click event
        self.fig.canvas.mpl_connect('button_press_event', self._on_pie_click)

        # Reset Button
        reset_button = ttk.Button(main_frame, text="Reset Toàn Bộ Điểm Số", command=self._handle_reset)
        reset_button.pack(pady=10)

    def update_chart(self):
        """Clears and redraws the performance chart with current data."""
        self.ax.clear()
        
        labels = [self.ai.config[key]['name'] for key in self.ai.categories]
        values = [self.scores[key] for key in self.ai.categories]
        overall_score = self.ai.get_overall_performance(self.scores)

        # Explode the slice with the highest score for visual effect
        explode = [0.05 if v == max(values) else 0 for v in values]

        wedges, texts, autotexts = self.ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=140,
            pctdistance=0.85,
            explode=explode,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
        )
        self.wedges = wedges # Store wedge objects for click detection

        # Draw a center circle to make it a donut chart
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        self.ax.add_artist(centre_circle)

        # Display overall score in the center
        self.ax.text(0, 0, f"{overall_score:.1f}\nTổng thể",
                     ha='center', va='center', fontsize=24, color='#33a02c', weight='bold')
        
        self.ax.axis('equal')
        self.fig.tight_layout()
        self.canvas.draw()

    def _on_pie_click(self, event):
        """Handles click events on the pie chart to open the logging window."""
        if event.inaxes != self.ax:
            return
        
        for i, wedge in enumerate(self.wedges):
            # Check if the click was inside this wedge
            if wedge.contains(event)[0]:
                category_key = self.ai.categories[i]
                self._open_log_activity_window(category_key)
                # Animate the click for user feedback
                self._animate_click(wedge)
                break

    def _animate_click(self, wedge: plt.Artist):
        """Provides visual feedback when a wedge is clicked."""
        original_color = wedge.get_facecolor()
        wedge.set_facecolor('#ffcc00') # Highlight color
        self.canvas.draw()
        self.after(200, lambda: (wedge.set_facecolor(original_color), self.canvas.draw()))

    def _open_log_activity_window(self, category_key: str):
        """Creates a new Toplevel window to log an activity for a specific category."""
        log_window = tk.Toplevel(self)
        log_window.title(f"Ghi nhận: {self.ai.config[category_key]['name']}")
        log_window.geometry("350x200")
        log_window.transient(self) # Keep window on top
        log_window.grab_set() # Modal behavior

        frame = ttk.Frame(log_window, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        # Activity selection
        ttk.Label(frame, text="Chọn hoạt động:").pack(anchor='w')
        activities = self.ai.config[category_key]['activities']
        activity_names = [act['name'] for act in activities.values()]
        activity_keys = list(activities.keys())
        
        activity_combo = ttk.Combobox(frame, values=activity_names, state="readonly")
        activity_combo.pack(fill=tk.X, pady=5)
        if activity_names:
            activity_combo.current(0)

        # Quantity input
        unit = activities[activity_keys[0]]['unit'] if activity_keys else ""
        quantity_label = ttk.Label(frame, text=f"Số lượng ({unit}):")
        quantity_label.pack(anchor='w', pady=(10, 0))
        quantity_entry = ttk.Entry(frame)
        quantity_entry.pack(fill=tk.X)
        
        def update_unit_label(*args):
            """Update unit when activity changes."""
            selected_idx = activity_combo.current()
            new_unit = activities[activity_keys[selected_idx]]['unit']
            quantity_label.config(text=f"Số lượng ({new_unit}):")
        activity_combo.bind("<<ComboboxSelected>>", update_unit_label)

        # Log button
        log_button = ttk.Button(frame, text="Ghi nhận", command=lambda: self._handle_log_submission(
            log_window, category_key, activity_keys[activity_combo.current()], quantity_entry.get()
        ))
        log_button.pack(pady=15)

    def _handle_log_submission(self, window: tk.Toplevel, cat_key: str, act_key: str, quantity_str: str):
        """Validates and processes the activity log submission."""
        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                messagebox.showerror("Lỗi", "Số lượng phải là một số dương.", parent=window)
                return
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập một số hợp lệ cho số lượng.", parent=window)
            return

        # AI calculates improvement
        improvement = self.ai.calculate_improvement(cat_key, act_key, quantity)
        
        # Update scores
        old_score = self.scores[cat_key]
        self.scores[cat_key] = min(100.0, old_score + improvement)
        
        # Save and update UI
        self.data_manager.save_scores(self.scores)
        self.update_chart()
        
        window.destroy()
        messagebox.showinfo("Thành công!", f"Đã ghi nhận thành công!\n'{self.ai.config[cat_key]['name']}' đã tăng +{improvement:.2f} điểm.")

    def _handle_reset(self):
        """Handles the score reset functionality with confirmation."""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn reset toàn bộ điểm số về ban đầu?"):
            self.scores = {cat: INITIAL_SCORE for cat in self.ai.categories}
            self.data_manager.save_scores(self.scores)
            self.update_chart()
            messagebox.showinfo("Hoàn tất", "Đã reset toàn bộ điểm số.")


def main():
    """The main entry point of the application."""
    # Ensure config file exists
    if not os.path.exists(CONFIG_FILE):
        messagebox.showerror("Lỗi nghiêm trọng", f"Không tìm thấy file '{CONFIG_FILE}'. Vui lòng tạo file này và chạy lại chương trình.")
        return

    ai = PerformanceAI(CONFIG_FILE)
    data_manager = DataManager(DATA_FILE, ai.categories)
    app = Application(ai, data_manager)
    app.mainloop()


if __name__ == "__main__":
    main()