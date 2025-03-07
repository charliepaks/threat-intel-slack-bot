# Threat Intel Slack Bot

## 📌 Overview

The **Threat Intel Slack Bot** is an automated cybersecurity news fetcher, summarizer, and Slack notifier. It scrapes articles from **The Hacker News**, extracts key details, and sends them to a designated Slack channel. Additionally, the bot analyzes **Indicators of Compromise (IOCs)** and provides actionable security recommendations.

## 🚀 Features

- 🔍 **Fetches latest cybersecurity news** from The Hacker News.
- 📜 **Extracts full articles** for better analysis.
- ✍️ **Summarizes content** using OpenAI's GPT-4 model.
- 🛡 **Extracts IOCs (Indicators of Compromise)** from articles.
- 📝 **Generates security recommendations** based on content.
- 🔔 **Sends enhanced reports to Slack** with structured formatting.

## 📦 Installation

### **1️⃣ Clone the Repository**

```bash
git clone https://github.com/charliepaks/threat-intel-slack-bot.git
cd threat-intel-slack-bot
```

### **2️⃣ Set Up a Virtual Environment**

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### **3️⃣ Install Dependencies**

Using `pip` with `pyproject.toml`:

```bash
pip install .
```

## ⚙️ Configuration

This bot requires **Slack API credentials** and an **OpenAI API key**. Create a `.env` file in the project root and add the following:

```ini
OPENAI_API_KEY=your_openai_api_key
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_CHANNEL=#threat-intel
```

## 🏃 Usage

To run the bot manually:

```bash
threat_intel_bot
```

This will:

1. Fetch today's articles from The Hacker News.
2. Summarize content using GPT-4.
3. Extract IOCs and security recommendations.
4. Send messages to the Slack channel.

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository.
2. Create a new branch.
3. Submit a pull request with detailed changes.

## 📜 License

This project is licensed under the **MIT License**. See `LICENSE` for details.

## 📧 Contact

For questions or issues, contact: <charlesukpaka@ymail.com>.
