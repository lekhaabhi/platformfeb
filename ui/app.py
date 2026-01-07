# SWITCH TO JAVASCRIPT

from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

HTML = """
<h2>CODA Data Discovery UI</h2>

<form method="post">
  <input name="query" placeholder="Enter natural language query" size="60">
  <button type="submit">Submit</button>
</form>

{% if response %}
<h3>API Response</h3>
<pre>{{ response }}</pre>
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def home():
    response = None
    if request.method == "POST":
        query = request.form["query"]
        r = requests.post(
            "http://api-gateway:8000/query",
            json={"query": query}
        )
        response = r.json()
    return render_template_string(HTML, response=response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)