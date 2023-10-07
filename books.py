import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QListWidget, QLabel, QTextBrowser, QMessageBox
from PyQt6.QtGui import QPixmap, QGuiApplication
from PyQt6.QtCore import Qt, QUrl

import requests
import webbrowser

class BookSearchApp(QWidget):
    def __init__(self):
        super().__init__()

        # Set window size
        self.resize(800, 600)

        # Set window position next to the primary screen
        primary_screen = QGuiApplication.primaryScreen()
        screen_geometry = primary_screen.geometry()
        self.move(50, int((screen_geometry.height() - self.height()) / 2))

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Book Search')

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.search_box = QLineEdit()
        self.layout.addWidget(self.search_box)

        self.search_button = QPushButton('Search')
        self.layout.addWidget(self.search_button)

        self.result_list = QListWidget()
        self.layout.addWidget(self.result_list)

        self.book_cover = QLabel()
        self.layout.addWidget(self.book_cover)

        self.description_text = QTextBrowser()
        self.description_text.setOpenExternalLinks(False)  # Do not open links automatically
        self.description_text.anchorClicked.connect(self.link_clicked)  # Connect signal to slot
        self.layout.addWidget(self.description_text)

        self.bibtex_button = QPushButton('Download Citation')
        self.layout.addWidget(self.bibtex_button)

        self.search_button.clicked.connect(self.on_search_button_click)
        self.result_list.itemClicked.connect(self.on_list_item_click)
        self.search_box.returnPressed.connect(self.on_search_button_click)
        self.bibtex_button.clicked.connect(self.on_bibtex_button_click)

        self.current_book = {}

    def link_clicked(self, url):
        webbrowser.open(url.toString())

    def on_search_button_click(self):
        query = self.search_box.text()

        params = {'q': query}
        url = 'https://www.googleapis.com/books/v1/volumes'
        print("URL:", url)
        print("Params:", params)
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        self.result_list.clear()

        for item in data['items']:
            title = item['volumeInfo'].get('title', 'No title available')
            authors = ', '.join(item['volumeInfo'].get('authors', ['No authors available']))
            self.result_list.addItem(f'{title} by {authors}')

    def on_list_item_click(self, item):
        query = item.text().split(' by ')[0]

        params = {'q': query}
        response = requests.get('https://www.googleapis.com/books/v1/volumes', params=params)
        data = response.json()

        description = data['items'][0]['volumeInfo'].get('description', 'No description available')
        link = data['items'][0]['volumeInfo'].get('previewLink', 'No link available')
        self.current_book = data['items'][0]

        self.description_text.setHtml(f'{description}<br><br><a href="{link}">Google Books link</a>')
        
        try:
            image_url = data['items'][0]['volumeInfo']['imageLinks']['thumbnail']
            data = requests.get(image_url).content
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.book_cover.setPixmap(pixmap)
        except Exception as e:
            self.book_cover.setText('No image available')

    def on_bibtex_button_click(self):
        if not self.current_book:
            return

        bibtext = self.generate_bibtext(self.current_book)
        with open('citation.bib', 'w') as f:
            f.write(bibtext)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("BibTeX citation has been saved to citation.bib")
        msg.setWindowTitle("Download Complete")
        msg.exec()

    def generate_bibtext(self, book):
        # A basic example of a bibtex entry:
        # @book{dickens1850david,
        # title={David Copperfield},
        # author={Dickens, Charles},
        # year={1850},
        # publisher={Bradbury \& Evans}
        # }

        volume_info = book['volumeInfo']

        title = volume_info.get('title', '')
        authors = ' and '.join(volume_info.get('authors', ['']))
        publisher = volume_info.get('publisher', '')
        published_date = volume_info.get('publishedDate', '')
        pages = volume_info.get('pageCount', '')
        url = book['selfLink']  # URL of the book on Google Books
        description = volume_info.get('description', '')  # Book's description

        bibtext = f"@book{{googlebooks{book['id']},\n"
        bibtext += f" title={{ {title} }},\n"
        bibtext += f" author={{ {authors} }},\n"
        bibtext += f" year={{ {published_date} }},\n"
        bibtext += f" publisher={{ {publisher} }},\n"
        bibtext += f" pages={{ {pages} }},\n"
        bibtext += f" url={{ {url} }},\n"  # Include the URL of the book on Google Books
        bibtext += f" description={{ {description} }}\n"  # Include the book's description
        bibtext += "}"

        return bibtext

if __name__ == '__main__':
    app = QApplication(sys.argv)

    ex = BookSearchApp()
    ex.show()

    sys.exit(app.exec())
