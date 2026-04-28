import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import json
import os

class Expense:
    """Класс для представления одного расхода"""
    def __init__(self, amount, category, date):
        self.amount = float(amount)
        self.category = category
        self.date = date
        
    def to_dict(self):
        return {
            'amount': self.amount,
            'category': self.category,
            'date': self.date
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['amount'], data['category'], data['date'])

class ExpenseTracker:
    def __init__(self, window):
        self.window = window
        self.window.title("Трекер расходов")
        self.window.geometry("900x700")
        self.window.resizable(True, True)
        
        self.expenses = []
        self.filename = "expenses.json"
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основные фреймы
        input_frame = ttk.LabelFrame(self.window, text="Добавить расход", padding="10")
        input_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        filter_frame = ttk.LabelFrame(self.window, text="Фильтры", padding="10")
        filter_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        stats_frame = ttk.LabelFrame(self.window, text="Статистика", padding="10")
        stats_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        table_frame = ttk.LabelFrame(self.window, text="Список расходов", padding="10")
        table_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        
        # Настройка входных полей
        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5)
        self.amount_entry = ttk.Entry(input_frame, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Категория:").grid(row=0, column=2, padx=5, pady=5)
        self.category_var = tk.StringVar()
        categories = ["Еда", "Транспорт", "Развлечения", "Жильё", "Здоровье", "Образование", "Другое"]
        self.category_combo = ttk.Combobox(input_frame, textvariable=self.category_var, 
                                          values=categories, width=15, state="readonly")
        self.category_combo.set(categories[0])
        self.category_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Дата (ДД.ММ.ГГГГ):").grid(row=0, column=4, padx=5, pady=5)
        self.date_entry = ttk.Entry(input_frame, width=12)
        self.date_entry.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.date_entry.grid(row=0, column=5, padx=5, pady=5)
        
        self.add_button = ttk.Button(input_frame, text="Добавить расход", command=self.add_expense)
        self.add_button.grid(row=0, column=6, padx=10, pady=5)
        
        # Фильтры
        ttk.Label(filter_frame, text="Фильтр по категории:").grid(row=0, column=0, padx=5, pady=5)
        self.filter_category_var = tk.StringVar(value="Все")
        filter_categories = ["Все"] + categories
        self.filter_category_combo = ttk.Combobox(filter_frame, textvariable=self.filter_category_var,
                                                 values=filter_categories, width=15, state="readonly")
        self.filter_category_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="С даты:").grid(row=0, column=2, padx=5, pady=5)
        self.filter_date_from = ttk.Entry(filter_frame, width=12)
        self.filter_date_from.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="По дату:").grid(row=0, column=4, padx=5, pady=5)
        self.filter_date_to = ttk.Entry(filter_frame, width=12)
        self.filter_date_to.grid(row=0, column=5, padx=5, pady=5)
        
        self.apply_filter_button = ttk.Button(filter_frame, text="Применить фильтр", 
                                             command=self.apply_filter)
        self.apply_filter_button.grid(row=0, column=6, padx=10, pady=5)
        
        self.clear_filter_button = ttk.Button(filter_frame, text="Сбросить фильтр", 
                                             command=self.clear_filter)
        self.clear_filter_button.grid(row=0, column=7, padx=5, pady=5)
        
        # Статистика
        self.total_label = ttk.Label(stats_frame, text="Общая сумма: 0.00 ₽", 
                                    font=("Arial", 12, "bold"))
        self.total_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.period_label = ttk.Label(stats_frame, text="Сумма за период: 0.00 ₽", 
                                     font=("Arial", 12))
        self.period_label.grid(row=0, column=1, padx=20, pady=5)
        
        self.count_label = ttk.Label(stats_frame, text="Количество записей: 0", 
                                    font=("Arial", 12))
        self.count_label.grid(row=0, column=2, padx=10, pady=5)
        
        # Таблица расходов
        columns = ("amount", "category", "date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("category", text="Категория")
        self.tree.heading("date", text="Дата")
        
        self.tree.column("amount", width=150)
        self.tree.column("category", width=200)
        self.tree.column("date", width=150)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Кнопка удаления
        self.delete_button = ttk.Button(table_frame, text="Удалить выбранное", 
                                       command=self.delete_selected)
        self.delete_button.grid(row=1, column=0, pady=10)
        
        # Настройка весов для растягивания
        self.window.grid_rowconfigure(3, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
    def validate_input(self, amount_str, date_str):
        """Проверка корректности ввода"""
        # Проверка суммы
        try:
            amount = float(amount_str)
            if amount <= 0:
                return False, "Сумма должна быть положительным числом."
        except ValueError:
            return False, "Сумма должна быть числом."
        
        # Проверка даты
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
        except ValueError:
            return False, "Неверный формат даты. Используйте ДД.ММ.ГГГГ"
        
        return True, ""
    
    def add_expense(self):
        """Добавление нового расхода"""
        amount = self.amount_entry.get().strip()
        category = self.category_var.get()
        date = self.date_entry.get().strip()
        
        is_valid, error_msg = self.validate_input(amount, date)
        if not is_valid:
            messagebox.showerror("Ошибка", error_msg)
            return
        
        expense = Expense(amount, category, date)
        self.expenses.append(expense)
        
        self.save_data()
        self.refresh_table()
        self.update_stats()
        
        # Очистка полей
        self.amount_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%d.%m.%Y"))
        
        messagebox.showinfo("Успешно", f"Расход {float(amount):.2f} ₽ добавлен!")
    
    def delete_selected(self):
        """Удаление выбранной записи"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления.")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную запись?"):
            for item in selected:
                values = self.tree.item(item)['values']
                # Поиск соответствия в списке расходов
                amount = float(values[0])
                category = values[1]
                date = values[2]
                
                self.expenses = [e for e in self.expenses 
                               if not (e.amount == amount and e.category == category and e.date == date)]
            
            self.save_data()
            self.refresh_table()
            self.update_stats()
    
    def apply_filter(self):
        """Применение фильтров"""
        category_filter = self.filter_category_var.get()
        date_from_str = self.filter_date_from.get().strip()
        date_to_str = self.filter_date_to.get().strip()
        
        # Фильтрация данных
        filtered = self.expenses
        
        # Фильтр по категории
        if category_filter != "Все":
            filtered = [e for e in filtered if e.category == category_filter]
        
        # Фильтр по дате
        if date_from_str or date_to_str:
            try:
                if date_from_str:
                    date_from = datetime.strptime(date_from_str, "%d.%m.%Y")
                    filtered = [e for e in filtered 
                               if datetime.strptime(e.date, "%d.%m.%Y") >= date_from]
                
                if date_to_str:
                    date_to = datetime.strptime(date_to_str, "%d.%m.%Y")
                    filtered = [e for e in filtered 
                               if datetime.strptime(e.date, "%d.%m.%Y") <= date_to]
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты в фильтре.")
                return
        
        self.refresh_table(filtered)
        
        # Обновление статистики для отфильтрованных данных
        total_amount = sum(e.amount for e in filtered)
        self.total_label.config(text=f"Общая сумма: {total_amount:.2f} ₽")
        self.period_label.config(text=f"Сумма за период: {total_amount:.2f} ₽")
        self.count_label.config(text=f"Количество записей: {len(filtered)}")
    
    def clear_filter(self):
        """Сброс фильтров"""
        self.filter_category_var.set("Все")
        self.filter_date_from.delete(0, tk.END)
        self.filter_date_to.delete(0, tk.END)
        self.refresh_table()
        self.update_stats()
    
    def refresh_table(self, expenses=None):
        """Обновление таблицы"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        data = expenses if expenses is not None else self.expenses
        for expense in data:
            formatted_amount = f"{expense.amount:.2f} ₽"
            self.tree.insert("", tk.END, values=(formatted_amount, expense.category, expense.date))
    
    def update_stats(self):
        """Обновление статистики"""
        total_amount = sum(e.amount for e in self.expenses)
        self.total_label.config(text=f"Общая сумма: {total_amount:.2f} ₽")
        self.count_label.config(text=f"Количество записей: {len(self.expenses)}")
    
    def save_data(self):
        """Сохранение данных в JSON"""
        data = [expense.to_dict() for expense in self.expenses]
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_data(self):
        """Загрузка данных из JSON"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.expenses = [Expense.from_dict(item) for item in data]
                self.refresh_table()
                self.update_stats()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")

if __name__ == "__main__":
    window = tk.Tk()
    app = ExpenseTracker(window)
    window.mainloop()
