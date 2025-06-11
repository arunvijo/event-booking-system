# 🎟️ EventEase - Django Event Booking System

EventEase is a feature-rich event booking platform built using Django. It offers a seamless booking experience for both authenticated users and guests. Guests can scan or upload QR codes to book events directly, while registered users can browse, filter, and book events from a user-friendly UI.

## 🌟 Features

- 🔐 User Authentication (Login/Register)
- 📦 Event Listing with Filters and Search
- 🎫 Event Booking (via Button or QR code)
- 🖼️ Upload or Scan QR Code to Book Instantly
- 🌙 Light/Dark Theme Toggle
- ✅ Toast Notifications for Feedback
- 🔄 Spinner Loaders on Form Submissions
- 📧 Booking confirmation email with QR code
- 🎨 Fully responsive modern UI with enhanced UX

## 🛠️ Technologies Used

- Django & Django REST Framework
- HTML, CSS, Bootstrap
- JavaScript
- Pillow (Image Processing)
- OpenCV (QR Decoding)
- SQLite (default) or PostgreSQL

## 📷 Screenshots

![Events Page](screenshots/events-page.png)
![QR Upload](screenshots/qr-upload.png)

## 🚀 Getting Started

### Prerequisites

```bash
pip install -r requirements.txt
Run the Server
bash
Copy
Edit
python manage.py migrate
python manage.py runserver
Access App
Visit: http://127.0.0.1:8000/login

📂 Folder Structure
csharp
Copy
Edit
event-booking-system/
│
├── core/               # Main Django app
├── templates/          # HTML Templates
├── static/             # CSS & JS Files
├── media/              # Uploaded QR Codes
├── manage.py
└── requirements.txt
🤝 Contributing
Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

yaml
Copy
Edit

---

## 📄 `CONTRIBUTING.md`

```markdown
# Contributing to EventEase

Thank you for your interest in contributing to **EventEase**! 🙌

Here’s how you can help:

## 🧩 How to Contribute

1. Fork the repository
2. Create your feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature-name`)
5. Open a pull request

## 🛠 Code Style

- Follow PEP8 for Python code.
- Use semantic HTML and clean, accessible CSS.
- Keep commits small and meaningful.

## 💡 Suggestions

Feel free to open issues if:
- You find a bug 🐞
- Want to request a new feature 🌟
- Have questions or need support ❓

Let’s build something awesome together! 💪
