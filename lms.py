import streamlit as st
import pandas as pd
import datetime
import json
import os
import hashlib
import random
import string

from books_data import POPULAR_BOOKS


# Initialize session state variables
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'books' not in st.session_state:
    st.session_state.books = []
if 'borrowings' not in st.session_state:
    st.session_state.borrowings = []
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'fines' not in st.session_state:
    st.session_state.fines = {}
if 'book_recommendations' not in st.session_state:
    st.session_state.book_recommendations = {}
if 'return_requests' not in st.session_state:
    st.session_state.return_requests = []

# File paths
USERS_FILE = "srp/users.json"
BOOKS_FILE = "srp/books.json"
BORROWINGS_FILE = "srp/borrowings.json"
TRANSACTIONS_FILE = "srp/transactions.json"
FINES_FILE = "srp/fines.json"
RETURN_REQUESTS_FILE = "srp/return_requests.json"

# Set page configuration
st.set_page_config(
    page_title="GRIET Library Management System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown(""" a""", unsafe_allow_html=True)

# Predefined datasets
BOOK_CATEGORIES = []  # Will be set after loading books

# Set BOOK_LANGUAGES after loading books
BOOK_LANGUAGES = sorted(list({book["language"] for book in st.session_state.books if "language" in book}))

# Initialize custom datasets in session state
if 'custom_categories' not in st.session_state:
    st.session_state.custom_categories = []
if 'custom_languages' not in st.session_state:
    st.session_state.custom_languages = []
if 'custom_authors' not in st.session_state:
    st.session_state.custom_authors = []
if 'custom_books' not in st.session_state:
    st.session_state.custom_books = []

PRICE_RANGES = [
    (0, 10, "Under $10"),
    (10, 20, "$10 - $20"),
    (20, 30, "$20 - $30"),
    (30, 50, "$30 - $50"),
    (50, 100, "$50 - $100"),
    (100, float('inf'), "Over $100")
]


# Helper functions
def load_data():
    """Load data from JSON files"""
    # No import from books_data
    os.makedirs("srp", exist_ok=True)

    # Load users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            st.session_state.users = json.load(f)
    else:
        st.session_state.users = {
            "admin": {
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "is_admin": True,
                "name": "Administrator"
            }
        }
        save_users()

    # Load books
    if os.path.exists(BOOKS_FILE) and os.path.getsize(BOOKS_FILE) > 0:
        with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
            st.session_state.books = json.load(f)
    else:
        st.session_state.books = []
        save_books()

    # Load borrowings
    if os.path.exists(BORROWINGS_FILE):
        with open(BORROWINGS_FILE, 'r') as f:
            st.session_state.borrowings = json.load(f)
    else:
        st.session_state.borrowings = []
        save_borrowings()

    # Load transactions
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'r') as f:
            st.session_state.transactions = json.load(f)
    else:
        st.session_state.transactions = []
        save_transactions()

    # Load fines
    if os.path.exists(FINES_FILE):
        with open(FINES_FILE, 'r') as f:
            st.session_state.fines = json.load(f)
    else:
        st.session_state.fines = {}
        save_fines()

    # Load return requests
    if os.path.exists(RETURN_REQUESTS_FILE):
        with open(RETURN_REQUESTS_FILE, 'r') as f:
            st.session_state.return_requests = json.load(f)
    else:
        st.session_state.return_requests = []
        save_return_requests()

    # Update session state with custom datasets
    # Set global categories and languages for use elsewhere
    global BOOK_CATEGORIES, BOOK_LANGUAGES
    BOOK_CATEGORIES = sorted(list(set(book["category"] for book in st.session_state.books)))
    BOOK_LANGUAGES = sorted(list(set(book["language"] for book in st.session_state.books)))
    st.session_state.custom_categories = BOOK_CATEGORIES.copy()
    st.session_state.custom_languages = BOOK_LANGUAGES.copy()
    st.session_state.custom_authors = list(set([book["author"] for book in st.session_state.books]))
    st.session_state.custom_books = st.session_state.books.copy()

    generate_recommendations()
    st.session_state.initialized = True


def save_users():
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(st.session_state.users, f)


def save_books():
    """Save books to JSON file"""
    with open(BOOKS_FILE, 'w') as f:
        json.dump(st.session_state.books, f)


def save_borrowings():
    """Save borrowings to JSON file"""
    with open(BORROWINGS_FILE, 'w') as f:
        json.dump(st.session_state.borrowings, f)


def save_transactions():
    """Save transactions to JSON file"""
    with open(TRANSACTIONS_FILE, 'w') as f:
        json.dump(st.session_state.transactions, f)


def save_fines():
    """Save fines to JSON file"""
    with open(FINES_FILE, 'w') as f:
        json.dump(st.session_state.fines, f)


def save_return_requests():
    """Save return requests to JSON file"""
    with open(RETURN_REQUESTS_FILE, 'w') as f:
        json.dump(st.session_state.return_requests, f)


def generate_book_id():
    """Generate a unique book ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def hash_password(password):
    """Hash a password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    return hash_password(password) == hashed_password


def calculate_fine(borrow_date, return_date):
    """Calculate fine for late return"""
    borrow_date = datetime.datetime.strptime(borrow_date, "%Y-%m-%d")
    return_date = datetime.datetime.strptime(return_date, "%Y-%m-%d")
    days_overdue = (return_date - borrow_date).days - 14  # 14 days borrowing period
    if days_overdue > 0:
        return days_overdue * 1.0  # $1 per day fine
    return 0.0


def generate_recommendations():
    """Generate book recommendations based on borrowing patterns"""
    # Count how many times each book has been borrowed
    book_counts = {}
    for borrowing in st.session_state.borrowings:
        if borrowing["book_id"] not in book_counts:
            book_counts[borrowing["book_id"]] = 0
        book_counts[borrowing["book_id"]] += 1

    # Sort books by popularity
    sorted_books = sorted(book_counts.items(), key=lambda x: x[1], reverse=True)

    # Generate recommendations for each book
    for book_id, count in sorted_books:
        # Find similar books (same category or author)
        book = next(b for b in st.session_state.books if b["id"] == book_id)
        similar_books = [
            b for b in st.session_state.books
            if b["id"] != book_id and
               (b["category"] == book["category"] or b["author"] == book["author"])
        ]

        # Sort similar books by popularity
        similar_books.sort(key=lambda b: book_counts.get(b["id"], 0), reverse=True)

        # Store top 3 recommendations
        st.session_state.book_recommendations[book_id] = [
            b["id"] for b in similar_books[:3]
        ]


# Load data on startup if not initialized
if not st.session_state.initialized:
    load_data()

# Main UI
st.markdown('<h1 class="main-header">📚 GRIET Library Management System</h1>', unsafe_allow_html=True)

# Login/Register section
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.markdown('<h2 class="sub-header">Login</h2>', unsafe_allow_html=True)
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if login_username in st.session_state.users:
                if verify_password(login_password, st.session_state.users[login_username]["password"]):
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.session_state.is_admin = st.session_state.users[login_username].get("is_admin", False)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Incorrect password!")
            else:
                st.error("User not found!")

    with tab2:
        st.markdown('<h2 class="sub-header">Register</h2>', unsafe_allow_html=True)
        reg_username = st.text_input("Username", key="reg_username")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        reg_name = st.text_input("Full Name", key="reg_name")
        reg_is_admin = st.checkbox("Register as Admin", key="reg_is_admin")

        if st.button("Register"):
            if reg_username and reg_password and reg_confirm_password and reg_name:
                if reg_password != reg_confirm_password:
                    st.error("Passwords do not match!")
                elif reg_username in st.session_state.users:
                    st.error("Username already exists!")
                else:
                    st.session_state.users[reg_username] = {
                        "password": hash_password(reg_password),
                        "is_admin": reg_is_admin,
                        "name": reg_name
                    }
                    save_users()
                    st.success("Registration successful! Please login.")
            else:
                st.error("Please fill all fields!")

# Main application after login
else:
    # Sidebar with user info and logout
    with st.sidebar:
        st.markdown('<div class="sidebar-avatar"><img src="https://api.dicebear.com/7.x/identicon/svg?seed=' + str(st.session_state.username) + '" alt="avatar"></div>', unsafe_allow_html=True)
        st.markdown(f"### 👋 Welcome, <span style='color:#4F8EF7'>{st.session_state.username}</span>", unsafe_allow_html=True)
        st.markdown(f"*Role:* <span style='color:#7F53AC'>{'Administrator' if st.session_state.is_admin else 'User'}</span>", unsafe_allow_html=True)
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.is_admin = False
            st.rerun()

    # Main tabs
    if st.session_state.is_admin:
        tab1, tab2, tab3, tab4 = st.tabs(["📚 Browse Books", "🔄 Borrow/Return", "💳 Transactions", "🛠️ Admin Panel"])
    else:
        tab1, tab2, tab3 = st.tabs(["📚 Browse Books", "🔄 Borrow/Return", "💳 Transactions"])

    # Browse Books tab
    with tab1:
        st.markdown('<h2 class="sub-header">📚 Browse Books</h2>', unsafe_allow_html=True)

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            categories = ["All"] + sorted(BOOK_CATEGORIES)
            selected_category = st.selectbox("Category", categories)

        with col2:
            languages = ["All"] + sorted(BOOK_LANGUAGES)
            selected_language = st.selectbox("Language", languages)

        with col3:
            search_query = st.text_input("Search by title or author")

        # Filter books
        filtered_books = st.session_state.books
        if selected_category != "All":
            filtered_books = [book for book in filtered_books if book["category"] == selected_category]
        if selected_language != "All":
            filtered_books = [book for book in filtered_books if book["language"] == selected_language]
        if search_query:
            search_query = search_query.lower()
            filtered_books = [book for book in filtered_books
                              if search_query in book["title"].lower() or
                              search_query in book["author"].lower()]

        # Display books
        for book in filtered_books:
            with st.container():
                st.markdown('<div class="book-card">', unsafe_allow_html=True)
                if book['title'] in [b['title'] for b in POPULAR_BOOKS]:
                    st.markdown('<div class="popular-badge">🌟 Popular</div>', unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 2, 1])

                with col1:
                    if book.get('cover_url'):
                        st.image(book['cover_url'], width=150)
                    else:
                        st.image("https://via.placeholder.com/150x200?text=No+Cover", width=150)

                with col2:
                    st.markdown(f"### {book['title']}")
                    st.markdown(f"*Author:* {book['author']}")
                    st.markdown(f"*Category:* {book['category']}")
                    st.markdown(f"*Language:* {book['language']}")
                    if book.get('description'):
                        st.markdown(f"*Description:* {book['description']}")

                    # Show recommendations
                    if book["id"] in st.session_state.book_recommendations:
                        st.markdown("*Students also read:*")
                        for rec_id in st.session_state.book_recommendations[book["id"]]:
                            rec_book = next(b for b in st.session_state.books if b["id"] == rec_id)
                            st.markdown(f"- {rec_book['title']} by {rec_book['author']}")

                with col3:
                    if st.session_state.is_admin:
                        st.markdown(f"*Price:* ${book['price']:.2f}")
                    st.markdown(f"*Available:* {book['available']}/{book['quantity']}")
                    if book['available'] > 0:
                        if st.button("Borrow", key=f"borrow_{book['id']}"):
                            # Add borrowing record
                            borrowing = {
                                "id": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
                                "book_id": book["id"],
                                "book_title": book["title"],
                                "username": st.session_state.username,
                                "borrow_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                                "return_date": None,
                                "price": book["price"]
                            }
                            st.session_state.borrowings.append(borrowing)
                            save_borrowings()

                            # Add transaction record
                            transaction = {
                                "id": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
                                "type": "borrow",
                                "book_id": book["id"],
                                "book_title": book["title"],
                                "username": st.session_state.username,
                                "amount": book["price"],
                                "date": datetime.datetime.now().strftime("%Y-%m-%d")
                            }
                            st.session_state.transactions.append(transaction)
                            save_transactions()
                            # Update book availability
                            book["available"] -= 1
                            save_books()
                            st.success(
                                f"Book '{book['title']}' borrowed successfully! Amount: ${book['price']:.2f}")
                            st.rerun()
                        else:
                            st.markdown("*Out of Stock*")
                st.markdown('</div>', unsafe_allow_html=True)
        if not filtered_books:
            st.info("No books found matching your criteria.")

    # Borrow/Return tab
    with tab2:
        st.markdown('<h2 class="sub-header">🔄 My Borrowings</h2>', unsafe_allow_html=True)

        # Filter borrowings for current user
        user_borrowings = [b for b in st.session_state.borrowings if b["username"] == st.session_state.username]

        if user_borrowings:
            for borrowing in user_borrowings:
                with st.container():
                    st.markdown('<div class="book-card">', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.markdown(f"{borrowing['book_title']}")
                        st.markdown(f"*Borrowed on:* {borrowing['borrow_date']}")

                    with col2:
                        if borrowing['return_date']:
                            st.markdown(f"*Returned on:* {borrowing['return_date']}")
                        else:
                            st.markdown("*Status:* Borrowed")

                    with col3:
                        if not borrowing['return_date']:
                            if st.button("Request Return", key=f"return_{borrowing['id']}"):
                                # Check if request already exists
                                existing_request = next(
                                    (r for r in st.session_state.return_requests
                                     if r["borrowing_id"] == borrowing["id"]),
                                    None
                                )

                                if not existing_request:
                                    return_request = {
                                        "id": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
                                        "borrowing_id": borrowing["id"],
                                        "book_id": borrowing["book_id"],
                                        "book_title": borrowing["book_title"],
                                        "username": st.session_state.username,
                                        "request_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                                        "status": "pending",
                                        "fine_amount": 0,
                                        "notes": ""
                                    }
                                    st.session_state.return_requests.append(return_request)
                                    save_return_requests()
                                    st.success("Return request submitted successfully! Waiting for admin approval.")
                                else:
                                    st.info("Return request already submitted. Waiting for admin approval.")
                                st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("You haven't borrowed any books yet.")

    # Transactions tab
    with tab3:
        st.markdown('<h2 class="sub-header">💳 My Transactions</h2>', unsafe_allow_html=True)

        # Show user's transactions
        user_transactions = [t for t in st.session_state.transactions if t["username"] == st.session_state.username]
        if user_transactions:
            transactions_df = pd.DataFrame(user_transactions)
            st.dataframe(transactions_df)

            # Calculate total spent
            total_spent = sum(t["amount"] for t in user_transactions)
            st.metric("Total Amount Spent", f"${total_spent:.2f}")
        else:
            st.info("No transactions found.")

        # Show fines if any
        if st.session_state.username in st.session_state.fines:
            st.markdown('<h3>My Fines</h3>', unsafe_allow_html=True)
            user_fines = st.session_state.fines[st.session_state.username]
            fines_df = pd.DataFrame(user_fines)
            st.dataframe(fines_df)

            # Calculate total fines
            total_fines = sum(f["amount"] for f in user_fines)
            st.metric("Total Fines", f"${total_fines:.2f}")

    # Admin Panel tab
    if st.session_state.is_admin:
        with tab4:
            st.markdown('<h2 class="sub-header">🛠️ Admin Panel</h2>', unsafe_allow_html=True)

            admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5, admin_tab6 = st.tabs([
                "Add Book", "Manage Books", "View All Borrowings", "Library Statistics", "Fine Management",
                "Return Requests"
            ])

            # Add Book tab
            with admin_tab1:
                st.markdown('<h3>Add New Book</h3>', unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    new_title = st.text_input("Title")
                    new_author = st.text_input("Author")
                    new_category = st.selectbox("Category", BOOK_CATEGORIES)
                    new_language = st.selectbox("Language", BOOK_LANGUAGES)

                with col2:
                    new_price = st.number_input("Price ($)", min_value=0.0, step=0.01)
                    new_quantity = st.number_input("Quantity", min_value=1, step=1)
                    new_description = st.text_area("Description")

                if st.button("Add Book", key="add_book_admin_panel"):
                    if new_title and new_author and new_price > 0 and new_quantity > 0:
                        new_book = {
                            "id": generate_book_id(),
                            "title": new_title,
                            "author": new_author,
                            "category": new_category,
                            "language": new_language,
                            "price": new_price,
                            "quantity": new_quantity,
                            "available": new_quantity,
                            "description": new_description,
                            "cover_url": ""
                        }

                        st.session_state.books.append(new_book)
                        save_books()

                        st.success(f"Book '{new_title}' added successfully!")
                    else:
                        st.error("Please fill all required fields!")

            # Manage Books tab
            with admin_tab2:
                st.markdown('<h3>Manage Books</h3>', unsafe_allow_html=True)

                if st.session_state.books:
                    for book in st.session_state.books:
                        with st.expander(f"{book['title']} by {book['author']}"):
                            col1, col2 = st.columns(2)

                            with col1:
                                edited_title = st.text_input("Title", book["title"], key=f"edit_title_{book['id']}")
                                edited_author = st.text_input("Author", book["author"], key=f"edit_author_{book['id']}")
                                try:
                                    category_index = BOOK_CATEGORIES.index(book["category"])
                                except ValueError:
                                    category_index = 0
                                edited_category = st.selectbox("Category", BOOK_CATEGORIES, index=category_index, key=f"edit_category_{book['id']}")
                                edited_language = st.selectbox("Language", BOOK_LANGUAGES,
                                                               index=BOOK_LANGUAGES.index(book["language"]),
                                                               key=f"edit_language_{book['id']}")

                            with col2:
                                edited_price = st.number_input("Price ($)", min_value=0.0, step=0.01,
                                                               value=book["price"], key=f"edit_price_{book['id']}")
                                edited_quantity = st.number_input("Quantity", min_value=0, step=1,
                                                                  value=book["quantity"],
                                                                  key=f"edit_quantity_{book['id']}")
                                edited_description = st.text_area("Description", book["description"],
                                                                  key=f"edit_description_{book['id']}")

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Update", key=f"update_{book['id']}"):
                                    book["title"] = edited_title
                                    book["author"] = edited_author
                                    book["category"] = edited_category
                                    book["language"] = edited_language
                                    book["price"] = edited_price
                                    book["quantity"] = edited_quantity
                                    book["description"] = edited_description
                                    book["available"] = min(book["available"], edited_quantity)

                                    save_books()
                                    st.success(f"Book '{edited_title}' updated successfully!")

                            with col2:
                                if st.button("Delete", key=f"delete_{book['id']}"):
                                    st.session_state.books.remove(book)
                                    save_books()
                                    st.success(f"Book '{book['title']}' deleted successfully!")
                                    st.rerun()
                else:
                    st.info("No books in the library.")

            # View All Borrowings tab
            with admin_tab3:
                st.markdown('<h3>All Borrowings</h3>', unsafe_allow_html=True)

                if st.session_state.borrowings:
                    # Create a DataFrame for better display
                    borrowings_data = []
                    for borrowing in st.session_state.borrowings:
                        user_name = st.session_state.users[borrowing["username"]]["name"]
                        borrowings_data.append({
                            "ID": borrowing["id"],
                            "Book": borrowing["book_title"],
                            "User": f"{borrowing['username']} ({user_name})",
                            "Borrow Date": borrowing["borrow_date"],
                            "Return Date": borrowing["return_date"] or "Not returned"
                        })

                    df = pd.DataFrame(borrowings_data)
                    st.dataframe(df)

                    # Download option
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download as CSV",
                        data=csv,
                        file_name="library_borrowings.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No borrowing records found.")

            # Library Statistics tab
            with admin_tab4:
                st.markdown('<h3>Library Statistics</h3>', unsafe_allow_html=True)

                col1, col2, col3 = st.columns(3)

                with col1:
                    total_books = len(st.session_state.books)
                    total_borrowings = len(st.session_state.borrowings)
                    st.metric("Total Books", total_books)
                    st.metric("Total Borrowings", total_borrowings)

                with col2:
                    active_borrowings = len([b for b in st.session_state.borrowings if b["return_date"] is None])
                    total_fines = sum(sum(f["amount"] for f in fines) for fines in st.session_state.fines.values())
                    st.metric("Active Borrowings", active_borrowings)
                    st.metric("Total Fines Collected", f"${total_fines:.2f}")

                with col3:
                    total_users = len(st.session_state.users)
                    total_transactions = len(st.session_state.transactions)
                    st.metric("Total Users", total_users)
                    st.metric("Total Transactions", total_transactions)

                # Popular books chart
                st.markdown("### Popular Books")
                book_counts = {}
                for borrowing in st.session_state.borrowings:
                    if borrowing["book_id"] not in book_counts:
                        book_counts[borrowing["book_id"]] = 0
                    book_counts[borrowing["book_id"]] += 1

                popular_books = sorted(book_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                popular_books_data = {
                    "Book": [next(b["title"] for b in st.session_state.books if b["id"] == book_id) for book_id, _ in
                             popular_books],
                    "Borrowings": [count for _, count in popular_books]
                }
                st.bar_chart(pd.DataFrame(popular_books_data).set_index("Book"))

            # Fine Management tab
            with admin_tab5:
                st.markdown('<h3>Fine Management</h3>', unsafe_allow_html=True)

                # Show all fines
                if st.session_state.fines:
                    all_fines = []
                    for username, fines in st.session_state.fines.items():
                        for fine in fines:
                            all_fines.append({
                                "User": username,
                                "Book": fine["book_title"],
                                "Amount": fine["amount"],
                                "Date": fine["date"]
                            })

                    fines_df = pd.DataFrame(all_fines)
                    st.dataframe(fines_df)

                    # Fine summary
                    col1, col2 = st.columns(2)
                    with col1:
                        total_fines = sum(f.get("amount", 0) for f in all_fines)
                        st.metric("Total Fines", f"${total_fines:.2f}")
                    with col2:
                        unpaid_fines = sum(f.get("amount", 0) for f in all_fines)
                        st.metric("Unpaid Fines", f"${unpaid_fines:.2f}")

                    # Fine payment
                    st.markdown("### Process Fine Payment")
                    selected_user = st.selectbox("Select User", list(st.session_state.fines.keys()))
                    if selected_user:
                        user_fines = st.session_state.fines[selected_user]
                        fine_df = pd.DataFrame(user_fines)
                        st.dataframe(fine_df)

                        if st.button("Mark as Paid"):
                            st.session_state.fines[selected_user] = []
                            save_fines()
                            st.success("Fines marked as paid successfully!")
                else:
                    st.info("No fines recorded yet.")

            # Return Requests tab
            with admin_tab6:
                st.markdown('<h3>Return Requests</h3>', unsafe_allow_html=True)

                pending_requests = [r for r in st.session_state.return_requests if r["status"] == "pending"]

                if pending_requests:
                    for request in pending_requests:
                        with st.expander(f"Return Request for {request['book_title']} by {request['username']}"):
                            st.markdown(f"*Request Date:* {request['request_date']}")
                            st.markdown(
                                f"*Borrowed on:* {next(b['borrow_date'] for b in st.session_state.borrowings if b['id'] == request['borrowing_id'])}")

                            # Book condition options
                            condition = st.radio("Book Condition", ["Good", "Damaged", "Lost"])

                            if condition != "Good":
                                fine_amount = st.number_input("Fine Amount ($)", min_value=0.0, step=0.01,
                                                              key=f"fine_{request['id']}")
                                notes = st.text_area("Notes", key=f"notes_{request['id']}")
                            else:
                                fine_amount = 0
                                notes = ""

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Approve Return", key=f"approve_{request['id']}"):
                                    # Update borrowing record
                                    borrowing = next(
                                        b for b in st.session_state.borrowings if b["id"] == request["borrowing_id"])
                                    borrowing["return_date"] = datetime.datetime.now().strftime("%Y-%m-%d")

                                    # Update book availability
                                    for book in st.session_state.books:
                                        if book["id"] == request["book_id"]:
                                            book["available"] += 1
                                            break

                                    # Add fine if applicable
                                    if fine_amount > 0:
                                        if request["username"] not in st.session_state.fines:
                                            st.session_state.fines[request["username"]] = []
                                        st.session_state.fines[request["username"]].append({
                                            "id": ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
                                            "borrowing_id": request["borrowing_id"],
                                            "book_title": request["book_title"],
                                            "amount": fine_amount,
                                            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                                            "reason": condition,
                                            "notes": notes
                                        })
                                        save_fines()

                                    # Update request status
                                    request["status"] = "approved"
                                    request["fine_amount"] = fine_amount
                                    request["notes"] = notes
                                    save_return_requests()

                                    # Save all changes
                                    save_books()
                                    save_borrowings()

                                    st.success("Return request approved successfully!")
                                    st.rerun()

                            with col2:
                                if st.button("Reject Return", key=f"reject_{request['id']}"):
                                    request["status"] = "rejected"
                                    save_return_requests()
                                    st.success("Return request rejected!")
                                    st.rerun()
                else:
                    st.info("No pending return requests.")

    # Dataset Management tab (only visible to admin)
    if st.session_state.is_admin:
        st.markdown("---")
        st.markdown('<h2 class="sub-header">Dataset Management</h2>', unsafe_allow_html=True)

        dataset_tab1, dataset_tab2, dataset_tab3, dataset_tab4 = st.tabs([
            "Categories", "Languages", "Authors", "Popular Books"
        ])

        # Categories Management
        with dataset_tab1:
            st.markdown('<h3>Manage Categories</h3>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)

            with col1:
                new_category = st.text_input("Add New Category")
                if st.button("Add Category"):
                    if new_category and new_category not in st.session_state.custom_categories:
                        st.session_state.custom_categories.append(new_category)
                        st.success(f"Category '{new_category}' added successfully!")

            with col2:
                category_to_remove = st.selectbox("Remove Category",
                                                  [c for c in st.session_state.custom_categories if
                                                   c not in ["Fiction", "Non-Fiction"]])
                if st.button("Remove Category"):
                    if category_to_remove:
                        st.session_state.custom_categories.remove(category_to_remove)
                        st.success(f"Category '{category_to_remove}' removed successfully!")

            st.markdown("### Current Categories")
            st.write(st.session_state.custom_categories)

        # Languages Management
        with dataset_tab2:
            st.markdown('<h3>Manage Languages</h3>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)

            with col1:
                new_language = st.text_input("Add New Language")
                if st.button("Add Language"):
                    if new_language and new_language not in st.session_state.custom_languages:
                        st.session_state.custom_languages.append(new_language)
                        st.success(f"Language '{new_language}' added successfully!")

            with col2:
                language_to_remove = st.selectbox("Remove Language",
                                                  [l for l in st.session_state.custom_languages if
                                                   l not in ["English"]])
                if st.button("Remove Language"):
                    if language_to_remove:
                        st.session_state.custom_languages.remove(language_to_remove)
                        st.success(f"Language '{language_to_remove}' removed successfully!")

            st.markdown("### Current Languages")
            st.write(st.session_state.custom_languages)

        # Authors Management
        with dataset_tab3:
            st.markdown('<h3>Manage Authors</h3>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)

            with col1:
                new_author = st.text_input("Add New Author")
                if st.button("Add Author"):
                    if new_author and new_author not in st.session_state.custom_authors:
                        st.session_state.custom_authors.append(new_author)
                        st.success(f"Author '{new_author}' added successfully!")

            with col2:
                author_to_remove = st.selectbox("Remove Author", st.session_state.custom_authors, key="remove_author_selectbox")
                if st.button("Remove Author"):
                    if author_to_remove:
                        st.session_state.custom_authors.remove(author_to_remove)
                        st.success(f"Author '{author_to_remove}' removed successfully!")

            st.markdown("### Current Authors")
            st.write(st.session_state.custom_authors)

        # Popular Books Management
        with dataset_tab4:
            st.markdown('<h3>Manage Popular Books</h3>', unsafe_allow_html=True)

            # Add new book
            st.markdown("#### Add New Book")
            col1, col2 = st.columns(2)
            with col1:
                new_book_title = st.text_input("Book Title")
                new_book_author = st.selectbox("Author", st.session_state.custom_authors, key="add_book_author_selectbox")
            with col2:
                new_book_category = st.selectbox("Category", st.session_state.custom_categories, key="add_book_category_selectbox")
                new_book_language = st.selectbox("Language", st.session_state.custom_languages, key="add_book_language_selectbox")

            if st.button("Add Book", key="add_book_popular_books"):
                if new_book_title and new_book_author and new_book_category and new_book_language:
                    new_book = {
                        "title": new_book_title,
                        "author": new_book_author,
                        "category": new_book_category,
                        "language": new_book_language,
                        "cover_url": ""
                    }
                    if new_book not in st.session_state.custom_books:
                        st.session_state.custom_books.append(new_book)
                        st.success(f"Book '{new_book_title}' added successfully!")

            # Remove book
            st.markdown("#### Remove Book")
            book_to_remove = st.selectbox("Select Book to Remove",
                                          [f"{book['title']} by {book['author']}" for book in
                                           st.session_state.custom_books])
            if st.button("Remove Book"):
                if book_to_remove:
                    title = book_to_remove.split(" by ")[0]
                    st.session_state.custom_books = [b for b in st.session_state.custom_books if b['title'] != title]
                    st.success(f"Book '{title}' removed successfully!")

            st.markdown("### Current Popular Books")
            books_df = pd.DataFrame(st.session_state.custom_books)
            st.dataframe(books_df)

# Footer
st.markdown("---")
st.caption("Library Management System © 2023")
