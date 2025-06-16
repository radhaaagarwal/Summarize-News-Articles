import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'

import tkinter as tk
from tkinter import messagebox
import nltk
from textblob import TextBlob
from newspaper import Article
import threading

# IMPORTANT: Ensure NLTK data is downloaded once, interactively.
# Run these in your terminal's Python shell IF YOU HAVEN'T ALREADY:
# python3
# >>> import nltk
# >>> nltk.download('punkt')
# >>> nltk.download('punkt_tab')
# >>> exit()

class NewsApp:
    def __init__(self, root):
        self.root = root
        self.setup_gui()
        
    def setup_gui(self):
        self.root.title("News Summarizer")
        self.root.geometry('800x900')
        self.root.configure(bg='#f0f0f0')
        
        # REMOVED: The problematic macOS window style call that was causing the black screen
        # try:
        #     self.root.tk.call('tk::unsupported::MacWindowStyle', 'style', self.root._w, 'document')
        # except:
        #     pass
        
        # Create main frame directly instead of complex canvas setup
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create scrollable area
        canvas = tk.Canvas(main_container, bg='#f0f0f0', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Now create all widgets in the scrollable frame
        self.create_widgets(scrollable_frame)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Force update to ensure proper rendering
        self.root.update_idletasks()
        
    def create_widgets(self, parent):
        # Main container with padding
        main_frame = tk.Frame(parent, bg='#f0f0f0', padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="📰 News Article Summarizer", 
                font=('Arial', 18, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # URL Input Section
        url_frame = tk.Frame(main_frame, bg='#f0f0f0')
        url_frame.pack(fill='x', pady=(0, 20))
        
        url_label = tk.Label(url_frame, text="🔗 Enter Article URL:", 
                font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#34495e')
        url_label.pack(anchor='w', pady=(0, 5))
        
        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(url_frame, textvariable=self.url_var, font=('Arial', 11),
                                 bg='white', fg='black', relief='solid', bd=1)
        self.url_entry.pack(fill='x', pady=(0, 10), ipady=5)
        self.url_entry.bind('<Return>', lambda e: self.start_summarize())
        
        # Summarize button
        self.summarize_btn = tk.Button(url_frame, text="📊 Summarize Article", 
                                      command=self.start_summarize,
                                      font=('Arial', 12, 'bold'), bg='#3498db', fg='white',
                                      padx=20, pady=10, relief='raised', bd=2,
                                      activebackground='#2980b9', activeforeground='white')
        self.summarize_btn.pack(pady=10)
        
        # Results Section
        results_frame = tk.Frame(main_frame, bg='#f0f0f0')
        results_frame.pack(fill='both', expand=True, pady=(20, 0))
        
        # Title Result
        self.create_result_section(results_frame, "📝 Title", "title_text", height=3)
        
        # Author Result
        self.create_result_section(results_frame, "👤 Author(s)", "author_text", height=2)
        
        # Publication Date Result
        self.create_result_section(results_frame, "📅 Publication Date", "date_text", height=2)
        
        # Summary Result
        self.create_result_section(results_frame, "📄 Summary", "summary_text", height=12)
        
        # Sentiment Result
        self.create_result_section(results_frame, "💭 Sentiment Analysis", "sentiment_text", height=3)
        
        # Status label
        self.status_label = tk.Label(main_frame, text="Ready to summarize articles", 
                                   font=('Arial', 10), bg='#f0f0f0', fg='#7f8c8d')
        self.status_label.pack(pady=(20, 0))
        
    def create_result_section(self, parent, title, attr_name, height):
        section_frame = tk.Frame(parent, bg='#f0f0f0')
        section_frame.pack(fill='x', pady=(0, 15))
        
        label = tk.Label(section_frame, text=title, font=('Arial', 11, 'bold'), 
                bg='#f0f0f0', fg='#2c3e50')
        label.pack(anchor='w', pady=(0, 5))
        
        text_widget = tk.Text(section_frame, height=height, font=('Arial', 10),
                             bg='white', fg='black', relief='solid', bd=1,
                             wrap='word', state='disabled', padx=8, pady=8)
        text_widget.pack(fill='x')
        
        setattr(self, attr_name, text_widget)
        
    def update_status(self, message, color='#7f8c8d'):
        self.status_label.config(text=message, fg=color)
        self.root.update_idletasks()
        
    def clear_results(self):
        for widget_name in ['title_text', 'author_text', 'date_text', 'summary_text', 'sentiment_text']:
            widget = getattr(self, widget_name)
            widget.config(state='normal')
            widget.delete('1.0', 'end')
            widget.config(state='disabled')
            
    def start_summarize(self):
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL to summarize.")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_var.set(url)
        
        self.clear_results()
        self.update_status("🔄 Processing article... Please wait", '#e67e22')
        self.summarize_btn.config(state='disabled', text="Processing...")
        
        # Run in separate thread
        def process():
            try:
                self.process_article(url)
            except Exception as e:
                self.root.after(0, lambda: self.show_error(str(e)))
            finally:
                self.root.after(0, lambda: self.summarize_btn.config(state='normal', text="📊 Summarize Article"))
        
        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()
        
    def process_article(self, url):
        try:
            # Create and process article
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()
            
            # Update GUI in main thread
            self.root.after(0, lambda: self.update_results(article))
            
        except Exception as e:
            raise e
            
    def update_results(self, article):
        try:
            # Title
            self.update_text_widget(self.title_text, article.title or "No title found")
            
            # Authors
            authors = ", ".join(article.authors) if article.authors else "No authors found"
            self.update_text_widget(self.author_text, authors)
            
            # Publication date
            pub_date = str(article.publish_date) if article.publish_date else "No publication date found"
            self.update_text_widget(self.date_text, pub_date)
            
            # Summary
            summary = article.summary or "No summary could be generated"
            self.update_text_widget(self.summary_text, summary)
            
            # Sentiment analysis
            if article.text:
                analysis = TextBlob(article.text)
                polarity = analysis.polarity
                subjectivity = analysis.subjectivity
                
                if polarity > 0.1:
                    sentiment = "Positive 😊"
                elif polarity < -0.1:
                    sentiment = "Negative 😞"
                else:
                    sentiment = "Neutral 😐"
                
                sentiment_text = f"Sentiment: {sentiment}\nPolarity: {polarity:.3f} | Subjectivity: {subjectivity:.3f}"
            else:
                sentiment_text = "Could not analyze sentiment - no text content found"
                
            self.update_text_widget(self.sentiment_text, sentiment_text)
            
            self.update_status("✅ Article processed successfully!", '#27ae60')
            
        except Exception as e:
            self.show_error(f"Error updating results: {str(e)}")
            
    def update_text_widget(self, widget, text):
        widget.config(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', text)
        widget.config(state='disabled')
        
    def show_error(self, error_msg):
        self.update_text_widget(self.summary_text, f"❌ Error: {error_msg}\n\nPlease check:\n- URL is valid and accessible\n- Internet connection is working\n- Website allows scraping")
        self.update_status("❌ Error processing article", '#e74c3c')
        print(f"Error: {error_msg}")

# Create and run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = NewsApp(root)
    
    print("🚀 News Summarizer started successfully!")
    print("📝 Paste a news article URL and click 'Summarize Article'")
    print("⌨️  Or press Enter after pasting the URL")
    
    root.mainloop()