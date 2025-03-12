import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import CharacterTextSplitter
from time import sleep

# Get the absolute path to the .env file
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")

load_dotenv(dotenv_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#threat-intel")

slack_client = WebClient(token=SLACK_BOT_TOKEN)
llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4", temperature=0.5)


def fetch_today_hacker_news():
    """Fetches today's full articles from The Hacker News."""
    url = "https://thehackernews.com/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    today_str = datetime.utcnow().strftime("%b %d, %Y")  
    articles = soup.select("div.body-post")
    news_entries = []

    for article in articles:
        date_tag = article.select_one(".item-label")
        if not date_tag:
            continue

        raw_date = date_tag.text.strip()
        cleaned_date_match = re.search(r"[A-Za-z]{3} \d{1,2}, \d{4}", raw_date)

        if not cleaned_date_match:
            continue

        article_date = cleaned_date_match.group(0).strip()

        print(f"🛠 Strictly Extracted Date: {article_date}")  

        if article_date != today_str:
            print(f"❌ Skipping {article_date} (Not Today)")
            continue

        title = article.select_one(".home-title").text.strip()
        link = article.select_one("a.story-link")["href"]

        print(f"🔗 Fetching full article: {link}")  

        
        full_article = fetch_full_article(link)

        print(f"📜 Extracted Content (First 200 chars): {full_article[:200]}")  

        news_entries.append({
            "title": title,
            "date": article_date,
            "full_content": full_article,
            "link": link
        })

    return news_entries



def fetch_full_article(article_url):
    """Fetches full blog content from a given article URL."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(article_url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch article: {article_url}")
        return "⚠️ Error: Could not retrieve full article content."

    soup = BeautifulSoup(response.text, "html.parser")

    
    article_body = soup.select("div.articlebody")  

    if not article_body:
        print(f"❌ Could not extract article content from {article_url}")
        return "⚠️ Full article content not available."

    paragraphs = article_body[0].find_all("p")  
    full_text = "\n".join([para.text.strip() for para in paragraphs])

    if not full_text:
        print(f"❌ Extracted content is empty for {article_url}")
        return "⚠️ No article text found."

    return full_text[:3500]  



def process_and_send_news():
    """Main function to process news and send to Slack."""
    
    articles = fetch_today_hacker_news()
    
    if not articles:
        print("No articles found for today")
        return
    
    for article in articles:
        
        print(f"Summarizing article: {article['title']}")
        article['summary'] = summarize_article(article)
        
        
        print(f"Extracting IOCs from article: {article['title']}")
        article['iocs_recommendations'] = extract_iocs_and_recommendations(article)
        
        
        enhanced_article = {
            'title': article['title'],
            'date': article['date'],
            'link': article['link'],
            'summary': article['summary'],
            'iocs_recommendations': article['iocs_recommendations']
        }
        
        
        print(f"Sending to Slack: {article['title']}")
        send_enhanced_slack_message(enhanced_article)
        sleep(1)  



def summarize_article(article):
    """Summarizes the full blog content using GPT-4 chat model."""
    prompt = f"""
    Summarize the following cybersecurity news article in not more than 300 characters. Focus on the key points that cybersecurity teams need to pay attention to only.

    Title: {article['title']}
    Full Content: {article['full_content']}
    Link: {article['link']}

    **FORMAT:**
    Thought: I now can give a great answer
    Final Answer: [Your summarized version of the article]
    """

    response = llm.invoke([{"role": "system", "content": "You are a helpful AI assistant that summarizes cybersecurity news."},
                           {"role": "user", "content": prompt}])

    
    summary_text = response.content.strip()

    
    if "Final Answer:" in summary_text:
        return summary_text.split("Final Answer:")[-1].strip()
    else:
        return summary_text  



def extract_iocs_and_recommendations(article):
    """Extracts IOCs and security recommendations from the article."""
    prompt = f"""
    Extract Indicators of Compromise (IOCs) and security recommendations from the following article. For the IOCS, return only IP addresses, hashes and urls/domains specified in the content. 
    If none were found, return "No actionable IOCs found". 
    For the recommendations, return not more than four
    items at not more than 100 characters each. Ensure the recommendations are actionable items that cybersecurity teams can implement to prevent whatever attack is specified in the content. If you think the recommendations do not apply to enterprise cybersecurity teams, then return "No actionable recommendations for enterprise cybersecurity teams"
    Give very specific recommendations and not generic ones.
    Title: {article['title']}
    Full Content: {article['full_content']}
    Link: {article['link']}

    **FORMAT:**
    Thought: I now can give a great answer
    Final Answer: 
    *IOCs:*
    - <list of IOCs>
    
    *Recommendations:*
    - <list of best practices>
    """

    response = llm.invoke([
        {"role": "system", "content": "You are a cybersecurity expert extracting IOCs and recommendations."},
        {"role": "user", "content": prompt}
    ])

    
    ioc_text = response.content.strip()

    
    if "Final Answer:" in ioc_text:
        return ioc_text.split("Final Answer:")[-1].strip()
    else:
        return ioc_text  



def send_enhanced_slack_message(article):
    """Sends a comprehensive version of the article to Slack including IOCs and recommendations."""
    message = (
        f"*{article['title']}*\n"
        f"📅 {article['date']}\n"
        f"🔗 <{article['link']}|Link>\n\n"
        f"*Summary:*\n{article['summary']}\n\n"
        f"{article['iocs_recommendations']}\n\n\n\n\n"
    )

    try:
        response = slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        print(f"✅ Successfully sent: {article['title']}")
    except SlackApiError as e:
        print(f"❌ Slack API Error: {e.response['error']}")
        if "ratelimited" in e.response['error']:
            print("⏳ Slack rate limit reached. Retrying in 60 seconds...")
            sleep(60)
            send_enhanced_slack_message(article)



def send_slack_message(article):
    """Sends a summarized version of the article to Slack."""
    message = (
        f"*{article['title']}*\n"
        f"📅 {article['date']}\n"
        f"🔗 <{article['link']}>\n\n"
        f"*Summary:*\n{article['summary']}"
    )

    try:
        response = slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
        print(f"✅ Successfully sent: {article['title']}")
    except SlackApiError as e:
        print(f"❌ Slack API Error: {e.response['error']}")
        if "ratelimited" in e.response['error']:
            print("⏳ Slack rate limit reached. Retrying in 60 seconds...")
            sleep(60)
            send_slack_message(article)


def main():
    """Entry point for the script."""
    process_and_send_news()  
if __name__ == "__main__":
    main()