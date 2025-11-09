# Project Title
This is my submission for the CAIE PROJECT. I have created a Text-to-SQL and Sentiment Analysis dashboard in plotly-dash

# Installation
```bash
pip3 install -r requirements.txt
```
# Workflow Overview

`Youtube_Selenium_Scrape.ipynb`
> Web scrape all the videos from Youtube_Channels that on the Associated of Banks Malaysia(ABM). The scraping is done using UI Automation with Selenium, No API used. The scraping was done over several nights.

`RDBMS.ipynb` optional
> After scraping the videos, I consilidate the data into a database. This process is optional as it will be done again in `Agent and NLP.ipynb`

`Agent and NLP.ipynb`
> googletrans and RoBERTa model is used to translate natural languages that are not supported into English, then the sentiment of the comments in COMMENT_table is deduced.

`app.py` and `.\pages`
> Multipage plotly-dash data app to visulise data. <br>

> `page1.py` : Assists in querying the database with natural language. Ouputs natural language and the SQL used to derive the information. <br>
> `page2.py` : Views and Likes data viz for custom input timeframes. <br>
> `page3.py` : Showcases the sentiments of comments for each banking Youtube Channel/Handle. Samples 5 positive, neutral, and negative comments. <br>
