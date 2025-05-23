import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psycopg2
import csv

# Конфигурация подключения к базе данных
DB_CONFIG = {
    'dbname': 'CURS',
    'user': 'postgres',
    'password': '666',
    'host': 'localhost',
    'port': 5432
}

class CustomerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("База Данных: Операции с клиентами")
        self.root.geometry("900x650")
        self.root.configure(bg="#f0f0f0")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabelframe', background='#e0e0e0', foreground='#333333', font=('Segoe UI', 10, 'bold'))
        style.configure('TLabel', background='#e0e0e0', font=('Segoe UI', 10))
        style.configure('TButton', background='#d0d0d0', font=('Segoe UI', 10))
        style.configure('TEntry', font=('Segoe UI', 10))
        style.configure('TCombobox', font=('Segoe UI', 10))
        style.configure('Treeview', font=('Arial', 10), background='#ffffff', fieldbackground='#ffffff', rowheight=25)
        style.configure('Treeview.Heading', font=('Segoe UI', 11, 'bold'), background='#c0c0c0')

        # --- Фрейм для фильтров ---
        filter_frame = ttk.Labelframe(root, text="Фильтрация")
        filter_frame.pack(fill="x", padx=15, pady=10)

        # Категория возраста
        ttk.Label(filter_frame, text="Категория возраста:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.age_category_cb = ttk.Combobox(filter_frame, state="readonly", width=20)
        self.age_category_cb.grid(row=0, column=1, padx=5, pady=5)

        # Spending Score min/max
        ttk.Label(filter_frame, text="Spending Score:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Label(filter_frame, text="Min").grid(row=1, column=1, sticky="e")
        self.min_score_entry = ttk.Entry(filter_frame, width=8)
        self.min_score_entry.grid(row=1, column=2, padx=(0,5))
        ttk.Label(filter_frame, text="Max").grid(row=1, column=3, sticky="e")
        self.max_score_entry = ttk.Entry(filter_frame, width=8)
        self.max_score_entry.grid(row=1, column=4, padx=(0,5))

        # Purchase Frequency min/max
        ttk.Label(filter_frame, text="Purchase Frequency:").grid(row=2, column=0, sticky="w", padx=5)
        ttk.Label(filter_frame, text="Min").grid(row=2, column=1, sticky="e")
        self.min_freq_entry = ttk.Entry(filter_frame, width=8)
        self.min_freq_entry.grid(row=2, column=2, padx=(0,5))
        ttk.Label(filter_frame, text="Max").grid(row=2, column=3, sticky="e")
        self.max_freq_entry = ttk.Entry(filter_frame, width=8)
        self.max_freq_entry.grid(row=2, column=4, padx=(0,5))

        # Transaction Amount min/max
        ttk.Label(filter_frame, text="Transaction Amount:").grid(row=3, column=0, sticky="w", padx=5)
        ttk.Label(filter_frame, text="Min").grid(row=3, column=1, sticky="e")
        self.min_amount_entry = ttk.Entry(filter_frame, width=8)
        self.min_amount_entry.grid(row=3, column=2, padx=(0,5))
        ttk.Label(filter_frame, text="Max").grid(row=3, column=3, sticky="e")
        self.max_amount_entry = ttk.Entry(filter_frame, width=8)
        self.max_amount_entry.grid(row=3, column=4, padx=(0,5))

        # Поиск по ID
        ttk.Label(filter_frame, text="Поиск по ID:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.id_entry = ttk.Entry(filter_frame, width=12)
        self.id_entry.grid(row=4, column=1, padx=5)

        # Кнопки
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.grid(row=5, column=0, columnspan=5, pady=(10,5))
        ttk.Button(btn_frame, text="Применить", command=self.load_data).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Очистить", command=self.clear_filters).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Экспорт CSV", command=self.export_csv).pack(side="left", padx=5)

        # --- Таблица ---
        columns = ("id", "age", "income", "score", "freq", "amount", "cat")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")
        self.tree.pack(fill="both", expand=True, padx=15, pady=5)
        headings = ["ID", "Age", "Income", "Score", "Freq", "Amount", "Category"]
        for col, heading in zip(columns, headings):
            self.tree.heading(col, text=heading,
                              command=lambda _col=col: self.sort_column(_col, False))
            self.tree.column(col, anchor="center")

        self.connect_and_load_categories()
        self.load_data()
    def sort_column(self, col, reverse):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children()]
        try:
            data.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0], reverse=reverse)

        for index, (_, k) in enumerate(data):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def connect(self):
        return psycopg2.connect(**DB_CONFIG)

    def connect_and_load_categories(self):
        try:
            conn = self.connect()
            cur = conn.cursor()
            cur.execute("SELECT age_category FROM age_categories ORDER BY age_category_id")
            categories = [row[0] for row in cur.fetchall()]
            self.age_category_cb['values'] = ["Все"] + categories
            self.age_category_cb.current(0)
            conn.close()
        except Exception as e:
            messagebox.showerror("Ошибка подключения", str(e))

    def load_data(self):
        try:
            conn = self.connect()
            cur = conn.cursor()
            query = """
            SELECT c.customer_id, c.age, c.annual_income, c.spending_score,
                   c.purchase_frequency, c.transaction_amount, a.age_category
            FROM customers c
            JOIN age_categories a ON c.age_category_id = a.age_category_id
            WHERE 1=1
            """
            params = []

            cat = self.age_category_cb.get()
            if cat and cat != "Все":
                query += " AND a.age_category = %s"
                params.append(cat)

            if self.min_score_entry.get():
                query += " AND c.spending_score >= %s"
                params.append(self.min_score_entry.get())
            if self.max_score_entry.get():
                query += " AND c.spending_score <= %s"
                params.append(self.max_score_entry.get())

            if self.min_freq_entry.get():
                query += " AND c.purchase_frequency >= %s"
                params.append(self.min_freq_entry.get())
            if self.max_freq_entry.get():
                query += " AND c.purchase_frequency <= %s"
                params.append(self.max_freq_entry.get())

            if self.min_amount_entry.get():
                query += " AND c.transaction_amount >= %s"
                params.append(self.min_amount_entry.get())
            if self.max_amount_entry.get():
                query += " AND c.transaction_amount <= %s"
                params.append(self.max_amount_entry.get())

            if self.id_entry.get():
                query += " AND c.customer_id = %s"
                params.append(self.id_entry.get())

            cur.execute(query, params)
            rows = cur.fetchall()
            conn.close()

            self.tree.delete(*self.tree.get_children())
            for row in rows:
                self.tree.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", str(e))

    def clear_filters(self):
        self.age_category_cb.current(0)
        for entry in [self.min_score_entry, self.max_score_entry,
                      self.min_freq_entry, self.max_freq_entry,
                      self.min_amount_entry, self.max_amount_entry,
                      self.id_entry]:
            entry.delete(0, tk.END)
        self.load_data()

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([self.tree.heading(c)['text'] for c in self.tree['columns']])
                for item in self.tree.get_children():
                    writer.writerow(self.tree.item(item)['values'])
            messagebox.showinfo("Экспорт", f"Данные сохранены в {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))

if __name__ == '__main__':
    root = tk.Tk()
    app = CustomerApp(root)
    root.mainloop()
