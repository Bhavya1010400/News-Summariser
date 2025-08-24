from flask import Flask, render_template, request, redirect, url_for, session
from groq import Groq
import os
import json
import re
from dotenv import load_dotenv
# Load environment variables
dotenv.load_dotenv()
groq_api = os.getenv("groq_api")
client = Groq(api_key=groq_api)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session


# Function to analyze news
def analyze_news(news_link, news_description):
    PROMPT_TEMPLATE = f"""
    News Link: {news_link}
    News Description: {news_description}

    You are an expert educator helping kids understand news. Summarize the news in simple language, then list the pros and cons of the news. Format your response like this:

    Summary:
    ...

    Pros:
    - ...
    - ...

    Cons:
    - ...
    - ...

    Only reply in this format, nothing else.
    """
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "user",
                "content": PROMPT_TEMPLATE
            }
        ],
        temperature=0.3,
        max_tokens=800,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    expected_response = response.choices[0].message.content
    print("Groq response:", expected_response)
    if not expected_response or expected_response.strip() == "":
        return None, "No response from Groq API. Please check your API key, prompt, or try again."

    # Parse plain text response
    summary = ""
    pros = []
    cons = []
    try:
        summary_match = re.search(r"Summary:\s*(.*?)(?:Pros:|$)", expected_response, re.DOTALL)
        pros_match = re.search(r"Pros:\s*(.*?)(?:Cons:|$)", expected_response, re.DOTALL)
        cons_match = re.search(r"Cons:\s*(.*)", expected_response, re.DOTALL)

        if summary_match:
            summary = summary_match.group(1).strip()
        if pros_match:
            pros = [line.strip('- ').strip() for line in pros_match.group(1).strip().split('\n') if line.strip()]
        if cons_match:
            cons = [line.strip('- ').strip() for line in cons_match.group(1).strip().split('\n') if line.strip()]

        result = {
            "summary": summary,
            "pros": pros,
            "cons": cons
        }
        return result, None
    except Exception as e:
        return None, f"Error parsing response: {e}. Raw response: {expected_response}"


# Route for home page
@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    if request.method == 'POST':
        news_link = request.form.get('news_link', '').strip()
        news_description = request.form.get('news_description', '').strip()
        if news_link or news_description:
            result, error = analyze_news(news_link, news_description)
            session['result'] = result
            session['error'] = None if result else error
            return redirect(url_for('index'))
        else:
            error = "Please provide at least a news link or a news description."
            session['result'] = None
            session['error'] = error
            return redirect(url_for('index'))
    else:
        result = session.pop('result', None)
        error = session.pop('error', None)
    return render_template('index.html', result=result, error=error)


# Start the app
if __name__ == '__main__':
    app.run(debug=False)
