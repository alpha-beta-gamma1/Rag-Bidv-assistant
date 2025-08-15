# BIDV Chatbot Project

## Overview
The BIDV Chatbot is a conversational AI application designed to assist customers of the Bank for Investment and Development of Vietnam (BIDV) with banking-related queries. The chatbot provides information on services such as account balance inquiries, transaction history, loan applications, and general customer support, aiming to enhance user experience and streamline customer interactions.

## Features
- **Account Inquiries**: Retrieve account balance and transaction history.
- **Loan Assistance**: Provide information on loan products and application processes.
- **Customer Support**: Answer FAQs and guide users to relevant BIDV services.
- **24/7 Availability**: Respond to user queries at any time with quick and accurate responses.
- **Multi-language Support**: Support for Vietnamese and English (customizable for other languages).

## Prerequisites
Before setting up the project, ensure you have the following installed:
- Python 3.8+ (or your preferred programming language)
- Node.js (if using a JavaScript-based framework)
- A virtual environment tool (e.g., `venv` for Python)
- Any required API keys (e.g., for NLP services like Dialogflow or Rasa)
- BIDV API access (if integrated with bank systems; contact BIDV IT for details)

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/alpha-beta-gamma1/Rag-Bidv-assistant.git
   cd bidv-chatbot
   ```

2. **Set Up a Virtual Environment** (for Python-based projects):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the project root and add necessary configurations, such as:
   ```plaintext
   GEMINI_API_KEY=your_api_key
   GEMINI_BASE_URL=your_nlp_service_key
   ```

5. **Run the Application**:
   ```bash
   python test.py
   ```

## Usage
- **Local Testing**: Run the chatbot locally and interact via a command-line interface or a web-based UI (e.g., `http://localhost:5000`).
- **Integration**: Connect the chatbot to BIDV’s customer-facing platforms (e.g., website, mobile app) using provided APIs.
- **Example Commands**:
  - "Check my account balance"
  - "How do I apply for a loan?"
  - "What are BIDV’s branch hours?"

## Project Structure
```
bidv-chatbot/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── package.json        # Node.js dependencies (if applicable)
├── config/             # Configuration files (e.g., .env)
├── models/             # NLP model or intents (e.g., for Rasa or Dialogflow)
├── static/             # Static files (e.g., CSS, JS for web UI)
├── templates/          # HTML templates (if using a web framework)
└── README.md           # This file
```

## Contributing
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For inquiries or support, contact the project maintainer at:
- Email: your-email@example.com
- BIDV Support: support@bidv.com.vn