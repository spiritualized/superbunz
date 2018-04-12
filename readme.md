# Super Bunz

This project provides a simplified view of the "Bunz" Facebook group, the most popular listing location for rental accommodation in Toronto.

At time of writing, Facebook is still performing damage control related to the Cambridge Analytica scandal. Most API functionality is disabled, and new developer account requests are not being reviewed. Thus it was necessary to scrape the site directly.

The codebase could possibly be reused for visualising other Facebook group/page data.


# Installation

  - Clone the git repo
  - Create a virtual environment, use pip to install dependencies from requirements.txt
  - Create a MySQL database
  - Copy config.py-dist to config.py, fill in MySQL/Facebook login credentials  and other variables

# Usage
  - Run scraper.py persistently. It will periodically scrape the target Facebook group, parse the results, and submit to the database.
  - server.py runs a Flask instance. Browse to http://localhost:5000 to test.
 
# Further info
Demo site at https://bunz.spiritualized.io
Source at https://github.com/spiritualized/superbunz